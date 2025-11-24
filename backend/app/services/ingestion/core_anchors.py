"""
core_anchors.py — Deterministic extraction of high-confidence XBRL anchor tags.

Extracts core financial statement anchors using deterministic rules (exact tag matches,
keyword heuristics, statement placement) without LLM dependency.

These anchors are used to compute derived DCF variables.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Set

from app.core.logging import get_logger
from app.core.model_role_map import (
    BS_ACCOUNTS_PAYABLE,
    BS_ACCOUNTS_RECEIVABLE,
    BS_AP_AND_ACCRUED,
    BS_DEBT_CURRENT,
    BS_DEBT_NONCURRENT,
    BS_INVENTORY,
    BS_PP_AND_E,
    CF_DEPRECIATION,
    CF_DIVIDENDS_PAID,
    CF_SHARE_REPURCHASES,
    IS_COGS,
    IS_D_AND_A,
    IS_OPERATING_INCOME,
    IS_REVENUE,
    IS_TAX_EXPENSE,
)

logger = get_logger(__name__)


class AnchorFact:
    """Represents a deterministically extracted anchor fact."""
    
    def __init__(
        self,
        tag: str,
        label: str,
        model_role: str,
        periods: Dict[str, float],
        unit: str,
        source_reason: str,
    ):
        self.tag = tag
        self.label = label
        self.model_role = model_role
        self.periods = periods
        self.unit = unit
        self.source_reason = source_reason
        self.confidence = "deterministic"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "tag": self.tag,
            "label": self.label,
            "model_role": self.model_role,
            "periods": self.periods,
            "unit": self.unit,
            "source_reason": self.source_reason,
            "confidence": self.confidence,
        }


def get_latest_period_value(periods: Dict[str, Any]) -> Optional[float]:
    """Extract the most recent period value."""
    if not periods:
        return None
    sorted_dates = sorted(periods.keys(), reverse=True)
    if not sorted_dates:
        return None
    latest_date = sorted_dates[0]
    value = periods[latest_date]
    if isinstance(value, (int, float)):
        return float(value)
    elif isinstance(value, dict):
        return float(value.get("value", 0))
    return None


def find_tag_by_exact_match(
    line_items: List[Dict[str, Any]],
    exact_tags: List[str],
    model_role: str,
) -> Optional[AnchorFact]:
    """Find tag by exact match against known US-GAAP tag names."""
    for item in line_items:
        tag = item.get("tag", "")
        if tag in exact_tags:
            label = item.get("label", tag)
            periods = item.get("periods", {})
            unit = item.get("unit", "USD")
            
            # Verify we have at least one period value
            if get_latest_period_value(periods) is not None:
                return AnchorFact(
                    tag=tag,
                    label=label,
                    model_role=model_role,
                    periods=periods,
                    unit=unit,
                    source_reason=f"Exact tag match: {tag}",
                )
    return None


def find_tag_by_keywords(
    line_items: List[Dict[str, Any]],
    keywords: List[str],
    model_role: str,
    exclude_keywords: Optional[List[str]] = None,
) -> Optional[AnchorFact]:
    """Find tag by keyword matching in tag name or label."""
    exclude_keywords = exclude_keywords or []
    
    candidates = []
    for item in line_items:
        tag = item.get("tag", "").lower()
        label = item.get("label", "").lower()
        
        # Check for exclude keywords first
        if any(excl.lower() in tag or excl.lower() in label for excl in exclude_keywords):
            continue
        
        # Check for include keywords
        matches = sum(1 for kw in keywords if kw.lower() in tag or kw.lower() in label)
        if matches > 0:
            periods = item.get("periods", {})
            if get_latest_period_value(periods) is not None:
                candidates.append((item, matches))
    
    if not candidates:
        return None
    
    # Sort by number of keyword matches (descending)
    candidates.sort(key=lambda x: x[1], reverse=True)
    best_item = candidates[0][0]
    
    return AnchorFact(
        tag=best_item.get("tag", ""),
        label=best_item.get("label", ""),
        model_role=model_role,
        periods=best_item.get("periods", {}),
        unit=best_item.get("unit", "USD"),
        source_reason=f"Keyword match: {', '.join(keywords)}",
    )


def extract_revenue_anchor(
    income_statement_items: List[Dict[str, Any]],
) -> Optional[AnchorFact]:
    """Extract Revenue anchor (IS_REVENUE)."""
    # Exact tag matches (common US-GAAP revenue tags)
    exact_tags = [
        "Revenues",
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
        "SalesRevenueNet",
        "SalesRevenueGoodsNet",
    ]
    
    anchor = find_tag_by_exact_match(income_statement_items, exact_tags, IS_REVENUE)
    if anchor:
        return anchor
    
    # Keyword fallback
    keywords = ["revenue", "revenues", "sales", "net sales"]
    exclude = ["cost", "expense", "income", "margin", "ratio"]
    return find_tag_by_keywords(income_statement_items, keywords, IS_REVENUE, exclude)


def extract_cogs_anchor(
    income_statement_items: List[Dict[str, Any]],
) -> Optional[AnchorFact]:
    """Extract COGS anchor (IS_COGS)."""
    exact_tags = [
        "CostOfGoodsAndServicesSold",
        "CostOfRevenue",
        "CostOfSales",
        "CostOfProductsSold",
    ]
    
    anchor = find_tag_by_exact_match(income_statement_items, exact_tags, IS_COGS)
    if anchor:
        return anchor
    
    keywords = ["cost of goods", "cost of revenue", "cost of sales", "cogs"]
    exclude = ["operating", "total", "other"]
    return find_tag_by_keywords(income_statement_items, keywords, IS_COGS, exclude)


def extract_operating_income_anchor(
    income_statement_items: List[Dict[str, Any]],
) -> Optional[AnchorFact]:
    """Extract Operating Income anchor (IS_OPERATING_INCOME)."""
    exact_tags = [
        "OperatingIncomeLoss",
        "OperatingIncome",
        "IncomeFromOperations",
    ]
    
    anchor = find_tag_by_exact_match(income_statement_items, exact_tags, IS_OPERATING_INCOME)
    if anchor:
        return anchor
    
    keywords = ["operating income", "income from operations", "operating profit"]
    exclude = ["non-operating", "before", "after"]
    return find_tag_by_keywords(income_statement_items, keywords, IS_OPERATING_INCOME, exclude)


def extract_depreciation_anchor(
    income_statement_items: List[Dict[str, Any]],
    cash_flow_items: List[Dict[str, Any]],
) -> Optional[AnchorFact]:
    """Extract Depreciation & Amortization anchor (IS_D_AND_A or CF_DEPRECIATION)."""
    # Try income statement first
    exact_tags = [
        "DepreciationAndAmortization",
        "DepreciationAmortizationAndAccretion",
    ]
    
    anchor = find_tag_by_exact_match(income_statement_items, exact_tags, IS_D_AND_A)
    if anchor:
        return anchor
    
    # Try cash flow statement
    anchor = find_tag_by_exact_match(cash_flow_items, exact_tags, CF_DEPRECIATION)
    if anchor:
        # Convert to IS_D_AND_A role for consistency
        anchor.model_role = IS_D_AND_A
        anchor.source_reason += " (from cash flow statement)"
        return anchor
    
    # Keyword fallback
    keywords = ["depreciation", "amortization", "depreciation and amortization"]
    exclude = ["accumulated", "net"]
    
    anchor = find_tag_by_keywords(income_statement_items, keywords, IS_D_AND_A, exclude)
    if anchor:
        return anchor
    
    return find_tag_by_keywords(cash_flow_items, keywords, CF_DEPRECIATION, exclude)


def extract_tax_expense_anchor(
    income_statement_items: List[Dict[str, Any]],
) -> Optional[AnchorFact]:
    """Extract Tax Expense anchor (IS_TAX_EXPENSE)."""
    exact_tags = [
        "IncomeTaxExpenseBenefit",
        "CurrentIncomeTaxExpenseBenefit",
        "IncomeTaxExpense",
    ]
    
    anchor = find_tag_by_exact_match(income_statement_items, exact_tags, IS_TAX_EXPENSE)
    if anchor:
        return anchor
    
    keywords = ["income tax expense", "tax expense", "current income tax"]
    exclude = ["rate", "provision", "deferred", "benefit only"]
    return find_tag_by_keywords(income_statement_items, keywords, IS_TAX_EXPENSE, exclude)


def extract_debt_anchors(
    balance_sheet_items: List[Dict[str, Any]],
) -> Tuple[Optional[AnchorFact], Optional[AnchorFact]]:
    """
    Extract Debt Current and Noncurrent anchors deterministically.
    
    Priority:
    1. Exact tag matches (Ford-specific tags included)
    2. Keyword matching (interest-bearing debt only)
    
    Excludes:
    - Operating liabilities (AP, Accrued, etc.)
    - Lease liabilities (unless explicitly finance lease debt)
    - Pension/postretirement liabilities
    - Derivatives
    - Cash flow activity (proceeds/repayments)
    """
    # Current debt - exact tags (Ford-specific included)
    current_exact = [
        "DebtCurrent",
        "ShortTermBorrowings",
        "ShortTermDebt",
        "LongTermDebtCurrent",
        "LongTermDebtAndFinanceLeaseObligationsCurrent",
        "LongTermDebtAndCapitalLeaseObligationsCurrent",
        "CurrentPortionOfLongTermDebt",
        "NotesPayableCurrent",
        "UnsecuredDebtCurrent",  # Ford-specific
        "SecuredDebtCurrent",
    ]
    
    current_anchor = find_tag_by_exact_match(balance_sheet_items, current_exact, BS_DEBT_CURRENT)
    if not current_anchor:
        # Keyword fallback - interest-bearing debt only
        current_keywords = [
            "short-term debt",
            "current portion of long-term debt",
            "current debt",
            "notes payable, current",
            "borrowings, current",
            "unsecured debt, current",
        ]
        current_exclude = [
            "accounts payable",
            "accrued",
            "operating lease",
            "pension",
            "postretirement",
            "derivative",
            "proceeds",
            "repayment",
        ]
        current_anchor = find_tag_by_keywords(
            balance_sheet_items, current_keywords, BS_DEBT_CURRENT, current_exclude
        )
    
    # Noncurrent debt - exact tags (Ford-specific included)
    noncurrent_exact = [
        "DebtNoncurrent",
        "LongTermDebtNoncurrent",
        "LongTermDebt",
        "LongTermDebtAndFinanceLeaseObligationsNoncurrent",
        "LongTermDebtAndCapitalLeaseObligationsNoncurrent",
        "NotesPayableNoncurrent",
        "UnsecuredLongTermDebt",  # Ford-specific
        "SecuredLongTermDebt",
    ]
    
    noncurrent_anchor = find_tag_by_exact_match(balance_sheet_items, noncurrent_exact, BS_DEBT_NONCURRENT)
    if not noncurrent_anchor:
        # Keyword fallback - interest-bearing debt only
        noncurrent_keywords = [
            "long-term debt",
            "debt, noncurrent",
            "notes payable, noncurrent",
            "borrowings, noncurrent",
            "unsecured long-term debt",
        ]
        noncurrent_exclude = [
            "accounts payable",
            "accrued",
            "operating lease",
            "pension",
            "postretirement",
            "derivative",
            "proceeds",
            "repayment",
        ]
        noncurrent_anchor = find_tag_by_keywords(
            balance_sheet_items, noncurrent_keywords, BS_DEBT_NONCURRENT, noncurrent_exclude
        )
    
    return current_anchor, noncurrent_anchor


def extract_accounts_payable_anchor(
    balance_sheet_items: List[Dict[str, Any]],
) -> Optional[AnchorFact]:
    """
    Extract Accounts Payable anchor deterministically.
    
    Priority:
    1. Direct AP tags (AccountsPayableCurrent, AccountsPayable, TradeAccountsPayableCurrent)
    2. Combined AP+Accrued tag as proxy (AccountsPayableAndAccruedLiabilitiesCurrent)
    
    Excludes:
    - Broad liability rollups (LiabilitiesCurrent, Liabilities, TotalLiabilities)
    - Other current liabilities (AccruedLiabilitiesCurrent, etc.)
    """
    # Prefer separate AP tags
    exact_tags = [
        "AccountsPayableCurrent",
        "AccountsPayable",
        "AccountsPayableTrade",
        "TradeAccountsPayableCurrent",
    ]
    
    anchor = find_tag_by_exact_match(balance_sheet_items, exact_tags, BS_ACCOUNTS_PAYABLE)
    if anchor:
        return anchor
    
    # Keyword fallback - but exclude broad rollups
    keywords = ["accounts payable", "trade payables"]
    exclude = [
        "accrued",
        "other",
        "liabilitiescurrent",  # Block broad rollups
        "liabilities",  # Block broad rollups
        "total liabilities",  # Block broad rollups
    ]
    return find_tag_by_keywords(balance_sheet_items, keywords, BS_ACCOUNTS_PAYABLE, exclude)


def extract_ap_and_accrued_anchor(
    balance_sheet_items: List[Dict[str, Any]],
) -> Optional[AnchorFact]:
    """Extract combined AP+Accrued anchor (BS_AP_AND_ACCRUED)."""
    exact_tags = [
        "AccountsPayableAndAccruedLiabilitiesCurrent",
        "AccountsPayableAndAccruedLiabilities",
    ]
    
    anchor = find_tag_by_exact_match(balance_sheet_items, exact_tags, BS_AP_AND_ACCRUED)
    if anchor:
        return anchor
    
    keywords = ["accounts payable and accrued", "payables and accrued liabilities"]
    return find_tag_by_keywords(balance_sheet_items, keywords, BS_AP_AND_ACCRUED)


def extract_inventory_anchor(
    balance_sheet_items: List[Dict[str, Any]],
) -> Optional[AnchorFact]:
    """Extract Inventory anchor (BS_INVENTORY)."""
    exact_tags = [
        "InventoryNet",
        "Inventory",
        "InventoryFinishedGoods",
    ]
    
    anchor = find_tag_by_exact_match(balance_sheet_items, exact_tags, BS_INVENTORY)
    if anchor:
        return anchor
    
    keywords = ["inventory"]
    exclude = ["deferred", "prepaid"]
    return find_tag_by_keywords(balance_sheet_items, keywords, BS_INVENTORY, exclude)


def extract_ppe_anchor(
    balance_sheet_items: List[Dict[str, Any]],
) -> Optional[AnchorFact]:
    """Extract PP&E anchor (BS_PP_AND_E)."""
    exact_tags = [
        "PropertyPlantAndEquipmentNet",
        "PropertyPlantAndEquipment",
    ]
    
    anchor = find_tag_by_exact_match(balance_sheet_items, exact_tags, BS_PP_AND_E)
    if anchor:
        return anchor
    
    keywords = ["property plant and equipment", "ppe", "fixed assets"]
    exclude = ["accumulated", "gross"]
    return find_tag_by_keywords(balance_sheet_items, keywords, BS_PP_AND_E, exclude)


def extract_accounts_receivable_anchor(
    balance_sheet_items: List[Dict[str, Any]],
) -> Optional[AnchorFact]:
    """Extract Accounts Receivable anchor (BS_ACCOUNTS_RECEIVABLE)."""
    exact_tags = [
        "AccountsReceivableNetCurrent",
        "AccountsReceivableNet",
        "AccountsReceivableCurrent",
        "AccountsReceivable",
    ]
    
    anchor = find_tag_by_exact_match(balance_sheet_items, exact_tags, BS_ACCOUNTS_RECEIVABLE)
    if anchor:
        return anchor
    
    keywords = ["accounts receivable", "trade receivables"]
    exclude = ["allowance", "other"]
    return find_tag_by_keywords(balance_sheet_items, keywords, BS_ACCOUNTS_RECEIVABLE, exclude)


def extract_share_repurchases_anchor(
    cash_flow_items: List[Dict[str, Any]],
) -> Optional[AnchorFact]:
    """Extract Share Repurchases anchor (CF_SHARE_REPURCHASES)."""
    exact_tags = [
        "PaymentsForRepurchaseOfCommonStock",
        "PaymentsForRepurchaseOfEquity",
    ]
    
    anchor = find_tag_by_exact_match(cash_flow_items, exact_tags, CF_SHARE_REPURCHASES)
    if anchor:
        return anchor
    
    keywords = ["repurchase", "buyback", "treasury stock"]
    exclude = ["issuance", "proceeds"]
    return find_tag_by_keywords(cash_flow_items, keywords, CF_SHARE_REPURCHASES, exclude)


def extract_dividends_anchor(
    cash_flow_items: List[Dict[str, Any]],
) -> Optional[AnchorFact]:
    """Extract Dividends Paid anchor (CF_DIVIDENDS_PAID)."""
    exact_tags = [
        "PaymentsOfDividendsCommonStock",
        "PaymentsOfDividends",
        "DividendsPaid",
    ]
    
    anchor = find_tag_by_exact_match(cash_flow_items, exact_tags, CF_DIVIDENDS_PAID)
    if anchor:
        return anchor
    
    keywords = ["dividends paid", "dividend payments"]
    exclude = ["declared", "per share"]
    return find_tag_by_keywords(cash_flow_items, keywords, CF_DIVIDENDS_PAID, exclude)


def extract_core_anchors(edgar_json: Dict[str, Any]) -> Dict[str, Optional[AnchorFact]]:
    """
    Extract all core anchors deterministically from structured EDGAR JSON.
    
    Args:
        edgar_json: Structured EDGAR JSON with statements and line_items
        
    Returns:
        Dictionary mapping model_role -> AnchorFact (or None if not found)
    """
    statements = edgar_json.get("statements", {})
    
    income_statement = statements.get("income_statement", {})
    income_items = income_statement.get("line_items", [])
    
    balance_sheet = statements.get("balance_sheet", {})
    balance_items = balance_sheet.get("line_items", [])
    
    cash_flow = statements.get("cash_flow_statement", {})
    cash_flow_items = cash_flow.get("line_items", [])
    
    anchors = {}
    
    # Income Statement anchors
    anchors[IS_REVENUE] = extract_revenue_anchor(income_items)
    anchors[IS_COGS] = extract_cogs_anchor(income_items)
    anchors[IS_OPERATING_INCOME] = extract_operating_income_anchor(income_items)
    anchors[IS_D_AND_A] = extract_depreciation_anchor(income_items, cash_flow_items)
    anchors[IS_TAX_EXPENSE] = extract_tax_expense_anchor(income_items)
    
    # Balance Sheet anchors
    anchors[BS_INVENTORY] = extract_inventory_anchor(balance_items)
    anchors[BS_PP_AND_E] = extract_ppe_anchor(balance_items)
    anchors[BS_ACCOUNTS_RECEIVABLE] = extract_accounts_receivable_anchor(balance_items)
    anchors[BS_ACCOUNTS_PAYABLE] = extract_accounts_payable_anchor(balance_items)
    anchors[BS_AP_AND_ACCRUED] = extract_ap_and_accrued_anchor(balance_items)
    
    debt_current, debt_noncurrent = extract_debt_anchors(balance_items)
    anchors[BS_DEBT_CURRENT] = debt_current
    anchors[BS_DEBT_NONCURRENT] = debt_noncurrent
    
    # Log debt anchor extraction for debugging
    if debt_current:
        logger.info(f"Extracted debt current anchor: {debt_current.tag} ({debt_current.label})")
    if debt_noncurrent:
        logger.info(f"Extracted debt noncurrent anchor: {debt_noncurrent.tag} ({debt_noncurrent.label})")
    if not debt_current and not debt_noncurrent:
        logger.warning("No debt anchors extracted - checking available debt tags...")
        debt_tags = [
            item.get("tag") for item in balance_items
            if any(kw in (item.get("tag") or "").lower() or (item.get("label") or "").lower()
                   for kw in ["debt", "borrow", "notes payable", "unsecured", "secured"])
        ]
        if debt_tags:
            logger.warning(f"Found debt-related tags but none matched anchor criteria: {debt_tags[:10]}")
    
    # Cash Flow anchors
    anchors[CF_SHARE_REPURCHASES] = extract_share_repurchases_anchor(cash_flow_items)
    anchors[CF_DIVIDENDS_PAID] = extract_dividends_anchor(cash_flow_items)
    
    return anchors


def _kw_hit(li: Dict[str, Any], kws: Tuple[str, ...]) -> bool:
    """Check if line item tag or label matches any keyword."""
    tag = (li.get("tag") or "").lower()
    label = (li.get("label") or "").lower()
    return any(k in tag for k in kws) or any(k in label for k in kws)


def _set_role(li: Dict[str, Any], role: str, reason: str):
    """Set model_role and classification metadata on a line item."""
    li["model_role"] = role
    li.setdefault("classification_meta", {})
    li["classification_meta"].update({
        "source": "deterministic",
        "reason": reason,
        "confidence": 1.0
    })


def anchor_balance_sheet_debt(items: List[Dict[str, Any]]):
    """
    Deterministically anchor balance sheet debt tags BEFORE LLM classification.
    
    This function directly tags debt items in the balance sheet line items,
    setting model_role to BS_DEBT_CURRENT or BS_DEBT_NONCURRENT.
    
    Args:
        items: List of balance sheet line items (modified in place)
    """
    CURRENT: Set[str] = {
        "longtermdebtcurrent",
        "debtcurrent",
        "shorttermborrowings",
        "shorttermdebt",
        "notespayablecurrent",
        "longtermdebtandfinanceleaseobligationscurrent",
        "longtermdebtandcapitalleaseobligationscurrent",
        "unsecureddebtcurrent",
        "secureddebtcurrent",
    }
    
    NONCURRENT: Set[str] = {
        "longtermdebtnoncurrent",
        "debtnoncurrent",
        "longtermdebtandfinanceleaseobligationsnoncurrent",
        "longtermdebtandcapitalleaseobligationsnoncurrent",
        "notespayablenoncurrent",
        "unsecuredlongtermdebt",
        "securedlongtermdebt",
    }
    
    COMBINED: Set[str] = {
        "longtermdebtandfinanceleaseobligations",
        "longtermdebtandcapitalleaseobligations",
        "longtermdebt",
        "totaldebt",
        "debt",
    }
    
    EXCLUDE = (
        "liabilitiescurrent",
        "operating lease",
        "accrued",
        "deferred",
        "pension",
        "accounts payable",
    )
    
    for li in items:
        tag = (li.get("tag") or "").lower()
        label = (li.get("label") or "").lower()
        
        # Skip if already has a model_role (don't override)
        if li.get("model_role"):
            continue
        
        # Exclude non-debt liabilities
        if _kw_hit(li, EXCLUDE):
            continue
        
        # Check current debt tags
        if tag in CURRENT:
            _set_role(li, BS_DEBT_CURRENT, f"Matched current debt tag: {li.get('tag')}")
            logger.debug(f"Anchored {li.get('tag')} as BS_DEBT_CURRENT")
            continue
        
        # Check noncurrent debt tags
        if tag in NONCURRENT:
            _set_role(li, BS_DEBT_NONCURRENT, f"Matched noncurrent debt tag: {li.get('tag')}")
            logger.debug(f"Anchored {li.get('tag')} as BS_DEBT_NONCURRENT")
            continue
        
        # Check combined debt tags (map to noncurrent for fallback computation)
        if tag in COMBINED:
            _set_role(li, BS_DEBT_NONCURRENT, f"Matched combined debt tag: {li.get('tag')}")
            logger.debug(f"Anchored {li.get('tag')} as BS_DEBT_NONCURRENT (combined)")
            continue

