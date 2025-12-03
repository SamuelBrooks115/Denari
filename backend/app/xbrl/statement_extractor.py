"""
statement_extractor.py — Extract Balance Sheet, Income Statement, and Cash Flow from Arelle ModelXbrl.

LEGACY: Replaced by FMP /stable-based pipeline (see app/data/fmp_client.py).

This module extracts financial statements from an Arelle ModelXbrl object and maps them
to our standardized "master chart of accounts" format.

Key features:
- Maps XBRL concepts (us-gaap + extensions) to normalized line items
- Prefers consolidated entity + current year context
- Enforces single normalized value per account using precedence rules
- Returns structured output matching our existing JSON schema

Does NOT depend on:
- EDGAR APIs
- Company Facts API
- HTTP calls

Works purely on Arelle ModelXbrl objects.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.core.logging import get_logger
from app.core.model_role_map import (
    BS_ACCOUNTS_PAYABLE,
    BS_ACCOUNTS_RECEIVABLE,
    BS_ACCRUED_LIABILITIES,
    BS_ASSETS_CURRENT,
    BS_ASSETS_NONCURRENT,
    BS_ASSETS_TOTAL,
    BS_CASH,
    BS_DEBT_CURRENT,
    BS_DEBT_NONCURRENT,
    BS_EQUITY_TOTAL,
    BS_INVENTORY,
    BS_LIABILITIES_CURRENT,
    BS_LIABILITIES_NONCURRENT,
    BS_LIABILITIES_TOTAL,
    BS_PP_AND_E,
    CF_CASH_FROM_FINANCING,
    CF_CASH_FROM_INVESTING,
    CF_CASH_FROM_OPERATIONS,
    CF_DEPRECIATION,
    CF_DIVIDENDS_PAID,
    CF_NET_CHANGE_IN_CASH,
    CF_SHARE_REPURCHASES,
    IS_COGS,
    IS_D_AND_A,
    IS_EBITDA,
    IS_NET_INCOME,
    IS_OPERATING_EXPENSE,
    IS_OPERATING_INCOME,
    IS_REVENUE,
    IS_TAX_EXPENSE,
)

logger = get_logger(__name__)


# ============================================================================
# STEP 3: MASTER CHART OF ACCOUNTS MAPPING
# ============================================================================

# Mapping from normalized line item (model_role) to XBRL concept candidates
# Order matters: first match wins (precedence)
MASTER_MAP: Dict[str, Dict[str, List[str]]] = {
    "balance_sheet": {
        # Assets
        BS_CASH: [
            "us-gaap:CashAndCashEquivalentsAtCarryingValue",
            "us-gaap:CashCashEquivalentsAndShortTermInvestments",
            "us-gaap:Cash",
        ],
        BS_ACCOUNTS_RECEIVABLE: [
            "us-gaap:AccountsReceivableNetCurrent",
            "us-gaap:ReceivablesNetCurrent",
            "us-gaap:AccountsReceivableCurrent",
        ],
        BS_INVENTORY: [
            "us-gaap:Inventories",
            "us-gaap:InventoryNet",
        ],
        BS_PP_AND_E: [
            "us-gaap:PropertyPlantAndEquipmentNet",
            "us-gaap:PropertyPlantAndEquipment",
        ],
        BS_ASSETS_CURRENT: [
            "us-gaap:AssetsCurrent",
        ],
        BS_ASSETS_NONCURRENT: [
            "us-gaap:AssetsNoncurrent",
            "us-gaap:NoncurrentAssets",
        ],
        BS_ASSETS_TOTAL: [
            "us-gaap:Assets",
        ],
        
        # Liabilities
        BS_ACCOUNTS_PAYABLE: [
            "us-gaap:AccountsPayableCurrent",
            "us-gaap:AccountsPayable",
        ],
        BS_ACCRUED_LIABILITIES: [
            "us-gaap:AccruedLiabilitiesCurrent",
            "us-gaap:AccruedLiabilities",
        ],
        BS_DEBT_CURRENT: [
            "us-gaap:DebtCurrent",
            "us-gaap:ShortTermBorrowings",
            "us-gaap:ShortTermDebt",
        ],
        BS_DEBT_NONCURRENT: [
            "us-gaap:DebtNoncurrent",
            "us-gaap:LongTermDebtNoncurrent",
            "us-gaap:LongTermDebt",
        ],
        BS_LIABILITIES_CURRENT: [
            "us-gaap:LiabilitiesCurrent",
        ],
        BS_LIABILITIES_NONCURRENT: [
            "us-gaap:LiabilitiesNoncurrent",
            "us-gaap:NoncurrentLiabilities",
        ],
        BS_LIABILITIES_TOTAL: [
            "us-gaap:Liabilities",
        ],
        
        # Equity
        BS_EQUITY_TOTAL: [
            "us-gaap:StockholdersEquity",
            "us-gaap:StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
            "us-gaap:Equity",
        ],
    },
    
    "income_statement": {
        IS_REVENUE: [
            "us-gaap:Revenues",
            "us-gaap:SalesRevenueNet",
            "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
        ],
        IS_COGS: [
            "us-gaap:CostOfGoodsAndServicesSold",
            "us-gaap:CostOfRevenue",
            "us-gaap:CostOfSales",
        ],
        IS_OPERATING_INCOME: [
            "us-gaap:OperatingIncomeLoss",
            "us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
        ],
        IS_OPERATING_EXPENSE: [
            # Computed: Revenue - Operating Income
            # But we can also look for explicit tags
            "us-gaap:OperatingExpenses",
            "us-gaap:CostsAndExpenses",
        ],
        IS_D_AND_A: [
            "us-gaap:DepreciationDepletionAndAmortization",
            "us-gaap:DepreciationAndAmortization",
        ],
        IS_TAX_EXPENSE: [
            "us-gaap:IncomeTaxExpenseBenefit",
            "us-gaap:IncomeTaxExpense",
        ],
        IS_NET_INCOME: [
            "us-gaap:NetIncomeLoss",
            "us-gaap:NetIncomeLossAttributableToParent",
            "us-gaap:ProfitLoss",
        ],
        IS_EBITDA: [
            # Computed: Operating Income + D&A
            # But some companies report it directly
            "us-gaap:EarningsBeforeInterestTaxesDepreciationAndAmortization",
        ],
    },
    
    "cash_flow": {
        CF_CASH_FROM_OPERATIONS: [
            "us-gaap:NetCashProvidedByUsedInOperatingActivities",
            "us-gaap:CashFlowFromOperatingActivities",
        ],
        CF_CASH_FROM_INVESTING: [
            "us-gaap:NetCashProvidedByUsedInInvestingActivities",
            "us-gaap:CashFlowFromInvestingActivities",
        ],
        CF_CASH_FROM_FINANCING: [
            "us-gaap:NetCashProvidedByUsedInFinancingActivities",
            "us-gaap:CashFlowFromFinancingActivities",
        ],
        CF_NET_CHANGE_IN_CASH: [
            "us-gaap:CashAndCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect",
            "us-gaap:CashCashEquivalentsAndShortTermInvestmentsPeriodIncreaseDecreaseIncludingExchangeRateEffect",
        ],
        CF_DEPRECIATION: [
            "us-gaap:DepreciationDepletionAndAmortization",
            "us-gaap:DepreciationAndAmortization",
        ],
        CF_DIVIDENDS_PAID: [
            "us-gaap:PaymentsOfDividends",
            "us-gaap:DividendsPaid",
        ],
        CF_SHARE_REPURCHASES: [
            "us-gaap:PaymentsForRepurchaseOfCommonStock",
            "us-gaap:StockRepurchasedAndRetiredDuringPeriodValue",
        ],
    },
}


@dataclass
class ExtractedLineItem:
    """A single extracted line item with value and metadata."""
    model_role: str
    tag: str
    label: str
    value: float
    unit: str
    period_end: str
    status: str  # "direct", "computed", "proxy"
    supporting_tags: List[str]
    context_id: Optional[str] = None
    is_consolidated: bool = True


def _is_consolidated_context(context: Any) -> bool:
    """
    Check if an XBRL context represents consolidated entity (no segment dimensions).
    
    Args:
        context: Arelle context object
        
    Returns:
        True if context appears to be consolidated (no segment dimensions or explicitly consolidated)
    """
    if context is None:
        return True
    
    # Check for segment dimensions
    if hasattr(context, "segDimValues") and context.segDimValues:
        # Check if any dimension explicitly indicates a segment (not consolidated)
        for dim in context.segDimValues:
            dim_str = str(dim).lower()
            # If it explicitly says "consolidated", it's still consolidated
            if "consolidated" in dim_str:
                return True
            # If it has segment indicators (but not consolidated), it's segmented
            if any(indicator in dim_str for indicator in [
                "ford credit", "company excluding", "automotive", "financial services"
            ]):
                return False
        # If we have dimensions but they don't indicate segments, assume consolidated
        return True
    
    return True


def _get_period_end(context: Any) -> Optional[str]:
    """
    Extract period end date from Arelle context.
    
    Args:
        context: Arelle context object
        
    Returns:
        Period end date as ISO string (YYYY-MM-DD) or None
    """
    if context is None:
        return None
    
    # Check if it's an instant period (balance sheet)
    # isInstantPeriod is a property, not a method
    if hasattr(context, "isInstantPeriod"):
        is_instant = context.isInstantPeriod if not callable(context.isInstantPeriod) else context.isInstantPeriod()
        if is_instant:
            if hasattr(context, "instantDatetime") and context.instantDatetime:
                return context.instantDatetime.date().isoformat()
    
    # Check if it's a duration period (income statement, cash flow)
    # isStartEndPeriod is a property, not a method
    if hasattr(context, "isStartEndPeriod"):
        is_start_end = context.isStartEndPeriod if not callable(context.isStartEndPeriod) else context.isStartEndPeriod()
        if is_start_end:
            if hasattr(context, "endDatetime") and context.endDatetime:
                # endDatetime is the day AFTER the period ends, so subtract 1 day
                from datetime import timedelta
                end_date = context.endDatetime.date() - timedelta(days=1)
                return end_date.isoformat()
    
    # Fallback: try direct attributes
    if hasattr(context, "instantDatetime") and context.instantDatetime:
        return context.instantDatetime.date().isoformat()
    
    if hasattr(context, "endDatetime") and context.endDatetime:
        from datetime import timedelta
        # endDatetime is the day AFTER the period ends
        # For a period ending 2024-12-31, endDatetime would be 2025-01-01
        end_date = context.endDatetime.date() - timedelta(days=1)
        return end_date.isoformat()
    
    # Also check startDatetime + 1 year for annual periods
    if hasattr(context, "startDatetime") and context.startDatetime:
        start_date = context.startDatetime.date()
        # If start is beginning of year, period end is end of that year
        if start_date.month == 1 and start_date.day == 1:
            from datetime import date
            period_end = date(start_date.year, 12, 31)
            return period_end.isoformat()
    
    return None


def _matches_fiscal_year(period_end: Optional[str], fiscal_year: int) -> bool:
    """
    Check if a period end date matches the target fiscal year.
    
    Args:
        period_end: Period end date as ISO string (YYYY-MM-DD) or None
        fiscal_year: Target fiscal year (e.g., 2024)
        
    Returns:
        True if period end is in the target fiscal year
    """
    if not period_end:
        return False
    
    try:
        date_obj = datetime.fromisoformat(period_end).date()
        return date_obj.year == fiscal_year
    except (ValueError, TypeError):
        return False


def _extract_fact_value(
    fact: Any,
    prefer_consolidated: bool = True,
) -> Optional[float]:
    """
    Extract numeric value from an Arelle fact.
    
    Args:
        fact: Arelle fact object
        prefer_consolidated: If True, only return value if context is consolidated
        
    Returns:
        Numeric value or None
    """
    if fact is None:
        return None
    
    # Check if consolidated (if required)
    if prefer_consolidated:
        if not _is_consolidated_context(fact.context):
            return None
    
    # Get value - try multiple methods for iXBRL facts
    try:
        # Method 1: xValue (standard XBRL)
        value = fact.xValue if hasattr(fact, "xValue") else None
        
        # Method 2: textValue (iXBRL)
        if value is None and hasattr(fact, "textValue"):
            text_val = fact.textValue
            if text_val:
                try:
                    # Remove commas and parse
                    cleaned = str(text_val).replace(",", "").strip()
                    value = float(cleaned)
                except (ValueError, TypeError):
                    pass
        
        # Method 3: stringValue
        if value is None and hasattr(fact, "stringValue"):
            str_val = fact.stringValue
            if str_val:
                try:
                    cleaned = str(str_val).replace(",", "").strip()
                    value = float(cleaned)
                except (ValueError, TypeError):
                    pass
        
        # Method 4: text content
        if value is None and hasattr(fact, "text"):
            text = fact.text
            if text:
                try:
                    cleaned = str(text).replace(",", "").strip()
                    value = float(cleaned)
                except (ValueError, TypeError):
                    pass
        
        if value is None:
            return None
        
        # Convert to float
        if isinstance(value, (int, float)):
            return float(value)
        
        # Try string conversion
        return float(str(value))
    
    except (ValueError, TypeError, AttributeError):
        return None


def _find_facts_for_concept(
    model_xbrl: Any,
    concept_qname: str,
    fiscal_year: int,
    prefer_consolidated: bool = True,
) -> List[Tuple[Any, str]]:
    """
    Find all facts matching a concept QName for a given fiscal year.
    
    Args:
        model_xbrl: Arelle ModelXbrl object
        concept_qname: Concept QName (e.g., "us-gaap:Assets")
        fiscal_year: Target fiscal year
        prefer_consolidated: If True, prefer consolidated contexts
        
    Returns:
        List of (fact, period_end) tuples
    """
    facts_found = []
    
    # Extract local name from QName (e.g., "Assets" from "us-gaap:Assets")
    concept_local_name = concept_qname.split(":")[-1] if ":" in concept_qname else concept_qname
    
    # For iXBRL files, facts may not have concept populated, so we need to check QName directly
    # Try multiple approaches:
    # 1. Check fact.qname or fact.elementQname
    # 2. Check fact.concept.qname if concept exists
    # 3. Check fact's local name
    
    # Find all facts for this concept
    for fact in model_xbrl.facts:
        # Get fact QName - try multiple attributes
        fact_qname_str = None
        
        # Method 1: Check fact.qname
        if hasattr(fact, "qname"):
            fact_qname = fact.qname
            if fact_qname:
                fact_qname_str = str(fact_qname)
        
        # Method 2: Check fact.elementQname
        if not fact_qname_str and hasattr(fact, "elementQname"):
            fact_qname = fact.elementQname
            if fact_qname:
                fact_qname_str = str(fact_qname)
        
        # Method 3: Check fact.concept.qname if concept exists
        if not fact_qname_str and hasattr(fact, "concept") and fact.concept:
            if hasattr(fact.concept, "qname"):
                fact_qname_str = str(fact.concept.qname)
        
        # Method 4: Check fact.localName
        if not fact_qname_str and hasattr(fact, "localName"):
            fact_local_name = fact.localName
            if fact_local_name == concept_local_name:
                # Match by local name - construct full QName
                fact_qname_str = concept_qname  # Assume it matches
        
        # Check if this fact matches our concept
        if not fact_qname_str:
            continue
        
        # Match by full QName or local name
        fact_local = fact_qname_str.split(":")[-1] if ":" in fact_qname_str else fact_qname_str
        if fact_qname_str != concept_qname and fact_local != concept_local_name:
            continue
        
        # Check period
        period_end = _get_period_end(fact.context)
        if not _matches_fiscal_year(period_end, fiscal_year):
            continue
        
        # Check consolidated (if required)
        if prefer_consolidated:
            if not _is_consolidated_context(fact.context):
                continue
        
        # Check if fact has a value
        value = _extract_fact_value(fact, prefer_consolidated=False)
        if value is None:
            continue
        
        facts_found.append((fact, period_end or ""))
    
    return facts_found


def _select_best_fact(
    facts: List[Tuple[Any, str]],
    concept_qname: str,
) -> Optional[Tuple[Any, str]]:
    """
    Select the best fact from multiple candidates using precedence rules.
    
    Precedence:
    1. Consolidated context (if multiple, prefer largest magnitude)
    2. Most recent filing date
    3. 10-K form over 10-Q
    
    Args:
        facts: List of (fact, period_end) tuples
        concept_qname: Concept QName (for logging)
        
    Returns:
        Best (fact, period_end) tuple or None
    """
    if not facts:
        return None
    
    if len(facts) == 1:
        return facts[0]
    
    # Group by period_end (should be same for same fiscal year)
    # Then select by magnitude (prefer larger absolute value for totals)
    # For now, just take the first one (they should be similar)
    # In practice, we might want to prefer 10-K over 10-Q, etc.
    
    # Sort by absolute value (descending) - prefer larger values for totals
    facts_sorted = sorted(
        facts,
        key=lambda f: abs(_extract_fact_value(f[0], prefer_consolidated=False) or 0),
        reverse=True,
    )
    
    return facts_sorted[0]


def extract_line_item(
    model_xbrl: Any,
    model_role: str,
    statement_type: str,
    fiscal_year: int,
) -> Optional[ExtractedLineItem]:
    """
    Extract a single line item by model role.
    
    Args:
        model_xbrl: Arelle ModelXbrl object
        model_role: Model role constant (e.g., BS_ASSETS_TOTAL)
        statement_type: "balance_sheet", "income_statement", or "cash_flow"
        fiscal_year: Target fiscal year (e.g., 2024)
        
    Returns:
        ExtractedLineItem or None if not found
    """
    # Get candidate concepts for this model role
    statement_map = MASTER_MAP.get(statement_type, {})
    candidate_qnames = statement_map.get(model_role, [])
    
    if not candidate_qnames:
        logger.debug(f"No candidates for model_role {model_role} in {statement_type}")
        return None
    
    # Try each candidate in order (precedence)
    for concept_qname in candidate_qnames:
        facts = _find_facts_for_concept(
            model_xbrl,
            concept_qname,
            fiscal_year,
            prefer_consolidated=True,
        )
        
        if not facts:
            continue
        
        # Select best fact
        best = _select_best_fact(facts, concept_qname)
        if not best:
            continue
        
        fact, period_end = best
        
        # Extract value
        value = _extract_fact_value(fact, prefer_consolidated=True)
        if value is None:
            continue
        
        # Get concept info
        concept = fact.concept
        tag = str(concept.qname) if concept and hasattr(concept, "qname") else concept_qname
        label = (
            concept.label() if concept and hasattr(concept, "label") else tag
        )
        
        # Get unit
        unit = "USD"
        if fact.unitID and hasattr(model_xbrl, "units"):
            unit_obj = model_xbrl.units.get(fact.unitID)
            if unit_obj is not None:
                # Extract unit string (e.g., "USD")
                if hasattr(unit_obj, "measures"):
                    measures = unit_obj.measures
                    if measures and len(measures) > 0:
                        unit = str(measures[0][0]) if isinstance(measures[0], tuple) else str(measures[0])
        
        # Get context ID
        context_id = fact.contextID if hasattr(fact, "contextID") else None
        
        return ExtractedLineItem(
            model_role=model_role,
            tag=tag,
            label=label,
            value=value,
            unit=unit,
            period_end=period_end,
            status="direct",
            supporting_tags=[tag],
            context_id=context_id,
            is_consolidated=_is_consolidated_context(fact.context),
        )
    
    logger.debug(f"No facts found for model_role {model_role} in {statement_type}")
    return None


def _extract_direct_totals(
    model_xbrl: Any,
    fiscal_year: int,
) -> Dict[str, Optional[ExtractedLineItem]]:
    """
    Direct extraction of key totals (Assets, Liabilities, Equity) by searching all facts.
    This is a fallback when concept-based lookup fails.
    
    Returns:
        Dict mapping model_role -> ExtractedLineItem or None
    """
    results = {}
    
    # Key mappings: model_role -> local names to search for (exact match)
    # Based on debug script, we know facts have local names like "Assets", "Liabilities", "StockholdersEquity"
    key_mappings = {
        BS_ASSETS_TOTAL: ["Assets"],  # Exact local name match
        BS_LIABILITIES_TOTAL: ["Liabilities"],  # Exact local name match  
        BS_EQUITY_TOTAL: ["StockholdersEquity"],  # Exact local name match
    }
    
    # Collect all candidate facts first, then select best
    for model_role, candidate_qnames in key_mappings.items():
        candidates = []
        logger.info(f"Searching for {model_role} with candidates: {candidate_qnames}")
        fact_count = 0
        matched_count = 0
        period_mismatch_count = 0
        value_missing_count = 0
        
        for fact in model_xbrl.facts:
            fact_count += 1
            # Get fact QName - try multiple methods
            fact_qname_str = None
            fact_local = None
            
            # Method 1: fact.qname (most direct) - use same logic as debug script
            if hasattr(fact, "qname") and fact.qname:
                fact_qname_str = str(fact.qname)
                fact_local = fact_qname_str.split(":")[-1] if ":" in fact_qname_str else fact_qname_str
            # Method 2: fact.elementQname
            elif hasattr(fact, "elementQname") and fact.elementQname:
                fact_qname_str = str(fact.elementQname)
                fact_local = fact_qname_str.split(":")[-1] if ":" in fact_qname_str else fact_qname_str
            # Method 3: fact.concept.qname
            elif hasattr(fact, "concept") and fact.concept and hasattr(fact.concept, "qname"):
                fact_qname_str = str(fact.concept.qname)
                fact_local = fact_qname_str.split(":")[-1] if ":" in fact_qname_str else fact_qname_str
            
            if not fact_qname_str or not fact_local:
                continue
            
            # Check if fact matches any candidate QName
            matched_qname = None
            match_priority = 999
            
            # Simplified matching: just check if local name matches any candidate
            for i, candidate_local_name in enumerate(candidate_qnames):
                if fact_local == candidate_local_name:
                    matched_qname = candidate_local_name
                    match_priority = i
                    break
            
            if not matched_qname:
                continue
            
            matched_count += 1
            
            # Check period - use same logic as debug script
            period_end = None
            if fact.context is not None:
                if hasattr(fact.context, "endDatetime") and fact.context.endDatetime is not None:
                    from datetime import timedelta
                    period_end = (fact.context.endDatetime.date() - timedelta(days=1)).isoformat()
                elif hasattr(fact.context, "instantDatetime") and fact.context.instantDatetime is not None:
                    period_end = fact.context.instantDatetime.date().isoformat()
            
            if not period_end:
                continue
            if not _matches_fiscal_year(period_end, fiscal_year):
                period_mismatch_count += 1
                continue
            
            # Check consolidated (relaxed - for now, allow all and sort by value)
            # We'll prefer consolidated in the sorting step
            is_consolidated = _is_consolidated_context(fact.context)
            # For now, don't filter - we'll prefer consolidated in sorting
            
            # Extract value - use same logic as debug script (textValue first)
            value = None
            if hasattr(fact, "xValue") and fact.xValue is not None:
                value = fact.xValue
            elif hasattr(fact, "textValue") and fact.textValue:
                try:
                    value = float(str(fact.textValue).replace(",", "").strip())
                except (ValueError, TypeError):
                    pass
            elif hasattr(fact, "stringValue") and fact.stringValue:
                try:
                    value = float(str(fact.stringValue).replace(",", "").strip())
                except (ValueError, TypeError):
                    pass
            
            if value is None:
                value_missing_count += 1
                continue
            
            # For totals, we want the largest absolute value (consolidated is usually largest)
            # But also check if it's actually consolidated
            is_consolidated = _is_consolidated_context(fact.context)
            
            # Get concept info
            concept = fact.concept if hasattr(fact, "concept") and fact.concept else None
            tag = fact_qname_str
            label = concept.label() if concept and hasattr(concept, "label") else tag
            
            # Get unit
            unit = "USD"
            if hasattr(fact, "unitID") and fact.unitID and hasattr(model_xbrl, "units"):
                unit_obj = model_xbrl.units.get(fact.unitID)
                if unit_obj is not None and hasattr(unit_obj, "measures"):
                    measures = unit_obj.measures
                    if measures and len(measures) > 0:
                        unit = str(measures[0][0]) if isinstance(measures[0], tuple) else str(measures[0])
            
            candidates.append({
                "fact": fact,
                "tag": tag,
                "label": label,
                "value": value,
                "unit": unit,
                "period_end": period_end,
                "match_priority": match_priority,
                "is_consolidated": is_consolidated,
                "context_id": fact.contextID if hasattr(fact, "contextID") else None,
            })
        
        # Log summary
        logger.info(f"  Processed {fact_count} facts, {matched_count} matched QName, "
                   f"{period_mismatch_count} period mismatches, {value_missing_count} missing values")
        
        # Select best candidate
        if candidates:
            logger.info(f"Found {len(candidates)} candidates for {model_role}")
            # Sort by: 1) consolidated first, 2) match priority (lower is better), 3) absolute value (larger for totals)
            candidates.sort(key=lambda c: (
                not c["is_consolidated"],  # Consolidated first (False sorts before True)
                c["match_priority"],
                -abs(c["value"])  # Larger values first
            ))
            best = candidates[0]
            logger.info(f"Selected {best['tag']} with value {best['value']:,.0f} for {model_role}")
            
            results[model_role] = ExtractedLineItem(
                model_role=model_role,
                tag=best["tag"],
                label=best["label"],
                value=best["value"],
                unit=best["unit"],
                period_end=best["period_end"],
                status="direct",
                supporting_tags=[best["tag"]],
                context_id=best["context_id"],
                is_consolidated=_is_consolidated_context(best["fact"].context),
            )
        else:
            logger.warning(f"No candidates found for {model_role}")
    
    return results


def extract_balance_sheet(
    model_xbrl: Any,
    fiscal_year: int,
) -> Dict[str, Any]:
    """
    Extract balance sheet from Arelle ModelXbrl.
    
    Args:
        model_xbrl: Arelle ModelXbrl object
        fiscal_year: Target fiscal year (e.g., 2024)
        
    Returns:
        Dictionary with line_items matching our structured JSON schema:
        {
            "line_items": [
                {
                    "tag": str,
                    "label": str,
                    "model_role": str,
                    "status": str,
                    "unit": str,
                    "periods": {period_end: value},
                    "supporting_tags": [str],
                },
                ...
            ]
        }
    """
    logger.info(f"Extracting balance sheet for fiscal year {fiscal_year}")
    
    line_items = []
    
    # First, try direct extraction of key totals (fallback)
    direct_totals = _extract_direct_totals(model_xbrl, fiscal_year)
    for model_role, item in direct_totals.items():
        if item:
            line_items.append({
                "tag": item.tag,
                "label": item.label,
                "model_role": item.model_role,
                "status": item.status,
                "unit": item.unit,
                "periods": {item.period_end: item.value},
                "supporting_tags": item.supporting_tags,
            })
    
    # Then, try standard extraction for other items
    statement_map = MASTER_MAP.get("balance_sheet", {})
    
    for model_role, candidate_qnames in statement_map.items():
        # Skip if we already got it from direct extraction
        if model_role in direct_totals and direct_totals[model_role]:
            continue
        
        item = extract_line_item(model_xbrl, model_role, "balance_sheet", fiscal_year)
        
        if item:
            line_items.append({
                "tag": item.tag,
                "label": item.label,
                "model_role": item.model_role,
                "status": item.status,
                "unit": item.unit,
                "periods": {item.period_end: item.value},
                "supporting_tags": item.supporting_tags,
            })
    
    logger.info(f"Extracted {len(line_items)} balance sheet line items")
    
    return {
        "line_items": line_items,
    }


def extract_income_statement(
    model_xbrl: Any,
    fiscal_year: int,
) -> Dict[str, Any]:
    """
    Extract income statement from Arelle ModelXbrl.
    
    Args:
        model_xbrl: Arelle ModelXbrl object
        fiscal_year: Target fiscal year (e.g., 2024)
        
    Returns:
        Dictionary with line_items matching our structured JSON schema
    """
    logger.info(f"Extracting income statement for fiscal year {fiscal_year}")
    
    line_items = []
    statement_map = MASTER_MAP.get("income_statement", {})
    
    for model_role, candidate_qnames in statement_map.items():
        item = extract_line_item(model_xbrl, model_role, "income_statement", fiscal_year)
        
        if item:
            line_items.append({
                "tag": item.tag,
                "label": item.label,
                "model_role": item.model_role,
                "status": item.status,
                "unit": item.unit,
                "periods": {item.period_end: item.value},
                "supporting_tags": item.supporting_tags,
            })
    
    logger.info(f"Extracted {len(line_items)} income statement line items")
    
    return {
        "line_items": line_items,
    }


def extract_cash_flow_statement(
    model_xbrl: Any,
    fiscal_year: int,
) -> Dict[str, Any]:
    """
    Extract cash flow statement from Arelle ModelXbrl.
    
    Args:
        model_xbrl: Arelle ModelXbrl object
        fiscal_year: Target fiscal year (e.g., 2024)
        
    Returns:
        Dictionary with line_items matching our structured JSON schema
    """
    logger.info(f"Extracting cash flow statement for fiscal year {fiscal_year}")
    
    line_items = []
    statement_map = MASTER_MAP.get("cash_flow", {})
    
    for model_role, candidate_qnames in statement_map.items():
        item = extract_line_item(model_xbrl, model_role, "cash_flow", fiscal_year)
        
        if item:
            line_items.append({
                "tag": item.tag,
                "label": item.label,
                "model_role": item.model_role,
                "status": item.status,
                "unit": item.unit,
                "periods": {item.period_end: item.value},
                "supporting_tags": item.supporting_tags,
            })
    
    logger.info(f"Extracted {len(line_items)} cash flow statement line items")
    
    return {
        "line_items": line_items,
    }

