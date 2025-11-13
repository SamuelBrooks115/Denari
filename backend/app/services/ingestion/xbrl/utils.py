"""
Shared helpers for working with EDGAR Company Facts payloads.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional


ANNUAL_DAYS_MIN = 330


def parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.split("T")[0])
    except ValueError:
        return None


def annual_duration_ok(start: Optional[str], end: Optional[str]) -> bool:
    ds, de = parse_date(start), parse_date(end)
    if not ds or not de:
        return False
    return (de - ds).days >= ANNUAL_DAYS_MIN


def prefer_unsegmented(records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    def is_unsegmented(record: Dict[str, Any]) -> bool:
        segment = record.get("segment") or record.get("segments")
        return not segment

    records = list(records)
    unsegmented = [r for r in records if is_unsegmented(r)]
    return unsegmented if unsegmented else records


def prefer_usd(records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    records = list(records)
    usd = [r for r in records if (r.get("_unit") or r.get("unit")) == "USD"]
    return usd if usd else records


def flatten_units(units_obj: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    flattened: List[Dict[str, Any]] = []
    for unit_name, entries in units_obj.items():
        for entry in entries:
            val = entry.get("val")
            if isinstance(val, (int, float)):
                record = dict(entry)
                record["_unit"] = unit_name
                flattened.append(record)
    return flattened


def pick_for_report_date(
    records: List[Dict[str, Any]],
    report_date: str,
    duration: bool,
) -> Optional[Dict[str, Any]]:
    if not records:
        return None

    pool = prefer_unsegmented(records)
    pool = prefer_usd(pool)
    pool = [r for r in pool if r.get("end") == report_date]

    if duration:
        pool = [r for r in pool if annual_duration_ok(r.get("start"), r.get("end"))]

    if not pool:
        return None

    preferred = [r for r in pool if r.get("form") in {"10-K", "10-K/A"}]
    bucket = preferred if preferred else pool
    bucket.sort(key=lambda r: (r.get("filed", ""), r.get("end", "")), reverse=True)
    return bucket[0]


def infer_canonical_from_label(label: str) -> Optional[str]:
    if not label:
        return None
    text = label.lower()

    def contains(*keywords: str) -> bool:
        return all(keyword in text for keyword in keywords)

    if any(keyword in text for keyword in ("revenue", "sales")):
        return "Revenue"
    if "cost of revenue" in text or "cost of goods" in text:
        return "COGS"
    if "gross profit" in text:
        return "GrossProfit"
    if contains("research", "development"):
        return "R&D"
    if ("selling" in text and "administrative" in text) or "sga" in text:
        return "SG&A"
    if "operating income" in text or "operating profit" in text:
        return "OperatingIncome"
    if "income tax" in text or "tax expense" in text:
        return "TaxExpense"
    if "net income" in text or "profit loss" in text:
        return "NetIncome"
    if "net cash" in text and "operating activities" in text:
        return "CFO"
    if "property" in text and any(k in text for k in ("capital expenditures", "acquire", "purchases")):
        return "CapEx"
    if "accounts receivable" in text:
        return "AR"
    if "accounts payable" in text:
        return "AP"
    if "inventory" in text:
        return "Inventory"
    if "equity" in text and "total" in text:
        return "Equity"
    return None





