"""
debt_extractor.py — Comprehensive XBRL debt fact extractor with segment classification.

This module extracts all interest-bearing debt facts from XBRL instances, properly
classifying them by segment (consolidated, company excluding Ford Credit, Ford Credit, etc.)
for use in debt calculations and reconciliation.

Uses existing Denari XBRL infrastructure:
- app.services.ingestion.xbrl.utils.flatten_units() for unit flattening
- app.services.ingestion.clients.EdgarClient for fetching company facts
- EDGAR Company Facts API JSON structure
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger
from app.services.ingestion.xbrl.utils import flatten_units

logger = get_logger(__name__)


# ============================================================================
# STEP 2: DEBT TAG UNIVERSE
# ============================================================================

# Core standard us-gaap debt tags (exact spelling as in XBRL)
DEBT_TAGS_CORE = {
    "ShortTermBorrowings",
    "DebtCurrent",
    "CommercialPaper",
    "LongTermDebt",
    "LongTermDebtNoncurrent",
    "LongTermDebtCurrent",
    "LongTermBorrowings",
    "DebtNoncurrent",
    "LongTermDebtAndCapitalLeaseObligations",
    "LongTermDebtAndCapitalLeaseObligationsCurrent",
    "LongTermDebtAndCapitalLeaseObligationsNoncurrent",
    "LongTermDebtAndFinanceLeaseObligations",
    "LongTermDebtAndFinanceLeaseObligationsCurrent",
    "LongTermDebtAndFinanceLeaseObligationsNoncurrent",
    "BorrowingsUnderRevolvingCreditFacility",
    "FinanceLeaseLiabilityCurrent",
    "FinanceLeaseLiabilityNoncurrent",
    "FinanceLeaseLiability",
    "VariableInterestEntityDebt",
    "NotesPayableCurrent",
    "NotesPayableNoncurrent",
    "UnsecuredDebtCurrent",
    "UnsecuredLongTermDebt",
    "SecuredDebtCurrent",
    "SecuredLongTermDebt",
    "CurrentPortionOfLongTermDebt",
    "ConvertibleDebtCurrent",
    "ConvertibleDebtNoncurrent",
    "LongTermLineOfCredit",
    "LongTermNotesPayable",
    "ShortTermDebt",
}

# Keywords to identify debt-related tags in company extensions
DEBT_TAG_NAME_KEYWORDS = [
    "debt",
    "borrowings",
    "notespayable",
    "loan",
    "creditfacility",
    "revolvingcredit",
    "unsecured",
    "assetbacked",
    "secureddebt",
    "unsecureddebt",
    "leaseobligation",
    "leaseobligations",
    "financeliability",
    "financeliabilities",
]


# ============================================================================
# STEP 4: SEGMENT CLASSIFICATION
# ============================================================================

class DebtSegment(Enum):
    """Classification of debt facts by segment/entity."""
    CONSOLIDATED = "consolidated"
    COMPANY_EXCL_FORD_CREDIT = "company_excl_ford_credit"
    FORD_CREDIT = "ford_credit"
    OTHER = "other"


def classify_debt_segment(
    record: Dict[str, Any],
    tag: Optional[str] = None,
    label: Optional[str] = None,
) -> DebtSegment:
    """
    Classify a debt fact by segment based on context dimensions and labels.
    
    This function inspects XBRL dimensions/axes to determine if a fact represents:
    - Consolidated entity (no dimensions or explicit consolidated)
    - Company excluding Ford Credit (Automotive & Corporate)
    - Ford Credit (Financial services segment)
    - Other segment
    
    Args:
        record: XBRL fact record (may contain dimensions, segment, etc.)
        tag: Optional XBRL tag name (for label-based inference)
        label: Optional human-readable label (for label-based inference)
        
    Returns:
        DebtSegment enum value
    """
    # Check for explicit dimensions
    dimensions = record.get("dimensions", {})
    segment_info = record.get("segment") or record.get("segments", {})
    
    # If we have dimensions dict, check for common axes
    if dimensions:
        # Check ConsolidationItemsAxis (common in XBRL)
        consolidation_axis = dimensions.get("us-gaap:ConsolidationItemsAxis")
        if not consolidation_axis:
            # Try other common axis names
            for axis_key in dimensions.keys():
                if "consolidation" in axis_key.lower() or "segment" in axis_key.lower():
                    consolidation_axis = dimensions.get(axis_key)
                    break
        
        if consolidation_axis:
            member_value = consolidation_axis.get("value") or consolidation_axis.get("member", "")
            member_lower = str(member_value).lower()
            
            # IMPORTANT: Check for company excluding Ford Credit FIRST (more specific)
            # before checking for Ford Credit (which would match "Company excluding Ford Credit")
            if any(indicator in member_lower for indicator in [
                "company excluding ford credit",
                "company excl ford credit",
                "excluding ford credit",
                "excl ford credit",
            ]):
                return DebtSegment.COMPANY_EXCL_FORD_CREDIT
            
            # Check for automotive/corporate (company excl. Ford Credit)
            if any(indicator in member_lower for indicator in [
                "automotive",
                "automotive and corporate",
                "corporate",
            ]):
                # But exclude if it also mentions Ford Credit
                if "ford credit" not in member_lower:
                    return DebtSegment.COMPANY_EXCL_FORD_CREDIT
            
            # Check for Ford Credit indicators (after checking company excl.)
            if any(indicator in member_lower for indicator in [
                "ford credit",
                "fordcredit",
                "credit segment",
                "financial services",
                "financing",
                "finance company",
            ]):
                return DebtSegment.FORD_CREDIT
            
            # If it's a dimension but doesn't match known patterns, it's other
            return DebtSegment.OTHER
    
    # Check segment field (alternative format)
    if segment_info:
        if isinstance(segment_info, dict):
            member = segment_info.get("member") or segment_info.get("value", "")
            member_lower = str(member).lower()
            
            # Check company excl. Ford Credit first (more specific)
            if any(indicator in member_lower for indicator in [
                "company excluding ford credit",
                "company excl ford credit",
                "excluding ford credit",
            ]):
                return DebtSegment.COMPANY_EXCL_FORD_CREDIT
            
            # Check automotive/corporate
            if any(indicator in member_lower for indicator in [
                "automotive",
                "corporate",
            ]):
                if "ford credit" not in member_lower:
                    return DebtSegment.COMPANY_EXCL_FORD_CREDIT
            
            # Check Ford Credit
            if any(indicator in member_lower for indicator in [
                "ford credit",
                "fordcredit",
                "credit segment",
                "financial services",
            ]):
                return DebtSegment.FORD_CREDIT
            
            return DebtSegment.OTHER
    
    # Check tag/label for segment indicators (fallback)
    if tag or label:
        text = f"{tag} {label}".lower().replace(" ", "").replace("-", "").replace("_", "")
        
        # IMPORTANT: Check company excl. Ford Credit FIRST (more specific)
        if any(indicator in text for indicator in [
            "companyexclfordcredit",
            "companyexcludefordcredit",
            "exclfordcredit",
            "automotivedebt",
        ]):
            return DebtSegment.COMPANY_EXCL_FORD_CREDIT
        
        # Ford Credit indicators in tag/label (after checking company excl.)
        if any(indicator in text for indicator in [
            "fordcredit",
            "fordcreditdebt",
            "creditdebt",
        ]):
            return DebtSegment.FORD_CREDIT
    
    # Default to consolidated if no dimensions/segments found
    return DebtSegment.CONSOLIDATED


# ============================================================================
# STEP 5: OUTPUT STRUCTURE
# ============================================================================

@dataclass
class DebtFact:
    """A single debt-related XBRL fact with full context."""
    tag: str
    label: str
    value: float
    unit: str
    period_end: str  # ISO date (YYYY-MM-DD)
    segment: DebtSegment
    context_id: Optional[str] = None  # XBRL context ID if available
    period_start: Optional[str] = None  # For duration facts
    is_instant: bool = True  # True for balance sheet (instant), False for duration
    namespace: str = "us-gaap"  # Taxonomy namespace
    is_standard_gaap_tag: bool = True
    filing_form: Optional[str] = None  # e.g., "10-K"
    filing_date: Optional[str] = None  # Filing date
    accession: Optional[str] = None  # SEC accession number


@dataclass
class DebtExtractionResult:
    """Complete debt extraction result with all facts and metadata."""
    company: str
    cik: int
    fiscal_year: Optional[int] = None
    report_date: Optional[str] = None  # Primary report date if filtering by period
    facts: List[DebtFact] = None
    
    def __post_init__(self):
        if self.facts is None:
            self.facts = []
    
    def get_facts_by_segment(self, segment: DebtSegment) -> List[DebtFact]:
        """Get all facts for a specific segment."""
        return [f for f in self.facts if f.segment == segment]
    
    def get_consolidated_facts(self) -> List[DebtFact]:
        """Get all consolidated facts."""
        return self.get_facts_by_segment(DebtSegment.CONSOLIDATED)
    
    def get_ford_credit_facts(self) -> List[DebtFact]:
        """Get all Ford Credit facts."""
        return self.get_facts_by_segment(DebtSegment.FORD_CREDIT)
    
    def get_company_excl_ford_credit_facts(self) -> List[DebtFact]:
        """Get all Company excluding Ford Credit facts."""
        return self.get_facts_by_segment(DebtSegment.COMPANY_EXCL_FORD_CREDIT)


# ============================================================================
# STEP 3 & 5: DEBT FACT EXTRACTION
# ============================================================================

def _is_debt_tag(tag: str, label: Optional[str] = None) -> bool:
    """
    Check if a tag/label represents a debt-related fact.
    
    Args:
        tag: XBRL tag name (may include namespace prefix)
        label: Optional human-readable label
        
    Returns:
        True if the tag appears to be debt-related
    """
    # Remove namespace prefix if present
    tag_clean = tag.split(":")[-1] if ":" in tag else tag
    tag_lower = tag_clean.lower()
    
    # Check core standard tags
    if tag_clean in DEBT_TAGS_CORE:
        return True
    
    # Check for debt keywords in tag name
    for keyword in DEBT_TAG_NAME_KEYWORDS:
        if keyword in tag_lower:
            return True
    
    # Check label if provided (normalize spaces for matching)
    if label:
        label_lower = label.lower().replace(" ", "").replace("-", "").replace("_", "")
        for keyword in DEBT_TAG_NAME_KEYWORDS:
            if keyword in label_lower:
                return True
    
    return False


def _is_monetary_fact(record: Dict[str, Any]) -> bool:
    """Check if a fact record represents a monetary value."""
    unit = record.get("_unit") or record.get("unit", "")
    unit_lower = str(unit).lower()
    
    # Monetary units
    if unit_lower in ("usd", "eur", "gbp", "jpy", "cny", "cad", "aud"):
        return True
    
    # Exclude non-monetary units
    if unit_lower in ("shares", "pure", "xbrli:shares", "xbrli:pure"):
        return False
    
    # If no unit but value is numeric, assume monetary
    if not unit and isinstance(record.get("val"), (int, float)):
        return True
    
    return False


def extract_debt_facts_from_instance(
    facts_payload: Dict[str, Any],
    report_date: Optional[str] = None,
) -> DebtExtractionResult:
    """
    Extract all debt-related facts from an XBRL instance (Company Facts format).
    
    This function:
    1. Iterates over all facts in the instance
    2. Filters for debt-related tags (standard + extensions)
    3. Classifies each fact by segment
    4. Returns structured result with all facts
    
    Args:
        facts_payload: Full company facts payload from EDGAR API
            Structure: {"cik": "...", "entityName": "...", "facts": {...}}
        report_date: Optional period end date to filter by (YYYY-MM-DD format)
            If None, includes all periods
        
    Returns:
        DebtExtractionResult with all matching debt facts
    """
    # Extract company metadata
    company_name = facts_payload.get("entityName", "Unknown Company")
    cik_str = facts_payload.get("cik", "")
    try:
        cik = int(cik_str) if cik_str else 0
    except (ValueError, TypeError):
        cik = 0
    
    # Extract fiscal year and report date from payload if available
    fiscal_year = None
    if report_date:
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(report_date)
            fiscal_year = dt.year
        except (ValueError, TypeError):
            pass
    
    result = DebtExtractionResult(
        company=company_name,
        cik=cik,
        fiscal_year=fiscal_year,
        report_date=report_date,
    )
    
    # Get facts root
    facts_root = facts_payload.get("facts", {})
    if not facts_root:
        logger.warning(f"No 'facts' section found in company facts payload for CIK {cik}")
        return result
    
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
            
            # Flatten all unit records (using existing utility)
            all_records = flatten_units(units)
            
            # Process each record
            for record in all_records:
                # Filter by period if specified
                if report_date:
                    end = record.get("end")
                    if end != report_date:
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
                is_instant = (not start or start == end)
                
                # Classify segment
                segment = classify_debt_segment(record, tag, label)
                
                # Build DebtFact
                debt_fact = DebtFact(
                    tag=tag,
                    label=label,
                    value=value,
                    unit=record.get("_unit") or record.get("unit") or "USD",
                    period_end=end or "",
                    period_start=start,
                    is_instant=is_instant,
                    segment=segment,
                    context_id=record.get("accn"),  # Use accession as context ID
                    namespace=taxonomy_name,
                    is_standard_gaap_tag=is_standard_gaap,
                    filing_form=record.get("form"),
                    filing_date=record.get("filed"),
                    accession=record.get("accn"),
                )
                
                result.facts.append(debt_fact)
    
    # Sort facts by segment, then tag, then period
    result.facts.sort(key=lambda f: (
        f.segment.value,
        f.tag,
        f.period_end,
    ))
    
    # Log summary
    consolidated_count = len(result.get_consolidated_facts())
    ford_credit_count = len(result.get_ford_credit_facts())
    company_excl_count = len(result.get_company_excl_ford_credit_facts())
    other_count = len(result.get_facts_by_segment(DebtSegment.OTHER))
    
    logger.info(
        f"Extracted {len(result.facts)} debt facts for {company_name} "
        f"(CIK: {cik}): "
        f"{consolidated_count} consolidated, "
        f"{ford_credit_count} Ford Credit, "
        f"{company_excl_count} Company excl. Ford Credit, "
        f"{other_count} other"
    )
    
    return result


# ============================================================================
# STEP 6: HIGH-LEVEL WRAPPER
# ============================================================================

def extract_debt_for_filing(
    cik: int,
    report_date: Optional[str] = None,
    edgar_client: Optional[Any] = None,
) -> DebtExtractionResult:
    """
    High-level helper that loads XBRL instance and extracts debt facts.
    
    This function:
    1. Loads the XBRL instance for the given CIK (from EDGAR or cached)
    2. Calls extract_debt_facts_from_instance()
    
    Args:
        cik: Company CIK (Central Index Key)
        report_date: Optional period end date to filter by (YYYY-MM-DD)
        edgar_client: Optional EdgarClient instance (creates new if not provided)
        
    Returns:
        DebtExtractionResult with all debt facts
    """
    # Import here to avoid circular dependencies
    from app.services.ingestion.clients import EdgarClient
    
    client = edgar_client or EdgarClient()
    
    # Fetch company facts from EDGAR
    logger.info(f"Fetching company facts for CIK {cik}")
    facts_payload = client.get_company_facts(cik)
    
    # Extract debt facts
    return extract_debt_facts_from_instance(facts_payload, report_date=report_date)


def extract_debt_for_ticker(
    ticker: str,
    report_date: Optional[str] = None,
    edgar_client: Optional[Any] = None,
) -> DebtExtractionResult:
    """
    Extract debt facts for a company by ticker symbol.
    
    Args:
        ticker: Stock ticker symbol (e.g., "F")
        report_date: Optional period end date to filter by (YYYY-MM-DD)
        edgar_client: Optional EdgarClient instance
        
    Returns:
        DebtExtractionResult with all debt facts
        
    Raises:
        RuntimeError if ticker not found
    """
    from app.services.ingestion.clients import EdgarClient
    
    client = edgar_client or EdgarClient()
    
    # Get CIK from ticker
    logger.info(f"Looking up CIK for ticker {ticker}")
    cik_map = client.get_cik_map()
    cik = cik_map.get(ticker.upper())
    
    if not cik:
        raise RuntimeError(f"CIK not found for ticker: {ticker}")
    
    return extract_debt_for_filing(cik, report_date=report_date, edgar_client=client)

