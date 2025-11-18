"""
structured_output.py — Structured 3-statement extraction from EDGAR Company Facts.

Provides functions to extract Balance Sheet, Income Statement, and Cash Flow Statement
data from EDGAR XBRL Company Facts API and return structured JSON matching the
single-year and multi-year filing templates.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from openai import OpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.logging import get_logger
from app.core.model_role_map import (
    BS_ACCOUNTS_PAYABLE,
    BS_ACCOUNTS_RECEIVABLE,
    BS_ACCRUED_LIABILITIES,
    BS_DEBT_CURRENT,
    BS_INVENTORY,
    BS_PP_AND_E,
    CF_DIVIDENDS_PAID,
    CF_SHARE_REPURCHASES,
    IS_COGS,
    IS_OPERATING_EXPENSE,
    IS_REVENUE,
    IS_TAX_EXPENSE,
    get_model_role_flags,
)
from app.services.ingestion.clients import EdgarClient
from app.services.ingestion.xbrl.utils import flatten_units, parse_date

logger = get_logger(__name__)

# Annual duration threshold (days)
ANNUAL_DAYS_MIN = 330

# Treat these forms as annual-type
PREFER_FORMS_ANNUAL = {"10-K", "10-K/A", "20-F"}

# ------------------------------------------------------------
# Balance sheet detection logic
# ------------------------------------------------------------

BS_ALLOWLIST = {
    # Totals
    "Assets",
    "AssetsCurrent",
    "AssetsNoncurrent",
    "Liabilities",
    "LiabilitiesCurrent",
    "LiabilitiesNoncurrent",
    "StockholdersEquity",
    "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    "Equity",
    "RetainedEarningsAccumulatedDeficit",
    "RetainedEarningsAccumulated",
    "AccumulatedOtherComprehensiveIncomeLossNetOfTax",
    # Assets – key accounts
    "CashAndCashEquivalentsAtCarryingValue",
    "CashCashEquivalentsAndShortTermInvestments",
    "ShortTermInvestments",
    "MarketableSecuritiesCurrent",
    "AccountsReceivableNetCurrent",
    "ReceivablesNetCurrent",
    "Inventories",
    "InventoryNet",
    "PrepaidExpensesAndOtherCurrentAssets",
    "OtherAssetsCurrent",
    "PropertyPlantAndEquipmentNet",
    "Goodwill",
    "IntangibleAssetsNetExcludingGoodwill",
    "FiniteLivedIntangibleAssetsNet",
    "OtherAssetsNoncurrent",
    # Liabilities – key accounts
    "AccountsPayableCurrent",
    "AccruedLiabilitiesCurrent",
    "OtherLiabilitiesCurrent",
    "ShortTermBorrowings",
    "CommercialPaper",
    "LongTermDebtCurrent",
    "LongTermDebtNoncurrent",
    "LongTermDebtAndCapitalLeaseObligationsCurrent",
    "LongTermDebtAndCapitalLeaseObligationsNoncurrent",
    "DeferredTaxLiabilitiesNoncurrent",
    "OtherLiabilitiesNoncurrent",
    # Equity components
    "CommonStockValue",
    "AdditionalPaidInCapital",
    "TreasuryStockValue",
}

BS_KEYWORDS = [
    "asset",
    "liabilit",
    "equity",
    "shareholder",
    "stockholder",
    "capital",
    "debt",
    "receivable",
    "payable",
    "inventory",
    "property, plant and equipment",
    "propertyplantandequipment",
    "ppe",
    "goodwill",
    "intangible",
    "deferred tax",
    "retained earnings",
    "accumulated other comprehensive",
]

# ------------------------------------------------------------
# Income statement detection logic
# ------------------------------------------------------------

IS_ALLOWLIST = {
    # Topline
    "Revenues",
    "Revenue",
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "SalesRevenueNet",
    # Cost / gross
    "CostOfRevenue",
    "CostOfGoodsAndServicesSold",
    "CostOfSales",
    "GrossProfit",
    # Operating expenses
    "ResearchAndDevelopmentExpense",
    "SellingGeneralAndAdministrativeExpense",
    "SellingAndMarketingExpense",
    "GeneralAndAdministrativeExpense",
    # Operating / pre-tax income
    "OperatingIncomeLoss",
    "OperatingProfitLoss",
    "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
    "EarningsBeforeInterestAndTaxes",
    # Taxes & net income
    "IncomeTaxExpenseBenefit",
    "IncomeTaxExpense",
    "NetIncomeLoss",
    "ProfitLoss",
}

IS_KEYWORDS = [
    "revenue",
    "sales",
    "net sales",
    "gross profit",
    "cost of goods",
    "cost of revenue",
    "operating income",
    "operating profit",
    "income before tax",
    "income tax",
    "net income",
    "profit loss",
    "earnings",
]

# ------------------------------------------------------------
# Cash flow detection logic
# ------------------------------------------------------------

CF_ALLOWLIST = {
    # Core totals
    "NetCashProvidedByUsedInOperatingActivities",
    "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
    "NetCashProvidedByUsedInInvestingActivities",
    "NetCashProvidedByUsedInFinancingActivities",
    "CashAndCashEquivalentsPeriodIncreaseDecrease",
    "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecrease",
    # Operating components
    "DepreciationDepletionAndAmortization",
    "DepreciationAndAmortization",
    "ShareBasedCompensation",
    "DeferredIncomeTaxExpenseBenefit",
    "IncreaseDecreaseInAccountsReceivable",
    "IncreaseDecreaseInInventories",
    "IncreaseDecreaseInAccountsPayable",
    "IncreaseDecreaseInAccruedLiabilities",
    "IncreaseDecreaseInOtherOperatingAssets",
    "IncreaseDecreaseInOtherOperatingLiabilities",
    "AmortizationOfIntangibleAssets",
    "ImpairmentOfIntangibleAssets",
    "ImpairmentOfLongLivedAssetsHeldAndUsed",
    # Investing components
    "PaymentsToAcquirePropertyPlantAndEquipment",
    "PaymentsToAcquirePropertyAndEquipment",
    "PurchasesOfPropertyAndEquipment",
    "CapitalExpenditures",
    "ProceedsFromSaleOfPropertyPlantAndEquipment",
    "PaymentsToAcquireBusinessesNetOfCashAcquired",
    "PaymentsToAcquireInvestments",
    "ProceedsFromSaleOfInvestments",
    # Financing components
    "ProceedsFromIssuanceOfLongTermDebt",
    "RepaymentsOfLongTermDebt",
    "ProceedsFromIssuanceOfShortTermDebt",
    "RepaymentsOfShortTermDebt",
    "ProceedsFromIssuanceOfCommonStock",
    "PaymentsForRepurchaseOfCommonStock",
    "PaymentsOfDividends",
    "PaymentsOfFinancingCosts",
    "PaymentsForRepurchaseOfEquityInstruments",
    "ProceedsFromStockOptionsExercised",
    # FX / cash-equivalent reconciliation
    "EffectOfExchangeRateOnCashAndCashEquivalents",
    "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
}

CF_KEYWORDS = [
    "net cash",
    "operating activities",
    "investing activities",
    "financing activities",
    "capital expenditures",
    "purchase of property",
    "acquire property",
    "proceeds from",
    "payments to",
    "repayments",
    "issuance of",
    "dividends",
    "restricted cash",
    "effect of exchange rate",
    "cash equivalents",
]

# ------------------------------------------------------------
# Date & period helpers
# ------------------------------------------------------------


def is_instant_record(rec: Dict[str, Any]) -> bool:
    """
    Balance sheet items are point-in-time (instant) facts.
    Instants usually have only 'end' and no 'start', or start == end.
    """
    end = rec.get("end")
    if not end:
        return False
    start = rec.get("start")
    if not start:
        return True
    return start == end


def duration_days(rec: Dict[str, Any]) -> Optional[int]:
    ds, de = parse_date(rec.get("start")), parse_date(rec.get("end"))
    if not ds or not de:
        return None
    return (de - ds).days


def is_annual_duration(rec: Dict[str, Any]) -> bool:
    d = duration_days(rec)
    if d is None:
        return False
    return d >= ANNUAL_DAYS_MIN


def has_seg(r: Dict[str, Any]) -> bool:
    return ("segment" in r and r["segment"]) or ("segments" in r and r["segments"])


def pick_best_record(recs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Among candidate records for the same tag & period:
    - prefer unsegmented
    - then USD
    - then latest filed
    """
    if not recs:
        raise ValueError("pick_best_record called with empty list")

    pool = [r for r in recs if not has_seg(r)] or recs
    usd = [r for r in pool if r.get("_unit") == "USD"] or pool

    def sort_key(r: Dict[str, Any]):
        filed = r.get("filed") or ""
        end = r.get("end") or ""
        return (filed, end)

    usd.sort(key=sort_key, reverse=True)
    return usd[0]


# ------------------------------------------------------------
# Determine annual BS "anchor" from CompanyFacts
# ------------------------------------------------------------


def determine_annual_bs_anchor(us_gaap: Dict[str, Any]) -> Dict[str, Any]:
    """
    Use the 'Assets' concept to determine the latest annual balance-sheet date
    and basic filing metadata (form, accession if available).

    Returns:
        {
            "report_date": <ISO date string>,
            "filing_type": <"10-K" / "20-F" / fallback>,
            "accession": <accn or "">,
            "filed": <filed date or "">,
            "fiscal_year": <int or None>
        }
    """
    assets_node = us_gaap.get("Assets")
    if not assets_node or "units" not in assets_node:
        raise RuntimeError("Could not find 'Assets' concept in us-gaap to anchor BS date.")

    recs = flatten_units(assets_node["units"])
    recs = [r for r in recs if is_instant_record(r)]
    if not recs:
        raise RuntimeError("No instant 'Assets' records found to anchor BS date.")

    usd = [r for r in recs if r.get("_unit") == "USD"] or recs
    preferred = [r for r in usd if r.get("form") in PREFER_FORMS_ANNUAL]
    pool = preferred or usd

    def sort_key(r: Dict[str, Any]):
        end = r.get("end") or ""
        filed = r.get("filed") or ""
        return (end, filed)

    pool.sort(key=sort_key, reverse=True)
    best = pool[0]

    report_date = best.get("end")
    filed = best.get("filed") or ""
    form = best.get("form") or "10-K"
    accn = best.get("accn") or ""

    fy = None
    d = parse_date(report_date)
    if d:
        fy = d.year

    return {
        "report_date": report_date,
        "filing_type": form,
        "accession": accn,
        "filed": filed,
        "fiscal_year": fy,
    }


# ------------------------------------------------------------
# Statement classification helpers
# ------------------------------------------------------------


def is_bs_tag(tag: str, label: Optional[str]) -> bool:
    if tag in BS_ALLOWLIST:
        return True
    t = (tag or "").lower()
    if any(k in t for k in ["asset", "liabilit", "equity", "receivable", "payable", "inventory", "propertyplantandequipment"]):
        return True
    if label:
        L = label.lower()
        if any(k in L for k in BS_KEYWORDS):
            return True
    return False


def is_is_tag(tag: str, label: Optional[str]) -> bool:
    if tag in IS_ALLOWLIST:
        return True
    t = (tag or "").lower()
    if any(k in t for k in ["revenue", "sales", "grossprofit", "costof", "operatingincome", "operatingprofit", "netincome", "profitloss"]):
        return True
    if label:
        L = label.lower()
        if any(k in L for k in IS_KEYWORDS):
            return True
    return False


def is_cf_tag(tag: str, label: Optional[str]) -> bool:
    if tag in CF_ALLOWLIST:
        return True
    t = (tag or "").lower()
    if any(
        key in t
        for key in [
            "netcashprovidedby",
            "netcashusedin",
            "netcashflowsfromusedin",
            "cashandcashequivalents",
            "capitalexpenditures",
        ]
    ):
        return True
    if label:
        L = label.lower()
        if any(k in L for k in CF_KEYWORDS):
            return True
    return False


# ------------------------------------------------------------
# Multi-year anchor collection
# ------------------------------------------------------------


def collect_annual_anchors(us_gaap: Dict[str, Any], max_filings: int) -> List[Dict[str, Any]]:
    """
    Use 'Assets' concept to collect multiple annual balance sheet anchors.

    Returns list of dicts (latest first):
        {
            "report_date": <ISO end date>,
            "filing_type": <"10-K"/"20-F"/fallback>,
            "accession": <accn or "">,
            "filed": <filed date or "">,
            "fiscal_year": <int or None>
        }
    """
    assets_node = us_gaap.get("Assets")
    if not assets_node or "units" not in assets_node:
        raise RuntimeError("Could not find 'Assets' concept in us-gaap to anchor BS dates.")

    recs = flatten_units(assets_node["units"])
    recs = [r for r in recs if is_instant_record(r)]
    if not recs:
        raise RuntimeError("No instant 'Assets' records found to anchor BS dates.")

    # Prefer USD
    usd = [r for r in recs if r.get("_unit") == "USD"] or recs

    # Restrict to annual forms where possible
    preferred = [r for r in usd if r.get("form") in PREFER_FORMS_ANNUAL]
    pool = preferred or usd

    # Group by end date
    by_end: Dict[str, List[Dict[str, Any]]] = {}
    for r in pool:
        end = r.get("end")
        if not end:
            continue
        by_end.setdefault(end, []).append(r)

    anchors: List[Dict[str, Any]] = []

    for end_date, rec_list in by_end.items():
        best = pick_best_record(rec_list)
        form = best.get("form") or "10-K"
        accn = best.get("accn") or ""
        filed = best.get("filed") or ""
        d = parse_date(end_date)
        fy = d.year if d else None
        anchors.append(
            {
                "report_date": end_date,
                "filing_type": form,
                "accession": accn,
                "filed": filed,
                "fiscal_year": fy,
            }
        )

    # Sort by report_date descending and limit
    anchors.sort(key=lambda a: a["report_date"], reverse=True)
    if max_filings is not None:
        anchors = anchors[:max_filings]

    return anchors


# ------------------------------------------------------------
# Per-filing extraction (for a given report_date)
# ------------------------------------------------------------


def extract_statements_for_date(
    us_gaap: Dict[str, Any],
    report_date: str
) -> Dict[str, List[Dict[str, Any]]]:
    """
    For a given annual report_date, collect BS (instant), IS (annual duration),
    and CF (annual duration) items.
    Returns dict with keys 'bs', 'is', 'cf'.
    """
    bs_items: List[Dict[str, Any]] = []
    is_items: List[Dict[str, Any]] = []
    cf_items: List[Dict[str, Any]] = []

    for tag, node in us_gaap.items():
        units = node.get("units")
        if not isinstance(units, dict):
            continue

        label = node.get("label") or node.get("description") or tag
        records = flatten_units(units)

        # Balance Sheet: instants at report_date
        if is_bs_tag(tag, label):
            instants = [
                r for r in records
                if is_instant_record(r) and r.get("end") == report_date
            ]
            if instants:
                best_bs = pick_best_record(instants)
                bs_items.append(
                    {
                        "tag": tag,
                        "label": label,
                        "amount": float(best_bs["val"]),
                        "unit": best_bs.get("_unit"),
                        "end": best_bs.get("end"),
                    }
                )

        # Income Statement: annual durations ending report_date
        if is_is_tag(tag, label):
            dur_is = [
                r for r in records
                if r.get("end") == report_date and is_annual_duration(r)
            ]
            if dur_is:
                best_is = pick_best_record(dur_is)
                is_items.append(
                    {
                        "tag": tag,
                        "label": label,
                        "amount": float(best_is["val"]),
                        "unit": best_is.get("_unit"),
                        "start": best_is.get("start"),
                        "end": best_is.get("end"),
                    }
                )

        # Cash Flow Statement: annual durations ending report_date
        if is_cf_tag(tag, label):
            dur_cf = [
                r for r in records
                if r.get("end") == report_date and is_annual_duration(r)
            ]
            if dur_cf:
                best_cf = pick_best_record(dur_cf)
                cf_items.append(
                    {
                        "tag": tag,
                        "label": label,
                        "amount": float(best_cf["val"]),
                        "unit": best_cf.get("_unit"),
                        "start": best_cf.get("start"),
                        "end": best_cf.get("end"),
                    }
                )

    # Sort each for readability
    bs_items.sort(key=lambda x: ((x.get("label") or "").lower(), x["tag"]))
    is_items.sort(key=lambda x: ((x.get("label") or "").lower(), x["tag"]))
    cf_items.sort(key=lambda x: ((x.get("label") or "").lower(), x["tag"]))

    return {"bs": bs_items, "is": is_items, "cf": cf_items}


# ------------------------------------------------------------
# Statement payload builder
# ------------------------------------------------------------


def build_statement_payload(
    items: List[Dict[str, Any]],
    report_date: str,
    default_currency: str
) -> Dict[str, Any]:
    line_items: List[Dict[str, Any]] = []
    normalized_order: List[str] = []

    for it in items:
        tag = it["tag"]
        label = it["label"]
        unit = it.get("unit") or default_currency
        amount = it["amount"]

        normalized_order.append(tag)

        line_items.append(
            {
                "tag": tag,
                "label": label,
                "model_role": "",
                "is_core_3_statement": False,
                "is_dcf_key": False,
                "is_comps_key": False,
                "llm_classification": {
                    "best_fit_role": "",
                    "confidence": None,
                },
                "unit": unit,
                "periods": {
                    report_date: amount
                },
                "subitems": [],
            }
        )

    return {
        "normalized_order": normalized_order,
        "line_items": line_items,
    }


def find_currency(*item_lists: List[Dict[str, Any]]) -> Optional[str]:
    for items in item_lists:
        for it in items:
            if it.get("unit"):
                return it["unit"]
    return None


# ------------------------------------------------------------
# Core extraction & structuring
# ------------------------------------------------------------


def extract_single_year_structured(cik: int, ticker: str, edgar_client: Optional[EdgarClient] = None) -> Dict[str, Any]:
    """
    Build a JSON object conforming to single-year filing schema,
    with balance sheet, income statement, and cash flow statement populated
    for the latest annual period based on Assets (BS anchor).

    Args:
        cik: Company CIK number
        ticker: Company ticker symbol
        edgar_client: Optional EdgarClient instance (creates new one if not provided)

    Returns:
        Structured JSON matching single-year filing template
    """
    client = edgar_client or EdgarClient()

    # 1) Company facts
    facts = client.get_company_facts(cik)
    entity_name = facts.get("entityName") or f"Company {ticker}"
    facts_root = (facts or {}).get("facts", {})
    us_gaap = facts_root.get("us-gaap", {})
    if not us_gaap:
        raise RuntimeError(f"No 'us-gaap' section found in company facts for CIK {cik}.")

    # 2) Determine anchor from Assets
    anchor = determine_annual_bs_anchor(us_gaap)
    report_date = anchor["report_date"]
    filing_type = anchor["filing_type"]
    accession = anchor["accession"]
    fiscal_year = anchor["fiscal_year"]
    fiscal_year_str = str(fiscal_year) if fiscal_year is not None else ""
    fiscal_period = "FY"

    # 3) Collect BS, IS, CF items at that same report_date
    stmt_items = extract_statements_for_date(us_gaap, report_date)
    bs_items = stmt_items["bs"]
    is_items = stmt_items["is"]
    cf_items = stmt_items["cf"]

    # 4) Determine statement currency (fallback to USD)
    statement_currency = (
        find_currency(bs_items, is_items, cf_items)
        or "USD"
    )

    # 5) Build line_items and normalized_order lists for each statement
    bs_payload = build_statement_payload(bs_items, report_date, statement_currency)
    is_payload = build_statement_payload(is_items, report_date, statement_currency)
    cf_payload = build_statement_payload(cf_items, report_date, statement_currency)

    # 6) Assemble the full document matching your template
    payload: Dict[str, Any] = {
        "metadata": {
            "cik": f"{cik:010d}",
            "ticker": ticker,
            "company_name": entity_name,
            "filing_type": filing_type,
            "filing_accession": accession,
            "fiscal_year": fiscal_year_str,
            "fiscal_period": fiscal_period,
            "statement_currency": statement_currency,
            "us_gaap_taxonomy_year": "",
        },
        "statements": {
            "income_statement": {
                "statement_type": "income_statement",
                "normalized_order": is_payload["normalized_order"],
                "line_items": is_payload["line_items"],
            },
            "balance_sheet": {
                "statement_type": "balance_sheet",
                "normalized_order": bs_payload["normalized_order"],
                "line_items": bs_payload["line_items"],
            },
            "cash_flow_statement": {
                "statement_type": "cash_flow_statement",
                "normalized_order": cf_payload["normalized_order"],
                "line_items": cf_payload["line_items"],
            },
        },
        "comps_config": {
            "sector": "",
            "industry": "",
            "peer_selection_rule": {
                "by_sector_industry": False,
                "market_cap_tolerance_pct": None,
            },
            "key_metrics": [],
            "metric_sources": {},
        },
    }

    return payload


def extract_multi_year_structured(
    cik: int,
    ticker: str,
    max_filings: int = 5,
    edgar_client: Optional[EdgarClient] = None
) -> Dict[str, Any]:
    """
    Build a JSON object conforming to multi-year filing schema,
    with multiple annual filings (latest first).

    Args:
        cik: Company CIK number
        ticker: Company ticker symbol
        max_filings: Maximum number of annual filings to include (default: 5)
        edgar_client: Optional EdgarClient instance (creates new one if not provided)

    Returns:
        Structured JSON matching multi-year filing template
    """
    client = edgar_client or EdgarClient()

    # 1) Company facts
    facts = client.get_company_facts(cik)
    entity_name = facts.get("entityName") or f"Company {ticker}"
    facts_root = (facts or {}).get("facts", {})
    us_gaap = facts_root.get("us-gaap", {})
    if not us_gaap:
        raise RuntimeError(f"No 'us-gaap' section found in company facts for CIK {cik}.")

    # 2) Multi-year anchors from Assets
    anchors = collect_annual_anchors(us_gaap, max_filings)
    if not anchors:
        raise RuntimeError("No annual anchors could be determined from Assets.")

    filings_payload: List[Dict[str, Any]] = []

    # We'll determine company-level currency from the most recent filing
    currency_candidate: Optional[str] = None

    for anchor in anchors:
        report_date = anchor["report_date"]
        filing_type = anchor["filing_type"]
        accession = anchor["accession"]
        fy = anchor["fiscal_year"]
        fiscal_year_str = str(fy) if fy is not None else ""
        fiscal_period = "FY"

        # Extract items for this report_date
        stmt_items = extract_statements_for_date(us_gaap, report_date)
        bs_items = stmt_items["bs"]
        is_items = stmt_items["is"]
        cf_items = stmt_items["cf"]

        # For the first (most recent) filing, decide a currency
        if currency_candidate is None:
            currency_candidate = find_currency(bs_items, is_items, cf_items) or "USD"

        # Build statement payloads
        bs_payload = build_statement_payload(bs_items, report_date, currency_candidate)
        is_payload = build_statement_payload(is_items, report_date, currency_candidate)
        cf_payload = build_statement_payload(cf_items, report_date, currency_candidate)

        # filing_id: use accession if present, else ticker + date
        filing_id = accession if accession else f"{ticker}_{report_date}"

        filings_payload.append(
            {
                "filing_id": filing_id,
                "filing_type": filing_type,
                "fiscal_year": fiscal_year_str,
                "fiscal_period": fiscal_period,
                "statements": {
                    "income_statement": {
                        "statement_type": "income_statement",
                        "normalized_order": is_payload["normalized_order"],
                        "line_items": is_payload["line_items"],
                    },
                    "balance_sheet": {
                        "statement_type": "balance_sheet",
                        "normalized_order": bs_payload["normalized_order"],
                        "line_items": bs_payload["line_items"],
                    },
                    "cash_flow_statement": {
                        "statement_type": "cash_flow_statement",
                        "normalized_order": cf_payload["normalized_order"],
                        "line_items": cf_payload["line_items"],
                    },
                },
            }
        )

    # 3) Company-level metadata
    statement_currency = currency_candidate or "USD"

    payload: Dict[str, Any] = {
        "company": {
            "cik": f"{cik:010d}",
            "ticker": ticker,
            "company_name": entity_name,
            "statement_currency": statement_currency,
            "us_gaap_taxonomy_year": "",  # not exposed by CompanyFacts; can be filled offline
        },
        "filings": filings_payload,
        "comps_config": {
            "peer_selection_rule": {
                "by_sector_industry": False,
                "market_cap_tolerance_pct": None,
            },
            "key_metrics": [
                {
                    "name": "",
                    "type": "",
                    "denominator_role": "",
                    "is_industry_standard": False,
                }
            ],
        },
    }

    return payload


# ------------------------------------------------------------
# Classification and tagging pipeline
# ------------------------------------------------------------

"""
Classification pipeline for tagging required modeling line items.

This section provides a minimal, deterministic, model-ready system for tagging
only the required modeling line items in EDGAR JSON. All other items remain untouched.
"""

# Required model items - these are the ONLY items that should be tagged
# 
# IMPORTANT: Only raw GAAP line items are taggable. All margins, ratios, and tax rates
# are computed downstream in the modeling engine. EDGAR does NOT provide margins or
# payout ratios as line items. We must never attempt to classify or tag them.
#
# Margins, tax rates, and payout ratios are NOT EDGAR-provided facts and must be
# computed after structured JSON creation. The structured-output pipeline tags ONLY
# raw GAAP line items.
#
# Ordered by specificity: more specific items first to reduce conflicts
REQUIRED_MODEL_ITEMS = [
    # Income Statement - Raw GAAP accounts only
    "Operating Costs",  # COGS + SG&A + R&D + other operating expenses
    "Gross Costs",  # COGS - direct cost of goods sold
    "Revenue",  # Total revenue/sales
    "Tax Expense",  # Raw GAAP tax expense (NOT tax rate)
    # Balance Sheet - Raw GAAP accounts only
    "PP&E",  # Property, Plant and Equipment
    "Inventory",  # Inventory
    "Accounts Payable",  # Accounts Payable
    "Accounts Receivable",  # Accounts Receivable
    "Accrued Expenses",  # Accrued Liabilities
    # Cash Flow Statement - Raw GAAP accounts only
    "Share Repurchases",  # Payments for repurchase of common stock
    "Debt Amount",  # Debt issuances + repayments + balance sheet debt
    "Dividend Payout",  # Raw dividends paid (NOT payout ratio)
]

# EXPLICITLY NON-TAGGABLE (COMPUTED) ITEMS - These must NEVER be mapped to EDGAR tags:
# - Operating Margin (computed: Operating Income / Revenue)
# - Gross Margin (computed: (Revenue - COGS) / Revenue)
# - EBITDA (computed: Operating Income + Depreciation & Amortization)
# - EBITDA Margin (computed: EBITDA / Revenue)
# - Net Margin (computed: Net Income / Revenue)
# - Tax Rate (computed: Tax Expense / Pre-Tax Income)
# - Dividend as % of Net Income (computed: Dividends Paid / Net Income)
# - Any "% of revenue" or ratio-like metric
# - Any margin-like label returned by the LLM


def extract_available_labels(edgar_json: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Extract all available EDGAR labels with their tags and statement types.
    
    Args:
        edgar_json: The structured EDGAR JSON with statements
        
    Returns:
        List of dictionaries with label, tag, and statement:
        [
            {"label": "...", "tag": "...", "statement": "income_statement"},
            ...
        ]
    """
    labels: List[Dict[str, str]] = []
    statements = edgar_json.get("statements", {})
    
    statement_mapping = {
        "income_statement": "income_statement",
        "balance_sheet": "balance_sheet",
        "cash_flow_statement": "cash_flow_statement",
    }
    
    for stmt_key, statement_type in statement_mapping.items():
        statement = statements.get(stmt_key, {})
        line_items = statement.get("line_items", [])
        
        for item in line_items:
            label = item.get("label", "")
            tag = item.get("tag", "")
            if label and tag:
                # Avoid duplicates by checking if label+tag combo already exists
                if not any(l["label"] == label and l["tag"] == tag for l in labels):
                    labels.append({
                        "label": label,
                        "tag": tag,
                        "statement": statement_type,
                    })
    
    return labels


def _validate_match(required_item: str, matched_tag: str, matched_label: str) -> Optional[str]:
    """
    Validate that an LLM match makes semantic sense.
    
    Returns error message if validation fails, None if valid.
    """
    tag_lower = matched_tag.lower()
    label_lower = matched_label.lower()
    
    # Critical validations - reject margins, ratios, and computed metrics
    # Reject any match that contains margin/ratio/rate indicators (unless it's a raw account)
    margin_indicators = ["margin", "ratio", "rate", "%", "percent", "percentage"]
    for indicator in margin_indicators:
        if indicator in tag_lower or indicator in label_lower:
            # Allow if it's clearly a raw account (e.g., "Tax Expense" contains "expense" not "rate")
            if required_item == "Tax Expense" and "expense" in tag_lower:
                continue  # Tax Expense is OK even if it contains "rate" somewhere
            # Reject if it looks like a computed metric
            if any(m in tag_lower or m in label_lower for m in ["operating margin", "gross margin", "ebitda margin", "net margin", "payout ratio", "tax rate"]):
                return f"Match contains '{indicator}' - margins and ratios are computed downstream, not tagged from EDGAR"
    
    # Reject EBITDA, EBITDA margin, or any EBITDA-related computed metric
    if "ebitda" in tag_lower or "ebitda" in label_lower:
        return "EBITDA is a computed metric (Operating Income + D&A) - tag underlying raw accounts instead"
    
    # Reject operating margin, gross margin, net margin
    if "operating margin" in tag_lower or "operating margin" in label_lower:
        return "Operating Margin is computed (Operating Income / Revenue) - tag raw accounts instead"
    if "gross margin" in tag_lower or "gross margin" in label_lower:
        return "Gross Margin is computed ((Revenue - COGS) / Revenue) - tag raw accounts instead"
    if "net margin" in tag_lower or "net margin" in label_lower:
        return "Net Margin is computed (Net Income / Revenue) - tag raw accounts instead"
    
    # Reject tax rate (we only tag tax expense)
    if "tax rate" in tag_lower or "tax rate" in label_lower or ("tax" in tag_lower and "rate" in tag_lower):
        if "expense" not in tag_lower and "expense" not in label_lower:
            return "Tax Rate is computed (Tax Expense / Pre-Tax Income) - tag Tax Expense instead"
    
    # Revenue should NOT be operating income, EBITDA, or margins
    if required_item == "Revenue":
        if "operatingincome" in tag_lower or "operatingincome" in label_lower:
            return "Revenue matched to Operating Income - Revenue is the top line, Operating Income is after expenses"
        if "ebitda" in tag_lower or "ebitda" in label_lower:
            return "Revenue matched to EBITDA - Revenue is the top line, EBITDA is calculated from revenue"
        if "grossprofit" in tag_lower or "grossprofit" in label_lower:
            return "Revenue matched to Gross Profit - Revenue is the top line, Gross Profit is Revenue minus COGS"
    
    # Operating Costs should be TOTAL operating expenses, NOT individual components like COGS
    if required_item == "Operating Costs":
        if "revenue" in tag_lower or "revenue" in label_lower:
            if "cost" not in tag_lower and "cost" not in label_lower and "expense" not in tag_lower:
                return "Operating Costs matched to Revenue - Operating Costs are expenses, not revenue"
        # Reject COGS - Operating Costs should match TOTAL operating expenses, not individual components
        if ("costofgoods" in tag_lower or "costofgoods" in label_lower or 
            "cogs" in tag_lower or "cogs" in label_lower):
            if "total" not in tag_lower and "total" not in label_lower:
                return "Operating Costs matched to COGS - Operating Costs should match TOTAL operating expenses, not individual components like COGS"
    
    # Gross Costs should be COGS-related, not gross profit or gross margin
    if required_item == "Gross Costs":
        if "grossprofit" in tag_lower or "grossprofit" in label_lower:
            return "Gross Costs matched to Gross Profit - Gross Costs is COGS, Gross Profit is Revenue minus COGS"
        if "grossmargin" in tag_lower or "grossmargin" in label_lower:
            return "Gross Costs matched to Gross Margin - Gross Margin is computed, tag COGS instead"
    
    # Tax Expense should NOT be tax rate
    if required_item == "Tax Expense":
        if "tax rate" in tag_lower or "tax rate" in label_lower:
            return "Tax Expense matched to Tax Rate - Tax Rate is computed (Tax Expense / Pre-Tax Income), tag Tax Expense instead"
    
    return None  # Validation passed


def _try_exact_match(required_item: str, available_labels: List[Dict[str, str]]) -> Optional[Dict[str, str]]:
    """
    Try to find exact or near-exact matches before using LLM.
    
    Uses heuristics and common patterns to match required items to EDGAR tags.
    Returns match dict if found, None otherwise.
    """
    required_lower = required_item.lower().strip()
    
    # Define expected tag patterns for each required item
    # NOTE: Only raw GAAP accounts - no margins, ratios, or computed metrics
    expected_patterns = {
        "revenue": [
            "revenues", "revenue", "salesrevenuenet", "revenuefromcontract",
            "revenuefromcontractwithcustomer", "salesrevenue"
        ],
        "operating costs": [
            # ONLY match total operating expenses - NOT individual components like COGS or SG&A
            "totaloperatingexpenses", "operatingexpenses", "operatingcosts",
            # Do NOT include COGS or SG&A here - those are separate line items
        ],
        "gross costs": [
            # ONLY match COGS (cost of goods sold) - NOT total operating expenses
            "costofgoodsandservicessold", "costofgoodsandsold", "cogs",
            "costofrevenue", "costofsales", "costofgoodsandservices"
        ],
        "tax expense": [
            "incometaxexpense", "incometaxexpensebenefit", "provisionforincometax",
            "incometaxes", "taxexpense", "incometaxexpensebenefitcontinuingoperations"
        ],
        "pp&e": [
            "propertyplantandequipmentnet", "propertyplantandequipment",
            "ppe", "propertyplantandequipmentgross"
        ],
        "inventory": [
            "inventory", "inventories", "inventorynet", "inventorycurrent"
        ],
        "accounts payable": [
            # Prefer separate Accounts Payable tags - avoid combined tags if possible
            "accountspayablecurrent", "accountspayable", "tradepayables",
            # Only use combined tag as last resort if no separate tag exists
            # "accountspayableandaccruedliabilities"  # Removed - causes conflicts with Accrued Expenses
        ],
        "accounts receivable": [
            "accountsreceivablenetcurrent", "receivablesnetcurrent",
            "accountsreceivable", "tradereceivables"
        ],
        "accrued expenses": [
            "accruedliabilitiescurrent", "accruedexpenses", "accruedliabilities",
            "accruedexpensesandothercurrentliabilities"
        ],
        "share repurchases": [
            "paymentsforrepurchaseofcommonstock", "paymentsforrepurchaseofequity",
            "treasurystock", "stockrepurchases", "paymentsforrepurchase"
        ],
        "debt amount": [
            "debtcurrent", "longtermdebtcurrent", "shorttermdebt",
            "debtandcapitalleaseobligationscurrent", "totaldebt"
        ],
        "dividend payout": [
            "paymentsofdividends", "dividendspaid", "cashdividends",
            "paymentsofdividendscommonstock"
        ],
    }
    
    # Get patterns for this required item
    patterns = expected_patterns.get(required_lower, [])
    
    # Special handling for items that should avoid combined tags
    avoid_combined_tags = required_lower in ["accounts payable", "accrued expenses"]
    
    # Collect all matches first
    matches = []
    for label_dict in available_labels:
        tag_lower = label_dict["tag"].lower()
        label_lower = label_dict["label"].lower()
        
        # Check against expected patterns
        for pattern in patterns:
            if pattern in tag_lower or pattern in label_lower:
                is_combined = "and" in tag_lower or "and" in label_lower
                matches.append({
                    "match": label_dict,
                    "pattern": pattern,
                    "is_combined": is_combined,
                })
                break
    
    if not matches:
        return None
    
    # If we should avoid combined tags, prefer separate tags
    if avoid_combined_tags:
        separate_matches = [m for m in matches if not m["is_combined"]]
        if separate_matches:
            matches = separate_matches
    
    # Return the first match (prioritized by pattern order and combined tag avoidance)
    best_match = matches[0]
    logger.info(
        f"Found exact/near-exact match for '{required_item}': "
        f"'{best_match['match']['label']}' (tag: {best_match['match']['tag']})"
    )
    return {
        "required_item": required_item,
        "matched_label": best_match["match"]["label"],
        "matched_tag": best_match["match"]["tag"],
        "reason": f"Exact match via pattern '{best_match['pattern']}'",
    }


@retry(
    stop=stop_after_attempt(settings.LLM_MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((Exception,)),
    reraise=True,
)
def match_required_item_to_label(required_item: str, available_labels: List[Dict[str, str]]) -> Dict[str, str]:
    """
    Use LLM to match one required modeling item to the single best EDGAR label.
    
    Args:
        required_item: One of the REQUIRED_MODEL_ITEMS
        available_labels: List of available label dictionaries
        
    Returns:
        Dictionary with:
        {
            "required_item": "...",
            "matched_label": "...",
            "matched_tag": "...",
            "reason": "..."
        }
    """
    if not settings.LLM_ENABLED:
        logger.debug(f"LLM disabled, skipping match for {required_item}")
        return {
            "required_item": required_item,
            "matched_label": "",
            "matched_tag": "",
            "reason": "LLM disabled",
        }
    
    if not settings.OPENAI_API_KEY or not settings.OPENAI_API_KEY.strip():
        logger.warning("OpenAI API key not configured, skipping match")
        return {
            "required_item": required_item,
            "matched_label": "",
            "matched_tag": "",
            "reason": "API key not configured",
        }
    
    if not available_labels:
        logger.warning(f"No available labels provided for {required_item}")
        return {
            "required_item": required_item,
            "matched_label": "",
            "matched_tag": "",
            "reason": "No labels available",
        }
    
    # Try exact matching first (before LLM)
    exact_match = _try_exact_match(required_item, available_labels)
    if exact_match:
        return exact_match
    
    # Format labels for prompt
    labels_text = "\n".join(
        f"- {label['label']} → {label['tag']}" for label in available_labels
    )
    
    # Define what each required item means (to help LLM make better matches)
    # NOTE: Only raw GAAP accounts are taggable. Margins and ratios are computed downstream.
    item_definitions = {
        "Revenue": "Total revenue/sales - the top line of the income statement. Raw GAAP account. NOT operating income, NOT EBITDA, NOT any margin.",
        "Operating Costs": "TOTAL operating expenses - the sum of COGS, SG&A, R&D, and all other operating expenses. Look for tags like 'TotalOperatingExpenses' or 'OperatingExpenses'. DO NOT match individual components like COGS or SG&A - those are separate line items. Raw GAAP account. NOT a margin or ratio.",
        "Gross Costs": "Cost of goods sold (COGS) ONLY - direct costs of producing goods/services. Look for tags like 'CostOfGoodsAndServicesSold' or 'CostOfRevenue'. This is a component of Operating Costs, but should be matched separately. Raw GAAP account. NOT gross margin or gross profit.",
        "Tax Expense": "Income tax expense - the actual tax paid on income. Raw GAAP account. NOT tax rate (which is computed as Tax Expense / Pre-Tax Income).",
        "PP&E": "Property, Plant and Equipment (net) - long-term tangible assets. Raw GAAP account on balance sheet.",
        "Inventory": "Inventory - goods held for sale. Raw GAAP account - current asset on balance sheet.",
        "Accounts Payable": "Accounts Payable ONLY - money owed to suppliers. Prefer separate 'AccountsPayable' or 'AccountsPayableCurrent' tags. AVOID combined tags like 'AccountsPayableAndAccruedLiabilities' unless no separate tag exists. Raw GAAP account - current liability on balance sheet.",
        "Accounts Receivable": "Accounts Receivable - money owed by customers. Raw GAAP account - current asset on balance sheet.",
        "Accrued Expenses": "Accrued Liabilities ONLY - expenses incurred but not yet paid. Prefer separate 'AccruedLiabilitiesCurrent' or 'AccruedExpenses' tags. AVOID combined tags like 'AccountsPayableAndAccruedLiabilities' unless no separate tag exists. Raw GAAP account - current liability.",
        "Share Repurchases": "Payments for repurchase of common stock or treasury stock. Raw GAAP account - cash flow item.",
        "Debt Amount": "Debt issuances, repayments, or balance sheet debt. Raw GAAP account. NOT a debt ratio.",
        "Dividend Payout": "Dividends paid to shareholders - raw cash outflow. Raw GAAP account - cash flow item. NOT dividend payout ratio (which is computed as Dividends Paid / Net Income).",
    }
    
    item_definition = item_definitions.get(required_item, "")
    
    # Improved prompt with definitions and validation rules
    prompt = f"""You are aligning Denari's standardized modeling line items with EDGAR/XBRL labels.

REQUIRED MODEL ITEM: {required_item}
{item_definition}

AVAILABLE EDGAR LABELS (label → tag):
{labels_text}

Return ONLY a JSON object with:
{{
  "matched_label": "<best matching label>",
  "matched_tag": "<the corresponding EDGAR tag>",
  "reason": "<one sentence explanation>"
}}

CRITICAL RULES:
- Select exactly one best match that semantically matches the definition above.
- Match ONLY raw GAAP accounts - NEVER match margins, ratios, or computed metrics.
- REJECT any match that contains "margin", "ratio", "rate" (as a percentage), or "%" unless it's clearly a raw account name.
- For Revenue: Match total revenue/sales, NOT operating income, NOT EBITDA, NOT any margin.
- For Operating Costs: Match TOTAL operating expenses (look for "TotalOperatingExpenses" or "OperatingExpenses"). DO NOT match individual components like COGS or SG&A - those are matched separately.
- For Gross Costs: Match cost of goods sold (COGS) specifically - look for "CostOfGoodsAndServicesSold" or "CostOfRevenue". This is separate from Operating Costs.
- For Accounts Payable: Prefer separate "AccountsPayable" or "AccountsPayableCurrent" tags. AVOID combined tags like "AccountsPayableAndAccruedLiabilities" unless no separate tag exists.
- For Accrued Expenses: Prefer separate "AccruedLiabilitiesCurrent" or "AccruedExpenses" tags. AVOID combined tags like "AccountsPayableAndAccruedLiabilities" unless no separate tag exists.
- For Tax Expense: Match the actual tax expense amount, NOT tax rate (tax rate is computed downstream).
- NEVER match EBITDA, EBITDA margin, operating margin, gross margin, net margin, or any ratio.
- Prefer the most aggregated or standard label if multiple exist, BUT avoid combined tags when separate tags exist.
- Do NOT return arrays, lists, alternatives, or commentary."""
    
    client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=settings.LLM_TIMEOUT_SECONDS)
    
    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a financial data matching expert. Match required financial modeling items to EDGAR/XBRL labels accurately and return only valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,  # Low temperature for consistent matching
            response_format={"type": "json_object"},
        )
        
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from LLM")
        
        result = json.loads(content)
        matched_label = result.get("matched_label", "")
        matched_tag = result.get("matched_tag", "")
        reason = result.get("reason", "")
        
        # Validate the match makes semantic sense
        if matched_tag:
            validation_error = _validate_match(required_item, matched_tag, matched_label)
            if validation_error:
                logger.warning(
                    f"LLM match validation failed for '{required_item}': {validation_error}. "
                    f"Matched tag: '{matched_tag}', label: '{matched_label}'. "
                    f"Rejecting match and trying exact matching instead."
                )
                # Try exact matching as fallback
                exact_match = _try_exact_match(required_item, available_labels)
                if exact_match:
                    logger.info(f"Using exact match fallback for '{required_item}'")
                    return exact_match
                # If exact match also fails, return empty match
                return {
                    "required_item": required_item,
                    "matched_label": "",
                    "matched_tag": "",
                    "reason": f"LLM match failed validation: {validation_error}",
                }
        
        # Verify the matched_tag exists in available_labels
        if matched_tag and not any(l["tag"] == matched_tag for l in available_labels):
            logger.warning(
                f"LLM returned tag '{matched_tag}' not in available labels for '{required_item}'. "
                f"Attempting to find tag by label '{matched_label}'"
            )
            # Try to find tag by label
            found_by_label = False
            for label_dict in available_labels:
                if label_dict["label"] == matched_label:
                    matched_tag = label_dict["tag"]
                    found_by_label = True
                    logger.info(f"Found tag '{matched_tag}' by label '{matched_label}'")
                    break
            
            if not found_by_label:
                logger.error(
                    f"Could not find tag for '{required_item}'. "
                    f"LLM returned label '{matched_label}' and tag '{matched_tag}', "
                    f"but neither matches available labels."
                )
                # Return empty match to indicate failure
                return {
                    "required_item": required_item,
                    "matched_label": "",
                    "matched_tag": "",
                    "reason": f"Tag '{matched_tag}' not found in available labels",
                }
        
        return {
            "required_item": required_item,
            "matched_label": matched_label,
            "matched_tag": matched_tag,
            "reason": reason,
        }
        
    except Exception as e:
        logger.error(f"LLM matching failed for {required_item}: {e}")
        raise


def model_role_for(required_item: str) -> str:
    """
    Map each required item to Denari's internal canonical model roles.
    
    NOTE: Only raw GAAP accounts are mapped. Margins, ratios, and computed metrics
    (like EBITDA, Gross Margin, Tax Rate) are NOT mapped here - they are computed
    downstream in the modeling engine.
    
    Args:
        required_item: One of the REQUIRED_MODEL_ITEMS (raw GAAP accounts only)
        
    Returns:
        Model role constant string (e.g., "IS_REVENUE")
    """
    mapping: Dict[str, str] = {
        # Income Statement - Raw GAAP accounts only
        "Revenue": IS_REVENUE,
        "Operating Costs": IS_OPERATING_EXPENSE,  # Total operating expenses (COGS + SG&A + R&D + other)
        "Gross Costs": IS_COGS,  # Cost of goods sold
        "Tax Expense": IS_TAX_EXPENSE,  # Raw tax expense (NOT tax rate)
        # Balance Sheet - Raw GAAP accounts only
        "PP&E": BS_PP_AND_E,
        "Inventory": BS_INVENTORY,
        "Accounts Payable": BS_ACCOUNTS_PAYABLE,
        "Accounts Receivable": BS_ACCOUNTS_RECEIVABLE,
        "Accrued Expenses": BS_ACCRUED_LIABILITIES,
        # Cash Flow Statement - Raw GAAP accounts only
        "Share Repurchases": CF_SHARE_REPURCHASES,
        "Debt Amount": BS_DEBT_CURRENT,  # Using current debt as primary
        "Dividend Payout": CF_DIVIDENDS_PAID,  # Raw dividends paid (NOT payout ratio)
    }
    
    role = mapping.get(required_item, "")
    if not role:
        logger.warning(f"No model_role mapping for required item: {required_item}")
    
    return role


def build_mapping(edgar_json: Dict[str, Any]) -> Dict[str, str]:
    """
    Build mapping from required items to EDGAR tags.
    
    Loops over REQUIRED_MODEL_ITEMS, calls match_required_item_to_label for each,
    and produces a dict mapping required_item -> matched_tag.
    
    Implements uniqueness validation: ensures each tag maps to only one required item.
    If conflicts occur, the first match wins (more specific items are matched first).
    
    Args:
        edgar_json: The structured EDGAR JSON
        
    Returns:
        Dictionary mapping required_item -> matched_tag
        Example: {"Revenue": "Revenues", "PP&E": "PropertyPlantAndEquipmentNet", ...}
    """
    labels = extract_available_labels(edgar_json)
    logger.info(f"Extracted {len(labels)} available labels from EDGAR JSON")
    
    mapping: Dict[str, str] = {}
    tag_to_required_item: Dict[str, str] = {}  # Track which tags are already mapped
    
    for required_item in REQUIRED_MODEL_ITEMS:
        logger.info(f"Matching required item: {required_item}")
        match_result = match_required_item_to_label(required_item, labels)
        matched_tag = match_result.get("matched_tag", "")
        matched_label = match_result.get("matched_label", "")
        
        if matched_tag:
            # Check for conflicts: if tag already mapped to another required item
            if matched_tag in tag_to_required_item:
                conflicting_item = tag_to_required_item[matched_tag]
                logger.warning(
                    f"Tag conflict: '{matched_tag}' already mapped to '{conflicting_item}'. "
                    f"Skipping match for '{required_item}' (keeping '{conflicting_item}' mapping)."
                )
                logger.warning(
                    f"  '{required_item}' matched to label '{matched_label}' but tag '{matched_tag}' "
                    f"is already used by '{conflicting_item}'. This may indicate an LLM matching error."
                )
                continue
            
            # Add to mapping
            mapping[required_item] = matched_tag
            tag_to_required_item[matched_tag] = required_item
            logger.info(f"Matched '{required_item}' -> '{matched_tag}' ({matched_label})")
        else:
            logger.warning(f"No match found for required item: {required_item}")
    
    # Validation: check that we got mappings for all required items
    missing_items = set(REQUIRED_MODEL_ITEMS) - set(mapping.keys())
    if missing_items:
        logger.warning(
            f"Missing mappings for {len(missing_items)} required items: {', '.join(missing_items)}"
        )
    
    logger.info(f"Built mapping for {len(mapping)}/{len(REQUIRED_MODEL_ITEMS)} required items")
    
    # Log summary of mappings
    if mapping:
        logger.info("Mapping summary:")
        for req_item, tag in sorted(mapping.items()):
            logger.info(f"  {req_item:20s} -> {tag}")
    
    return mapping


def apply_mapping(edgar_json: Dict[str, Any], mapping: Dict[str, str]) -> Dict[str, Any]:
    """
    Apply the mapping to the EDGAR JSON, updating ONLY matched line items.
    
    IMPORTANT: Only raw GAAP accounts are tagged. Margins, ratios, and computed metrics
    (like EBITDA, Gross Margin, Tax Rate) are NOT tagged here - they are computed
    downstream in the modeling engine.
    
    Modifies ONLY the matched EDGAR line items:
    - Adds/updates model_role, is_core_3_statement, is_dcf_key, is_comps_key
    - Leaves all other items untouched
    
    Validates that all mappings can be applied and logs any issues.
    
    Args:
        edgar_json: The structured EDGAR JSON to update
        mapping: Dictionary mapping required_item -> matched_tag (raw GAAP accounts only)
        
    Returns:
        Updated EDGAR JSON (modified in-place)
    """
    statements = edgar_json.get("statements", {})
    
    # Create reverse mapping: tag -> required_item
    tag_to_required_item: Dict[str, str] = {}
    for required_item, matched_tag in mapping.items():
        if matched_tag in tag_to_required_item:
            logger.error(
                f"Duplicate tag mapping detected: '{matched_tag}' mapped to both "
                f"'{tag_to_required_item[matched_tag]}' and '{required_item}'. "
                f"This should not happen after build_mapping validation."
            )
        tag_to_required_item[matched_tag] = required_item
    
    # Track which tags were actually found and updated
    tags_found: Dict[str, str] = {}  # tag -> required_item
    tags_not_found: List[str] = []  # tags from mapping that weren't found in JSON
    
    # Update line items
    for stmt_key in ["income_statement", "balance_sheet", "cash_flow_statement"]:
        statement = statements.get(stmt_key, {})
        line_items = statement.get("line_items", [])
        
        for line_item in line_items:
            tag = line_item.get("tag", "")
            if tag in tag_to_required_item:
                required_item = tag_to_required_item[tag]
                model_role = model_role_for(required_item)
                
                if not model_role:
                    logger.warning(f"No model_role mapping for required item: {required_item}")
                    continue
                
                # Get flags from model_role_map
                flags = get_model_role_flags(model_role)
                
                # Update line item in-place
                line_item["model_role"] = model_role
                line_item["is_core_3_statement"] = True  # All required items are core
                line_item["is_dcf_key"] = True  # All required items are DCF keys
                line_item["is_comps_key"] = flags.get("is_comps_key", False)
                line_item["llm_classification"] = {
                    "best_fit_role": model_role,
                    "confidence": 1.0,
                }
                
                tags_found[tag] = required_item
                logger.debug(f"Tagged '{line_item.get('label', '')}' (tag: {tag}) with model_role '{model_role}'")
    
    # Check for tags in mapping that weren't found in the JSON
    for required_item, matched_tag in mapping.items():
        if matched_tag not in tags_found:
            tags_not_found.append(f"{required_item} -> {matched_tag}")
    
    if tags_not_found:
        logger.warning(
            f"Found {len(tags_not_found)} tag(s) in mapping that were not found in JSON: "
            f"{', '.join(tags_not_found)}"
        )
    
    # Summary
    logger.info(
        f"Applied mapping: {len(tags_found)}/{len(mapping)} tags successfully updated. "
        f"Missing: {len(tags_not_found)}"
    )
    
    return edgar_json


def generate_structured_output(edgar_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Top-level pipeline function for generating structured output.
    
    Pipeline:
    1. Extract available labels
    2. Build mapping from required items to tags
    3. Apply mapping to JSON
    4. Return enriched JSON
    
    This is the only API the backend should call going forward.
    
    Args:
        edgar_json: The structured EDGAR JSON (without classifications)
        
    Returns:
        Enriched EDGAR JSON with only required items tagged
    """
    if not settings.LLM_ENABLED:
        logger.info("LLM disabled, skipping structured output generation")
        return edgar_json
    
    logger.info("Starting structured output generation pipeline")
    
    # Step 1: Extract available labels
    labels = extract_available_labels(edgar_json)
    logger.info(f"Extracted {len(labels)} available labels")
    
    # Step 2: Build mapping
    mapping = build_mapping(edgar_json)
    logger.info(f"Built mapping for {len(mapping)} required items")
    
    # Step 3: Apply mapping
    enriched = apply_mapping(edgar_json, mapping)
    
    logger.info(f"Completed structured output generation: {len(mapping)} items tagged")
    return enriched

