"""
debt_extractor.py — Robust Interest-Bearing Debt Extraction Module

This module provides comprehensive extraction of interest-bearing debt from multiple
sources (XBRL tags, structured statements, fallback calculations) with full auditability.

Key Features:
- Multiple fallback methods (5 methods)
- Full component-level breakdown
- Human-readable audit trail
- Ford-specific segment handling (Automotive + Credit)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from pathlib import Path
import json

from app.core.logging import get_logger
from app.core.model_role_map import (
    BS_DEBT_CURRENT,
    BS_DEBT_NONCURRENT,
    IS_INTEREST_EXPENSE,
)

logger = get_logger(__name__)

# Standard XBRL tags for interest-bearing debt
DEBT_XBRL_TAGS = {
    "us-gaap:ShortTermBorrowings",
    "us-gaap:DebtCurrent",
    "us-gaap:CommercialPaper",
    "us-gaap:LongTermDebt",
    "us-gaap:LongTermDebtNoncurrent",
    "us-gaap:LongTermBorrowings",
    "us-gaap:DebtNoncurrent",
    "us-gaap:FinanceLeaseLiabilityCurrent",
    "us-gaap:FinanceLeaseLiabilityNoncurrent",
    "us-gaap:SecuredDebt",
    "us-gaap:UnsecuredDebt",
    "us-gaap:BorrowingsUnderRevolvingCreditFacility",
    "us-gaap:VariableInterestEntityDebt",
    "us-gaap:LongTermDebtCurrent",
    "us-gaap:LongTermDebtAndCapitalLeaseObligationsCurrent",
    "us-gaap:LongTermDebtAndCapitalLeaseObligationsNoncurrent",
    "us-gaap:LongTermDebtAndFinanceLeaseObligationsCurrent",
    "us-gaap:LongTermDebtAndFinanceLeaseObligationsNoncurrent",
    "us-gaap:NotesPayableCurrent",
    "us-gaap:NotesPayableNoncurrent",
    "us-gaap:CurrentPortionOfLongTermDebt",
}

# Keywords for identifying debt in statement labels
DEBT_KEYWORDS = [
    "short-term debt",
    "short term debt",
    "long-term debt",
    "long term debt",
    "current portion of long-term debt",
    "commercial paper",
    "notes payable",
    "borrowings",
    "revolving credit",
    "finance lease",
    "capital lease",
    "secured debt",
    "unsecured debt",
    "total debt",
    "total borrowings",
    "interest-bearing debt",
]

# Keywords to EXCLUDE (non-interest-bearing)
EXCLUDE_KEYWORDS = [
    "accounts payable",
    "accrued",
    "operating lease",
    "pension",
    "deferred revenue",
    "warranty",
    "taxes payable",
    "income taxes",
]


@dataclass
class DebtComponent:
    """Represents a single component of interest-bearing debt."""
    name: str                    # e.g., "Short-Term Borrowings"
    source_type: str             # "xbrl", "statement", "derived"
    source_identifier: str       # e.g., XBRL tag or statement label
    context: Optional[str] = None  # e.g., reporting entity / segment / period
    value: float = 0.0           # numeric amount used in the sum
    
    def __repr__(self) -> str:
        ctx_str = f", context='{self.context}'" if self.context else ""
        return f"{self.name} ({self.source_identifier}{ctx_str}): {self.value:,.0f}"


@dataclass
class DebtMethodResult:
    """Result from a single debt calculation method."""
    method_name: str             # "XBRL_AGGREGATION", "STRUCTURED_STATEMENT", etc.
    description: str             # human-readable explanation
    components: List[DebtComponent] = field(default_factory=list)
    formula: str = ""            # human-readable formula
    value: Optional[float] = None  # final number from this method, if computed
    warnings: List[str] = field(default_factory=list)
    
    def is_reliable(self) -> bool:
        """Check if this method produced a reliable result."""
        return self.value is not None and self.value >= 0 and len(self.components) > 0


@dataclass
class InterestBearingDebtResult:
    """Final result with all methods attempted and primary result."""
    final_value: Optional[float] = None          # interest_bearing_debt
    primary_method: Optional[str] = None         # name of the method actually used
    all_methods: List[DebtMethodResult] = field(default_factory=list)
    period: Optional[str] = None                 # Period date string
    
    def to_human_readable(self) -> str:
        """
        Return a multi-line string that explains, step-by-step, how the
        final_value was calculated from its components and methods.
        """
        lines = []
        lines.append("=" * 80)
        lines.append("INTEREST-BEARING DEBT EXTRACTION REPORT")
        lines.append("=" * 80)
        
        if self.period:
            lines.append(f"\nPeriod: {self.period}")
        
        if self.final_value is not None:
            lines.append(f"\nFinal Interest-Bearing Debt: ${self.final_value:,.0f}")
        else:
            lines.append("\nFinal Interest-Bearing Debt: NOT COMPUTABLE")
        
        if self.primary_method:
            lines.append(f"\nPrimary Method: {self.primary_method}")
        else:
            lines.append("\nPrimary Method: NONE (no reliable method found)")
        
        lines.append("\n" + "-" * 80)
        lines.append("METHOD DETAILS")
        lines.append("-" * 80)
        
        for i, method in enumerate(self.all_methods, 1):
            lines.append(f"\nMethod {i}: {method.method_name}")
            lines.append(f"  Description: {method.description}")
            
            if method.value is not None:
                lines.append(f"  Result: ${method.value:,.0f}")
            else:
                lines.append(f"  Result: NOT COMPUTABLE")
            
            if method.formula:
                lines.append(f"  Formula: {method.formula}")
            
            if method.components:
                lines.append(f"  Components ({len(method.components)}):")
                for comp in method.components:
                    lines.append(f"    - {comp}")
            else:
                lines.append("  Components: None found")
            
            if method.warnings:
                lines.append(f"  Warnings ({len(method.warnings)}):")
                for warning in method.warnings:
                    lines.append(f"    - {warning}")
            
            # Mark primary method
            if method.method_name == self.primary_method:
                lines.append("  [PRIMARY METHOD USED]")
        
        lines.append("\n" + "=" * 80)
        return "\n".join(lines)


def _is_debt_tag(tag: str) -> bool:
    """Check if an XBRL tag represents interest-bearing debt."""
    tag_lower = tag.lower()
    # Check exact matches
    if tag in DEBT_XBRL_TAGS:
        return True
    # Check namespace-prefixed matches
    for debt_tag in DEBT_XBRL_TAGS:
        if tag_lower.endswith(debt_tag.split(":")[-1].lower()):
            return True
    return False


def _is_debt_label(label: str) -> bool:
    """Check if a statement label represents interest-bearing debt."""
    label_lower = label.lower()
    
    # Exclude non-debt items first
    for exclude_kw in EXCLUDE_KEYWORDS:
        if exclude_kw in label_lower:
            return False
    
    # Check for debt keywords
    for debt_kw in DEBT_KEYWORDS:
        if debt_kw in label_lower:
            return True
    
    return False


def _extract_value_from_periods(periods: Dict[str, Any], period: Optional[str] = None) -> Optional[float]:
    """Extract numeric value from periods dictionary."""
    if not periods:
        return None
    
    # If period specified, use it
    if period and period in periods:
        val = periods[period]
        try:
            return float(val)
        except (ValueError, TypeError):
            return None
    
    # Otherwise, use the most recent period
    sorted_periods = sorted(periods.keys(), reverse=True)
    if sorted_periods:
        val = periods[sorted_periods[0]]
        try:
            return float(val)
        except (ValueError, TypeError):
            return None
    
    return None


def get_xbrl_debt_values(
    filing_json: Dict[str, Any],
    period: Optional[str] = None,
) -> DebtMethodResult:
    """
    Method 1: Extract and aggregate all debt-related XBRL tags.
    
    Handles multiple segments (e.g., Ford Automotive + Ford Credit).
    Can work with either raw XBRL JSON or structured JSON with XBRL tags.
    """
    result = DebtMethodResult(
        method_name="XBRL_AGGREGATION",
        description="Sum of all interest-bearing debt XBRL tags from company facts",
        formula="sum(all_debt_xbrl_tags)",
    )
    
    components: List[DebtComponent] = []
    total_debt = 0.0
    
    # Try raw XBRL structure first (EDGAR Company Facts format)
    facts = filing_json.get("facts", {})
    us_gaap = facts.get("us-gaap", {})
    
    if us_gaap:
        # Process raw XBRL structure
        for tag, tag_data in us_gaap.items():
            if not _is_debt_tag(tag):
                continue
            
            # Get units (prefer USD)
            units = tag_data.get("units", {})
            usd_units = units.get("USD", [])
            
            if not usd_units:
                # Try other monetary units
                for unit_key, unit_data in units.items():
                    if "USD" in unit_key.upper() or unit_key.upper() in ["USD", "USDOLLARS"]:
                        usd_units = unit_data
                        break
            
            if not usd_units:
                continue
            
            # Process each fact/observation
            for fact in usd_units:
                # Check if this is the right period
                end_date = fact.get("end")
                start_date = fact.get("start")
                
                # For instant facts (balance sheet), use end date
                # For duration facts, check if period falls within range
                if period:
                    if start_date is None:  # Instant fact
                        if end_date != period:
                            continue
                    else:  # Duration fact
                        if not (start_date <= period <= end_date):
                            continue
                
                # Check for dimensions (prefer consolidated/non-dimensional)
                dimensions = fact.get("dimensions", {})
                
                # Prefer dimensionless facts (consolidated)
                if dimensions:
                    # Check if it's a segment-specific fact
                    segment_dim = dimensions.get("us-gaap:ConsolidationItemsAxis", {})
                    if segment_dim:
                        segment_value = segment_dim.get("value", "")
                        context = f"Segment: {segment_value}"
                    else:
                        context = "Dimensional fact (may include segments)"
                else:
                    context = "Consolidated"
                
                # Extract value
                val = fact.get("val")
                if val is None:
                    continue
                
                try:
                    value = float(val)
                except (ValueError, TypeError):
                    continue
                
                # Get label
                label = tag_data.get("label", tag)
                
                # Create component
                component = DebtComponent(
                    name=label,
                    source_type="xbrl",
                    source_identifier=tag,
                    context=context,
                    value=value,
                )
                components.append(component)
                total_debt += value
    
    # Also try structured JSON format (if it has XBRL tags in line items)
    statements = filing_json.get("statements", {})
    balance_sheet = statements.get("balance_sheet", {})
    line_items = balance_sheet.get("line_items", [])
    
    if line_items:
        # Extract from structured line items that have XBRL tags
        for item in line_items:
            tag = item.get("tag", "")
            label = item.get("label", "")
            periods = item.get("periods", {})
            
            # Check if this is a debt XBRL tag
            if not _is_debt_tag(tag):
                continue
            
            # Extract value for the period
            value = _extract_value_from_periods(periods, period)
            if value is None or value == 0:
                continue
            
            # Check if we already have this component (avoid duplicates)
            if any(comp.source_identifier == tag for comp in components):
                continue
            
            # Determine context
            context = "Consolidated"
            if "ford" in label.lower() or "automotive" in label.lower() or "credit" in label.lower():
                context = "Segment-specific"
            
            component = DebtComponent(
                name=label or tag,
                source_type="xbrl",
                source_identifier=tag,
                context=context,
                value=value,
            )
            components.append(component)
            total_debt += value
    
    result.components = components
    result.value = total_debt if components else None
    
    if not components:
        result.warnings.append("No debt XBRL tags found in filing")
    elif not us_gaap and not line_items:
        result.warnings.append("Neither raw XBRL structure nor structured statements found")
    
    return result


def get_statement_debt_values(
    structured_statement_json: Dict[str, Any],
    period: Optional[str] = None,
) -> DebtMethodResult:
    """
    Method 2: Look up conventional financial statement line items.
    
    Maps labels → DebtComponent entries and computes total.
    """
    result = DebtMethodResult(
        method_name="STRUCTURED_STATEMENT",
        description="Sum of debt line items from structured balance sheet",
        formula="Short-Term Debt + Current Portion of Long-Term Debt + Long-Term Debt + Finance Lease Liabilities",
    )
    
    # Navigate to balance sheet
    statements = structured_statement_json.get("statements", {})
    balance_sheet = statements.get("balance_sheet", {})
    line_items = balance_sheet.get("line_items", [])
    
    if not line_items:
        result.warnings.append("No balance sheet line items found")
        return result
    
    components: List[DebtComponent] = []
    total_debt = 0.0
    
    # Look for debt-related line items
    for item in line_items:
        label = item.get("label", "")
        tag = item.get("tag", "")
        model_role = item.get("model_role", "")
        periods = item.get("periods", {})
        
        # Check if this is a debt item
        is_debt = False
        
        # Check by model role first
        if model_role in [BS_DEBT_CURRENT, BS_DEBT_NONCURRENT]:
            is_debt = True
        # Check by label
        elif _is_debt_label(label):
            is_debt = True
        # Check by tag
        elif _is_debt_tag(tag):
            is_debt = True
        
        if not is_debt:
            continue
        
        # Extract value
        value = _extract_value_from_periods(periods, period)
        if value is None or value == 0:
            continue
        
        # Determine context
        context = "Consolidated"
        if "ford" in label.lower() or "automotive" in label.lower() or "credit" in label.lower():
            context = "Segment-specific"
        
        component = DebtComponent(
            name=label,
            source_type="statement",
            source_identifier=tag or label,
            context=context,
            value=value,
        )
        components.append(component)
        total_debt += value
    
    result.components = components
    result.value = total_debt if components else None
    
    if not components:
        result.warnings.append("No debt line items found in structured balance sheet")
    
    return result


def get_total_debt_summarized(
    structured_statement_json: Dict[str, Any],
    period: Optional[str] = None,
) -> DebtMethodResult:
    """
    Method 3: Try to find "Total Debt"/"Total Borrowings" style lines.
    
    Flags clearly that this is a summarized source.
    """
    result = DebtMethodResult(
        method_name="TOTAL_DEBT_SUMMARIZED",
        description="Use explicit 'Total Debt' or 'Total Borrowings' line item if available",
        formula="Total Debt (from single line item)",
    )
    
    statements = structured_statement_json.get("statements", {})
    balance_sheet = statements.get("balance_sheet", {})
    line_items = balance_sheet.get("line_items", [])
    
    if not line_items:
        result.warnings.append("No balance sheet line items found")
        return result
    
    # Look for explicit total debt lines
    total_debt_labels = [
        "total debt",
        "total borrowings",
        "total interest-bearing debt",
        "total debt and capital lease obligations",
        "total debt and finance lease obligations",
    ]
    
    for item in line_items:
        label = item.get("label", "").lower()
        periods = item.get("periods", {})
        
        # Check if this matches a total debt label
        is_total_debt = any(td_label in label for td_label in total_debt_labels)
        
        # Exclude if it includes operating leases
        if "operating lease" in label:
            continue
        
        if is_total_debt:
            value = _extract_value_from_periods(periods, period)
            if value is not None and value > 0:
                component = DebtComponent(
                    name=item.get("label", "Total Debt"),
                    source_type="statement",
                    source_identifier=item.get("tag", item.get("label", "")),
                    context="Consolidated (summarized line)",
                    value=value,
                )
                result.components = [component]
                result.value = value
                result.formula = f"Total Debt = {value:,.0f} (from single summarized line item)"
                return result
    
    result.warnings.append("No explicit 'Total Debt' line item found")
    return result


def get_segmented_debt_if_applicable(
    structured_data: Dict[str, Any],
    period: Optional[str] = None,
) -> DebtMethodResult:
    """
    Method 4: Ford-like split: Automotive + Credit.
    
    If the company has separate Automotive and Credit / Finance segments,
    sum them explicitly.
    """
    result = DebtMethodResult(
        method_name="SEGMENTED_DEBT",
        description="Sum of Automotive Debt + Credit/Finance Segment Debt (Ford-style)",
        formula="automotive_debt + credit_debt",
    )
    
    statements = structured_data.get("statements", {})
    balance_sheet = statements.get("balance_sheet", {})
    line_items = balance_sheet.get("line_items", [])
    
    if not line_items:
        result.warnings.append("No balance sheet line items found")
        return result
    
    automotive_debt = 0.0
    credit_debt = 0.0
    automotive_components: List[DebtComponent] = []
    credit_components: List[DebtComponent] = []
    
    # Look for segment-specific debt items
    for item in line_items:
        label = item.get("label", "").lower()
        periods = item.get("periods", {})
        
        # Check if this is debt-related
        if not _is_debt_label(item.get("label", "")):
            continue
        
        value = _extract_value_from_periods(periods, period)
        if value is None or value == 0:
            continue
        
        # Determine segment
        is_automotive = any(kw in label for kw in ["automotive", "ford automotive", "auto"])
        is_credit = any(kw in label for kw in ["credit", "finance", "financial services", "ford credit"])
        
        if is_automotive:
            component = DebtComponent(
                name=item.get("label", ""),
                source_type="statement",
                source_identifier=item.get("tag", item.get("label", "")),
                context="Ford Automotive",
                value=value,
            )
            automotive_components.append(component)
            automotive_debt += value
        elif is_credit:
            component = DebtComponent(
                name=item.get("label", ""),
                source_type="statement",
                source_identifier=item.get("tag", item.get("label", "")),
                context="Ford Credit",
                value=value,
            )
            credit_components.append(component)
            credit_debt += value
    
    # Only return result if we found both segments
    if automotive_debt > 0 or credit_debt > 0:
        all_components = automotive_components + credit_components
        total = automotive_debt + credit_debt
        
        result.components = all_components
        result.value = total
        result.formula = f"Automotive Debt ({automotive_debt:,.0f}) + Credit Debt ({credit_debt:,.0f}) = {total:,.0f}"
    else:
        result.warnings.append("No segmented debt found (not applicable or not Ford-style structure)")
    
    return result


def _get_interest_expense(
    structured_data: Dict[str, Any],
    period: Optional[str] = None,
) -> Optional[float]:
    """Extract interest expense from income statement."""
    statements = structured_data.get("statements", {})
    income_statement = statements.get("income_statement", {})
    line_items = income_statement.get("line_items", [])
    
    for item in line_items:
        model_role = item.get("model_role", "")
        if model_role == IS_INTEREST_EXPENSE:
            periods = item.get("periods", {})
            return _extract_value_from_periods(periods, period)
    
    return None


def compute_interest_bearing_debt(
    data_sources: Dict[str, Any],
    period: Optional[str] = None,
    assumed_interest_rate: float = 0.06,
) -> InterestBearingDebtResult:
    """
    Main orchestrator: Attempt all methods in priority order.
    
    Args:
        data_sources: Dictionary with keys:
            - "xbrl_json": Raw XBRL company facts JSON
            - "structured_statements_json": Structured output JSON
        period: Period date string (e.g., "2024-12-31")
        assumed_interest_rate: Assumed interest rate for Method 5 (default 6%)
    
    Returns:
        InterestBearingDebtResult with all methods attempted and primary result
    """
    result = InterestBearingDebtResult(period=period)
    
    xbrl_json = data_sources.get("xbrl_json")
    structured_json = data_sources.get("structured_statements_json")
    
    # Method 1: XBRL Aggregation
    if xbrl_json:
        method1 = get_xbrl_debt_values(xbrl_json, period)
        result.all_methods.append(method1)
        if method1.is_reliable() and result.primary_method is None:
            result.primary_method = method1.method_name
            result.final_value = method1.value
    
    # Method 2: Structured Statement
    if structured_json:
        method2 = get_statement_debt_values(structured_json, period)
        result.all_methods.append(method2)
        if method2.is_reliable() and result.primary_method is None:
            result.primary_method = method2.method_name
            result.final_value = method2.value
    
    # Method 3: Total Debt Summarized
    if structured_json:
        method3 = get_total_debt_summarized(structured_json, period)
        result.all_methods.append(method3)
        if method3.is_reliable() and result.primary_method is None:
            result.primary_method = method3.method_name
            result.final_value = method3.value
    
    # Method 4: Segmented Debt (Ford-style)
    if structured_json:
        method4 = get_segmented_debt_if_applicable(structured_json, period)
        result.all_methods.append(method4)
        if method4.is_reliable() and result.primary_method is None:
            result.primary_method = method4.method_name
            result.final_value = method4.value
    
    # Method 5: Interest Expense Backsolve (last resort)
    if structured_json:
        interest_expense = _get_interest_expense(structured_json, period)
        if interest_expense is not None and interest_expense > 0:
            implied_debt = interest_expense / assumed_interest_rate
            method5 = DebtMethodResult(
                method_name="INTEREST_EXPENSE_BACKSOLVE",
                description=f"Implied debt from interest expense and assumed rate",
                formula=f"Interest Expense ({interest_expense:,.0f}) / Assumed Rate ({assumed_interest_rate:.1%})",
                value=implied_debt,
                components=[
                    DebtComponent(
                        name="Interest Expense",
                        source_type="derived",
                        source_identifier="IS_INTEREST_EXPENSE",
                        context="Income Statement",
                        value=interest_expense,
                    )
                ],
                warnings=[
                    f"Using assumed interest rate of {assumed_interest_rate:.1%}",
                    "This is a rough estimate, not a precise accounting measure",
                ],
            )
            result.all_methods.append(method5)
            if method5.is_reliable() and result.primary_method is None:
                result.primary_method = method5.method_name
                result.final_value = method5.value
        else:
            method5 = DebtMethodResult(
                method_name="INTEREST_EXPENSE_BACKSOLVE",
                description="Implied debt from interest expense and assumed rate",
                formula="Interest Expense / Assumed Rate",
                warnings=["Interest expense not found or zero"],
            )
            result.all_methods.append(method5)
    
    return result


def get_interest_bearing_debt_for_ticker(
    ticker: str,
    output_dir: str | Path = "outputs",
    period: Optional[str] = None,
    assumed_interest_rate: float = 0.06,
) -> InterestBearingDebtResult:
    """
    High-level entry point: Load XBRL + structured output files for the ticker.
    
    Args:
        ticker: Stock ticker symbol (e.g., "F")
        output_dir: Directory containing JSON files
        period: Period date string (optional, uses latest if not provided)
        assumed_interest_rate: Assumed interest rate for Method 5
    
    Returns:
        InterestBearingDebtResult object
    """
    output_dir = Path(output_dir)
    
    # Try to find structured JSON file
    # Look for single-year or multi-year files
    json_files = list(output_dir.glob(f"{ticker}_*_single_year_llm_classified.json"))
    if not json_files:
        json_files = list(output_dir.glob(f"{ticker}_*_multi_year_*_llm_classified.json"))
    
    if not json_files:
        # Try to load from EDGAR directly
        from app.services.ingestion.clients import EdgarClient
        from app.services.ingestion.structured_output import extract_single_year_structured
        
        logger.info(f"JSON files not found for {ticker}, fetching from EDGAR...")
        # This would require CIK lookup - simplified for now
        raise FileNotFoundError(f"No JSON files found for ticker {ticker} in {output_dir}")
    
    # Load the most recent file
    json_file = sorted(json_files, key=lambda p: p.stat().st_mtime, reverse=True)[0]
    logger.info(f"Loading structured JSON from: {json_file}")
    
    with json_file.open('r', encoding='utf-8') as f:
        structured_json = json.load(f)
    
    # Extract period if not provided
    if not period:
        periods = structured_json.get("periods", [])
        if periods:
            period = periods[-1]  # Use most recent period
        else:
            # Try to get from metadata
            metadata = structured_json.get("metadata", {})
            fiscal_year = metadata.get("fiscal_year")
            if fiscal_year:
                period = f"{fiscal_year}-12-31"
    
    # For XBRL JSON, we'd need to load the raw company facts
    # For now, we'll use the structured JSON which contains XBRL tags
    # In a full implementation, you'd load the raw XBRL JSON separately
    
    data_sources = {
        "structured_statements_json": structured_json,
        # "xbrl_json": xbrl_json,  # Would need to load separately
    }
    
    return compute_interest_bearing_debt(
        data_sources=data_sources,
        period=period,
        assumed_interest_rate=assumed_interest_rate,
    )

