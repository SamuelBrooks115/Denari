"""
debt_facts_collector.py — Collect all debt-related XBRL facts for transparency and auditing.

This module collects comprehensive debt-related facts from XBRL instances, including
both standard GAAP tags and company-specific extensions, to provide full visibility
into all components that might contribute to Total Debt calculations.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.logging import get_logger
from app.services.ingestion.xbrl.utils import flatten_units, parse_date

logger = get_logger(__name__)

# Standard GAAP debt tags (non-exhaustive but important)
STANDARD_DEBT_TAGS = {
    "DebtCurrent",
    "DebtNoncurrent",
    "ShortTermBorrowings",
    "CommercialPaper",
    "LongTermDebtCurrent",
    "LongTermDebtNoncurrent",
    "LongTermLineOfCredit",
    "LongTermNotesPayable",
    "FinanceLeaseLiabilityCurrent",
    "FinanceLeaseLiabilityNoncurrent",
    "ConvertibleDebtCurrent",
    "ConvertibleDebtNoncurrent",
    "ShortTermDebt",
    "NotesPayableCurrent",
    "NotesPayableNoncurrent",
    "UnsecuredDebtCurrent",
    "UnsecuredLongTermDebt",
    "SecuredDebtCurrent",
    "SecuredLongTermDebt",
    "CurrentPortionOfLongTermDebt",
    "LongTermDebtAndCapitalLeaseObligationsCurrent",
    "LongTermDebtAndCapitalLeaseObligationsNoncurrent",
    "LongTermDebtAndFinanceLeaseObligationsCurrent",
    "LongTermDebtAndFinanceLeaseObligationsNoncurrent",
}

# Keywords to identify debt-related tags in company extensions
DEBT_KEYWORDS = [
    "debt",
    "borrowings",
    "notespayable",
    "loan",
    "creditfacility",
    "revolvingcredit",
    "secureddebt",
    "unsecureddebt",
    "fordcredit",
    "leaseobligation",
    "leaseobligations",
    "financeliability",
    "financeliabilities",
]


def _is_debt_tag(tag: str, label: Optional[str] = None) -> bool:
    """
    Check if a tag is debt-related.
    
    Args:
        tag: XBRL tag name (e.g., "LongTermDebtNoncurrent" or "ford:FordCreditDebt")
        label: Optional human-readable label
        
    Returns:
        True if the tag appears to be debt-related
    """
    tag_lower = tag.lower()
    
    # Check if it's a standard GAAP debt tag
    if tag in STANDARD_DEBT_TAGS:
        return True
    
    # Remove namespace prefix if present (e.g., "ford:FordCreditDebt" -> "fordcreditdebt")
    tag_clean = tag_lower.split(":")[-1] if ":" in tag_lower else tag_lower
    
    # Check for debt keywords
    for keyword in DEBT_KEYWORDS:
        if keyword in tag_clean:
            return True
    
    # Check label if provided
    if label:
        label_lower = label.lower()
        for keyword in DEBT_KEYWORDS:
            if keyword in label_lower:
                return True
    
    return False


def _is_monetary_fact(record: Dict[str, Any]) -> bool:
    """
    Check if a fact record represents a monetary value (not ratio, percentage, etc.).
    
    Args:
        record: XBRL fact record
        
    Returns:
        True if the record appears to be a monetary fact
    """
    unit = record.get("_unit") or record.get("unit", "")
    unit_lower = unit.lower()
    
    # Monetary units
    if unit_lower in ("usd", "eur", "gbp", "jpy", "cny", "cad", "aud"):
        return True
    
    # Exclude non-monetary units
    if unit_lower in ("shares", "pure", "xbrli:shares", "xbrli:pure"):
        return False
    
    # If no unit specified but value is numeric, assume monetary
    if not unit and isinstance(record.get("val"), (int, float)):
        return True
    
    return False


def _infer_statement_type(tag: str, label: Optional[str] = None) -> str:
    """
    Infer the statement type from tag and label.
    
    Args:
        tag: XBRL tag name
        label: Optional human-readable label
        
    Returns:
        "Balance Sheet", "Income Statement", "Cash Flow Statement", or "Unknown"
    """
    tag_lower = tag.lower()
    label_lower = (label or "").lower()
    
    # Balance sheet indicators
    if any(indicator in tag_lower or indicator in label_lower for indicator in [
        "current", "noncurrent", "liability", "obligation", "payable", "receivable",
        "asset", "equity", "stockholder", "shareholder"
    ]):
        # But exclude income statement items
        if any(indicator in tag_lower or indicator in label_lower for indicator in [
            "expense", "income", "revenue", "cost", "earnings"
        ]):
            return "Income Statement"
        return "Balance Sheet"
    
    # Cash flow indicators
    if any(indicator in tag_lower or indicator in label_lower for indicator in [
        "cashflow", "cash flow", "operating", "investing", "financing", "proceeds",
        "payments", "repayment", "issuance"
    ]):
        return "Cash Flow Statement"
    
    # Income statement indicators
    if any(indicator in tag_lower or indicator in label_lower for indicator in [
        "expense", "income", "revenue", "cost", "earnings", "profit", "loss"
    ]):
        return "Income Statement"
    
    return "Unknown"


def collect_debt_facts_for_ford(
    facts_payload: Dict[str, Any],
    periods: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Collect all debt-related facts from Ford's XBRL instance.
    
    This function iterates over all facts in the XBRL instance and selects facts
    that clearly relate to debt (interest-bearing funding sources), including both
    standard GAAP tags and Ford-specific extensions.
    
    Args:
        facts_payload: Full company facts payload from EDGAR API
        periods: Optional list of period end dates to filter by. If None, includes all periods.
        
    Returns:
        List of dictionaries with debt fact details:
        {
            "tag": str,
            "label": str,
            "value": float,
            "unit": str,
            "period": {
                "type": "instant" | "duration",
                "date": str,  # for instant
                "start": str,  # for duration
                "end": str     # for duration
            },
            "statement": str,
            "is_standard_gaap_tag": bool,
            "namespace": str,  # e.g., "us-gaap" or "ford"
        }
    """
    debt_facts = []
    
    facts_root = facts_payload.get("facts", {})
    if not facts_root:
        logger.warning("No 'facts' section found in company facts payload")
        return debt_facts
    
    # Process all taxonomies (us-gaap, company extensions, etc.)
    for taxonomy_name, taxonomy_facts in facts_root.items():
        if not isinstance(taxonomy_facts, dict):
            continue
        
        is_standard_gaap = (taxonomy_name == "us-gaap")
        
        # Iterate over all tags in this taxonomy
        for tag, tag_node in taxonomy_facts.items():
            if not isinstance(tag_node, dict):
                continue
            
            # Get label
            label = tag_node.get("label") or tag_node.get("description") or tag
            
            # Check if this is a debt-related tag
            if not _is_debt_tag(tag, label):
                continue
            
            # Get units
            units = tag_node.get("units")
            if not isinstance(units, dict):
                continue
            
            # Flatten all unit records
            all_records = flatten_units(units)
            
            # Process each record
            for record in all_records:
                # Filter by period if specified
                if periods:
                    end = record.get("end")
                    if end not in periods:
                        continue
                
                # Only include monetary facts
                if not _is_monetary_fact(record):
                    continue
                
                # Get value
                val = record.get("val")
                if val is None:
                    continue
                
                try:
                    value = float(val)
                except (ValueError, TypeError):
                    continue
                
                # Determine period type
                start = record.get("start")
                end = record.get("end")
                period_type = "instant" if not start or start == end else "duration"
                
                # Build period info
                period_info: Dict[str, Any] = {
                    "type": period_type,
                }
                if period_type == "instant":
                    period_info["date"] = end
                else:
                    period_info["start"] = start
                    period_info["end"] = end
                
                # Infer statement type
                statement = _infer_statement_type(tag, label)
                
                # Build fact record
                fact_record = {
                    "tag": tag,
                    "label": label,
                    "value": value,
                    "unit": record.get("_unit") or record.get("unit") or "USD",
                    "period": period_info,
                    "statement": statement,
                    "is_standard_gaap_tag": is_standard_gaap,
                    "namespace": taxonomy_name,
                }
                
                # Add filing metadata if available
                if "form" in record:
                    fact_record["filing_form"] = record.get("form")
                if "filed" in record:
                    fact_record["filing_date"] = record.get("filed")
                if "accn" in record:
                    fact_record["accession"] = record.get("accn")
                
                debt_facts.append(fact_record)
    
    # Sort by statement, then by tag, then by period end date (descending)
    debt_facts.sort(key=lambda x: (
        x.get("statement", "Unknown"),
        x.get("tag", ""),
        x.get("period", {}).get("end") or x.get("period", {}).get("date", ""),
    ), reverse=False)
    
    # Log summary
    standard_count = sum(1 for f in debt_facts if f.get("is_standard_gaap_tag"))
    extension_count = len(debt_facts) - standard_count
    logger.info(
        f"Collected {len(debt_facts)} debt-related facts "
        f"({standard_count} standard GAAP, {extension_count} company extensions)"
    )
    
    return debt_facts

