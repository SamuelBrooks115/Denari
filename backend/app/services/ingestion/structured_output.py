"""
structured_output.py — Structured 3-statement extraction from EDGAR Company Facts.

Provides functions to extract Balance Sheet, Income Statement, and Cash Flow Statement
data from EDGAR XBRL Company Facts API and return structured JSON matching the
single-year and multi-year filing templates.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger
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

