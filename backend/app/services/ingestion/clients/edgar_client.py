"""
edgar_client.py — HTTP client for SEC EDGAR data endpoints.

MVP Responsibilities:
- Direct HTTP communication with SEC JSON endpoints (no caching)
- Fetch Company Facts, Submissions, and Ticker mappings
- Polite rate limiting and retry behavior
- Stateless - safe for concurrent use
"""

from __future__ import annotations

import csv
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import requests
from tenacity import before_sleep_log, retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.logging import get_logger


logger = get_logger(__name__)


SEC_BASE_HEADERS = {
    "Accept": "application/json",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}

COMPANY_TICKER_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL_TEMPLATE = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
COMPANY_FACTS_URL_TEMPLATE = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"


class EdgarClientError(RuntimeError):
    """Base exception for EDGAR client failures."""


class EdgarClientConfigurationError(EdgarClientError):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True)
class EdgarClientSettings:
    """
    MVP EdgarClient settings - no caching, direct fetch only.
    """
    user_agent: str
    sleep_seconds: float
    timeout_seconds: int
    max_retries: int
    backoff_base: float

    @classmethod
    def from_app_settings(cls) -> "EdgarClientSettings":
        return cls(
            user_agent=settings.EDGAR_USER_AGENT,
            sleep_seconds=settings.EDGAR_REQUEST_SLEEP_SECONDS,
            timeout_seconds=settings.EDGAR_REQUEST_TIMEOUT_SECONDS,
            max_retries=settings.EDGAR_MAX_RETRIES,
            backoff_base=settings.EDGAR_BACKOFF_BASE,
        )


class EdgarClient:
    """
    Thin wrapper over `requests.Session` with polite EDGAR defaults.

    The client is sync/blocking because the SEC endpoints are rate limited and
    accessed primarily from background ingestion tasks.
    """

    def __init__(self, session: Optional[requests.Session] = None, config: Optional[EdgarClientSettings] = None):
        self._session = session or requests.Session()
        self._config = config or EdgarClientSettings.from_app_settings()
        self._session.headers.update({**SEC_BASE_HEADERS, "User-Agent": self._config.user_agent})

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def fetch_company_list(self, index: str = "sp500") -> List[Dict[str, Any]]:
        """
        Return a list of constituents for the requested index.

        Currently supports S&P 500 via CSV/JSON specified by `SP500_TICKER_SOURCE`.
        The file must contain at minimum a `ticker` column; `name` is optional.

        Raises:
            EdgarClientConfigurationError if the source cannot be located or parsed.
        """
        source = settings.SP500_TICKER_SOURCE.strip()
        if not source:
            raise EdgarClientConfigurationError(
                "SP500_TICKER_SOURCE must be configured (path or URL to ticker list)."
            )

        if source.lower().startswith("http"):
            response = self._request_json_or_csv(source)
        else:
            path = Path(source).expanduser()
            if not path.exists():
                raise EdgarClientConfigurationError(f"S&P 500 source file not found at {path}")
            response = self._load_local(path)

        records = self._normalize_index_payload(response)
        if not records:
            raise EdgarClientConfigurationError(f"No tickers parsed from source '{source}'")

        if index.lower() != "sp500":
            logger.warning("Index '%s' requested but only SP500 is currently supported.", index)
        return records

    def get_cik_map(self) -> Dict[str, int]:
        """
        Retrieve the SEC-wide ticker → CIK mapping.

        Returns:
            Dict mapping upper-case ticker -> integer CIK.
        """
        data = self._request_json(COMPANY_TICKER_URL)
        return {row["ticker"].upper(): int(row["cik_str"]) for row in data.values()}

    def get_submissions(self, cik: int) -> Dict[str, Any]:
        """Fetch a company's submissions feed."""
        return self._request_json(SUBMISSIONS_URL_TEMPLATE.format(cik=cik))

    def get_company_facts(self, cik: int) -> Dict[str, Any]:
        """Fetch the Company Facts XBRL dataset for a company."""
        return self._request_json(COMPANY_FACTS_URL_TEMPLATE.format(cik=cik))

    # ------------------------------------------------------------------ #
    # Request helpers
    # ------------------------------------------------------------------ #

    def _request_json_or_csv(self, url: str) -> Any:
        if url.lower().endswith(".json"):
            return self._request_json(url)
        response = self._request(url)
        return self._parse_csv(response.text.splitlines())

    def _load_local(self, path: Path) -> Any:
        if path.suffix.lower() == ".json":
            with path.open("r", encoding="utf-8") as fh:
                return json.load(fh)
        with path.open("r", encoding="utf-8") as fh:
            return self._parse_csv(fh)

    def _parse_csv(self, rows: Iterable[str]) -> List[Dict[str, Any]]:
        reader = csv.DictReader(rows)
        return [row for row in reader]

    def _request_json(self, url: str) -> Any:
        """Fetch JSON from URL - MVP: no caching, direct fetch only."""
        response = self._request(url)
        return response.json()

    def _request(self, url: str) -> requests.Response:
        response = self._perform_request(url)
        response.raise_for_status()
        self._polite_sleep()
        return response

    def _polite_sleep(self) -> None:
        delay = max(self._config.sleep_seconds, 0.0)
        if delay:
            time.sleep(delay)

    @retry(
        stop=stop_after_attempt(settings.EDGAR_MAX_RETRIES),
        wait=wait_exponential(multiplier=settings.EDGAR_BACKOFF_BASE, min=0.1, max=5),
        retry=retry_if_exception_type((requests.RequestException,)),
        before_sleep=before_sleep_log(logger, "warning"),
        reraise=True,
    )
    def _perform_request(self, url: str) -> requests.Response:
        logger.debug("Requesting %s", url)
        response = self._session.get(url, timeout=self._config.timeout_seconds)
        if response.status_code in {403, 429, 500, 502, 503, 504}:
            # Trigger retry
            msg = f"EDGAR request throttled or server error (status {response.status_code})"
            logger.warning("%s — retrying", msg)
            raise requests.HTTPError(msg, response=response)
        return response

    # ------------------------------------------------------------------ #
    # Payload normalization helpers
    # ------------------------------------------------------------------ #
    def _normalize_index_payload(self, payload: Any) -> List[Dict[str, Any]]:
        """
        Normalize raw CSV/JSON payload into:
            [{\"ticker\": str, \"name\": Optional[str]}]
        """
        records: List[Dict[str, Any]] = []

        if isinstance(payload, dict):
            # Treat as mapping of {ticker: {...}}
            for value in payload.values():
                ticker = (value.get("ticker") or value.get("symbol") or "").strip().upper()
                if ticker:
                    records.append({"ticker": ticker, "name": value.get("name")})
            return records

        if isinstance(payload, list):
            for row in payload:
                ticker = (row.get("ticker") or row.get("symbol") or row.get("Ticker") or "").strip().upper()
                if ticker:
                    records.append({"ticker": ticker, "name": row.get("name") or row.get("Security")})
            return records

        logger.error("Unsupported S&P 500 payload type: %s", type(payload))
        return records


