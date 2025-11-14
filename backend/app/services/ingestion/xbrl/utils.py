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

    # Income Statement
    if any(keyword in text for keyword in ("revenue", "sales")):
        return "revenue"
    if "cost of revenue" in text or "cost of goods" in text:
        return "cogs"
    if "gross profit" in text:
        return "gross_profit"
    if "operating expense" in text or "operating cost" in text:
        return "operating_expense"
    if contains("research", "development") or "r&d" in text:
        return "research_and_development"
    if ("selling" in text and "administrative" in text) or "sga" in text or "s&g" in text:
        return "selling_general_administrative"
    if "operating income" in text or "operating profit" in text:
        return "operating_income"
    if "interest expense" in text or ("interest" in text and "debt" in text and "expense" in text):
        return "interest_expense"
    if "depreciation" in text and "amortization" in text:
        return "depreciation_amortization"
    if "depreciation" in text and "amortization" not in text:
        return "depreciation_amortization"
    if "amortization" in text and "intangible" in text:
        return "depreciation_amortization"
    if "nonoperating income" in text or "other income expense" in text:
        return "nonoperating_income"
    if "pretax" in text or "before tax" in text or ("income" in text and "before" in text and "tax" in text):
        return "pretax_income"
    if "income tax" in text or "tax expense" in text or "provision for income tax" in text:
        return "income_tax"
    if "net income" in text or "profit loss" in text or "net earnings" in text:
        return "net_income"
    
    # Cash Flow
    if "net cash" in text and "operating activities" in text:
        return "cfo"
    if "net cash" in text and "investing activities" in text:
        return "cfi"
    if "net cash" in text and "financing activities" in text:
        return "cff"
    if "property" in text and any(k in text for k in ("capital expenditures", "acquire", "purchases")):
        return "capex"
    if "stock based compensation" in text or "share based compensation" in text:
        return "stock_based_compensation"
    if "working capital" in text and "change" in text:
        return "working_capital_changes"
    if "dividends paid" in text or "payment of dividend" in text:
        return "dividends_paid"
    if "proceeds" in text and "debt" in text and ("issuance" in text or "issue" in text):
        return "debt_issued"
    if ("repayment" in text and "debt" in text) or ("debt" in text and "repay" in text):
        return "debt_repaid"
    if ("repurchase" in text and ("stock" in text or "share" in text)) or "treasury stock" in text:
        return "share_repurchases"
    
    # Balance Sheet
    if "total assets" in text or ("assets" in text and "total" in text):
        return "total_assets"
    if "current assets" in text:
        return "current_assets"
    if "cash" in text and "equivalent" in text:
        return "cash_and_equivalents"
    if "accounts receivable" in text or ("receivable" in text and "current" in text):
        return "accounts_receivable"
    if "inventory" in text:
        return "inventory"
    if "property" in text and "plant" in text and "equipment" in text:
        return "ppe_net"
    if "goodwill" in text:
        return "goodwill"
    if "intangible assets" in text:
        return "intangible_assets"
    if "total liabilities" in text or ("liabilities" in text and "total" in text):
        return "total_liabilities"
    if "current liabilities" in text:
        return "current_liabilities"
    if "accounts payable" in text:
        return "accounts_payable"
    if "long term debt" in text or "long-term debt" in text:
        return "long_term_debt"
    if ("shareholders equity" in text or "stockholders equity" in text) or ("equity" in text and "total" in text):
        return "shareholders_equity"
    
    # Share Data
    if "shares outstanding" in text and "basic" in text:
        return "shares_basic"
    if "weighted average" in text and "shares" in text and "basic" in text:
        return "shares_basic"
    if "shares outstanding" in text and "diluted" in text:
        return "shares_diluted"
    if "weighted average" in text and "shares" in text and "diluted" in text:
        return "shares_diluted"
    if "earnings per share" in text and "basic" in text:
        return "eps_basic"
    if "earnings per share" in text and "diluted" in text:
        return "eps_diluted"
    if "shares outstanding" in text and "basic" not in text and "diluted" not in text:
        return "shares_outstanding"
    if "common stock" in text and "shares" in text and "outstanding" in text:
        return "shares_outstanding"
    
    return None





