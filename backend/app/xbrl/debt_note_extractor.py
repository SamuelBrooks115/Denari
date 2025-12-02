"""
debt_note_extractor.py — Extract Note 18 (Debt and Commitments) from Arelle ModelXbrl.

This module extracts detailed debt information from Note 18 disclosure tables,
including segment breakdowns (Company excluding Ford Credit, Ford Credit, Consolidated)
and maturity buckets (within one year, after one year, etc.).

Key features:
- Finds Note 18 role using role definitions
- Traverses presentation linkbase to identify table structure
- Extracts facts with segment and maturity dimensions
- Aggregates into standardized totals

Does NOT depend on:
- EDGAR APIs
- Company Facts API
- HTTP calls

Works purely on Arelle ModelXbrl objects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger
from app.xbrl.arelle_loader import find_role_by_keywords

logger = get_logger(__name__)


# ============================================================================
# STEP 4: DEBT NOTE EXTRACTION DATA STRUCTURES
# ============================================================================

@dataclass
class DebtCell:
    """
    A single cell in the Note 18 debt table.
    
    Represents one debt line item (e.g., "Unsecured Debt") for a specific
    segment and maturity bucket.
    """
    line_item: str  # Normalized name, e.g., "unsecured_debt", "asset_backed_debt"
    raw_concept: str  # XBRL concept QName
    segment: str  # "company_excl_ford_credit", "ford_credit", "consolidated", "other"
    maturity_bucket: str  # "within_one_year", "after_one_year", "1-3_years", etc.
    value: float
    unit: str
    period_end: str  # ISO date (YYYY-MM-DD)
    context_id: Optional[str] = None
    label: Optional[str] = None  # Human-readable label from concept


@dataclass
class Note18DebtTable:
    """
    Complete Note 18 debt table with all cells and aggregations.
    """
    company: str
    cik: str
    fiscal_year: int
    period_end: str
    cells: List[DebtCell] = field(default_factory=list)
    
    def get_cells_by_segment(
        self,
        segment: str,
    ) -> List[DebtCell]:
        """Get all cells for a specific segment."""
        return [c for c in self.cells if c.segment == segment]
    
    def get_cells_by_maturity(
        self,
        maturity_bucket: str,
    ) -> List[DebtCell]:
        """Get all cells for a specific maturity bucket."""
        return [c for c in self.cells if c.maturity_bucket == maturity_bucket]
    
    def aggregate_by_segment_and_maturity(self) -> Dict[str, Dict[str, float]]:
        """
        Aggregate cells by segment and maturity bucket.
        
        Returns:
            {
                "segment": {
                    "maturity_bucket": total_value,
                    ...
                },
                ...
            }
        """
        result: Dict[str, Dict[str, float]] = {}
        
        for cell in self.cells:
            if cell.segment not in result:
                result[cell.segment] = {}
            if cell.maturity_bucket not in result[cell.segment]:
                result[cell.segment][cell.maturity_bucket] = 0.0
            result[cell.segment][cell.maturity_bucket] += cell.value
        
        return result
    
    def get_total_by_segment(self, segment: str) -> float:
        """Get total debt for a specific segment."""
        cells = self.get_cells_by_segment(segment)
        return sum(c.value for c in cells)
    
    def get_total_by_maturity(self, maturity_bucket: str) -> float:
        """Get total debt for a specific maturity bucket."""
        cells = self.get_cells_by_maturity(maturity_bucket)
        return sum(c.value for c in cells)
    
    def get_consolidated_total(self) -> float:
        """Get total consolidated debt."""
        return self.get_total_by_segment("consolidated")


# ============================================================================
# SEGMENT AND MATURITY CLASSIFICATION
# ============================================================================

def classify_segment_from_dimensions(context: Any) -> str:
    """
    Classify segment from XBRL context dimensions.
    
    Args:
        context: Arelle context object
        
    Returns:
        Segment string: "consolidated", "company_excl_ford_credit", "ford_credit", "other"
    """
    if not context:
        return "consolidated"
    
    # Check for segment dimensions
    if hasattr(context, "segDimValues") and context.segDimValues:
        for dim in context.segDimValues:
            dim_str = str(dim).lower()
            
            # Check for company excluding Ford Credit (more specific first)
            if any(indicator in dim_str for indicator in [
                "company excluding ford credit",
                "company excl ford credit",
                "excluding ford credit",
                "excl ford credit",
            ]):
                return "company_excl_ford_credit"
            
            # Check for automotive/corporate (company excl. Ford Credit)
            if any(indicator in dim_str for indicator in [
                "automotive",
                "corporate",
            ]):
                if "ford credit" not in dim_str:
                    return "company_excl_ford_credit"
            
            # Check for Ford Credit
            if any(indicator in dim_str for indicator in [
                "ford credit",
                "fordcredit",
                "credit segment",
                "financial services",
            ]):
                return "ford_credit"
        
        # If we have dimensions but don't match known patterns, it's "other"
        return "other"
    
    # No dimensions = consolidated
    return "consolidated"


def classify_maturity_from_dimensions(context: Any) -> str:
    """
    Classify maturity bucket from XBRL context dimensions.
    
    Args:
        context: Arelle context object
        
    Returns:
        Maturity bucket string: "within_one_year", "after_one_year", "1-3_years", etc.
    """
    if not context:
        return "unknown"
    
    # Check for maturity/term dimensions
    if hasattr(context, "segDimValues") and context.segDimValues:
        for dim in context.segDimValues:
            dim_str = str(dim).lower()
            
            # Common maturity patterns
            if any(indicator in dim_str for indicator in [
                "within one year",
                "within 1 year",
                "current",
                "due within",
                "payable within",
            ]):
                return "within_one_year"
            
            if any(indicator in dim_str for indicator in [
                "after one year",
                "after 1 year",
                "noncurrent",
                "long-term",
                "longterm",
            ]):
                return "after_one_year"
            
            # Specific year ranges
            if "1-3 years" in dim_str or "1 to 3" in dim_str:
                return "1-3_years"
            if "3-5 years" in dim_str or "3 to 5" in dim_str:
                return "3-5_years"
            if "5-10 years" in dim_str or "5 to 10" in dim_str:
                return "5-10_years"
            if "over 10 years" in dim_str or "after 10" in dim_str:
                return "over_10_years"
    
    # Default: try to infer from concept name or label
    return "unknown"


def normalize_line_item_name(concept_qname: str, label: Optional[str] = None) -> str:
    """
    Normalize a debt line item concept to a standard name.
    
    Args:
        concept_qname: XBRL concept QName
        label: Optional human-readable label
        
    Returns:
        Normalized line item name (e.g., "unsecured_debt", "asset_backed_debt")
    """
    text = f"{concept_qname} {label}".lower().replace(" ", "").replace("-", "").replace("_", "")
    
    # Map common patterns to normalized names
    if "unsecured" in text and "debt" in text:
        return "unsecured_debt"
    if "assetbacked" in text or "asset-backed" in text or "asset backed" in text:
        return "asset_backed_debt"
    if "secured" in text and "debt" in text:
        return "secured_debt"
    if "convertible" in text and "debt" in text:
        return "convertible_debt"
    if "commercialpaper" in text or "commercial paper" in text:
        return "commercial_paper"
    if "revolving" in text or "revolver" in text:
        return "revolving_credit"
    if "notespayable" in text or "notes payable" in text:
        return "notes_payable"
    if "financelease" in text or "finance lease" in text:
        return "finance_lease_liabilities"
    if "other" in text and "debt" in text:
        return "other_debt"
    
    # Default: use concept name (cleaned)
    concept_name = concept_qname.split(":")[-1] if ":" in concept_qname else concept_qname
    return concept_name.lower().replace(" ", "_").replace("-", "_")


# ============================================================================
# NOTE 18 EXTRACTION
# ============================================================================

def find_note18_role(model_xbrl: Any) -> Optional[str]:
    """
    Find the role URI for Note 18 - Debt and Commitments.
    
    Args:
        model_xbrl: Arelle ModelXbrl object
        
    Returns:
        Role URI if found, None otherwise
    """
    # Try multiple keyword combinations
    keywords_combinations = [
        ["debt", "commitments"],
        ["debt", "commitment"],
        ["long-term", "debt"],
        ["debt", "obligations"],
    ]
    
    for keywords in keywords_combinations:
        role_uri = find_role_by_keywords(model_xbrl, keywords)
        if role_uri:
            logger.info(f"Found Note 18 role: {role_uri} (keywords: {keywords})")
            return role_uri
    
    logger.warning("Could not find Note 18 role using keyword search")
    return None


def extract_facts_from_role(
    model_xbrl: Any,
    role_uri: str,
    fiscal_year: int,
) -> List[Any]:
    """
    Extract all facts from a specific role (e.g., Note 18).
    
    Args:
        model_xbrl: Arelle ModelXbrl object
        role_uri: Role URI to filter facts by
        fiscal_year: Target fiscal year
        
    Returns:
        List of Arelle fact objects
    """
    facts_found = []
    
    # Get presentation relationships for this role
    # Arelle stores relationships in modelRelationshipSet
    if not hasattr(model_xbrl, "relationshipSet"):
        logger.warning("ModelXbrl does not have relationshipSet attribute")
        return facts_found
    
    # Try to get presentation linkbase relationships
    try:
        # Get all facts and filter by role
        # In Arelle, facts don't directly have roles, but we can use presentation relationships
        # to find which concepts are in this role, then find facts for those concepts
        
        # For now, we'll search all facts and check if they're debt-related
        # and match the fiscal year
        for fact in model_xbrl.facts:
            if not fact.concept:
                continue
            
            # Check if this fact is debt-related
            concept_qname = str(fact.concept.qname) if hasattr(fact.concept, "qname") else ""
            concept_lower = concept_qname.lower()
            
            if not any(keyword in concept_lower for keyword in [
                "debt", "borrowing", "notespayable", "lease", "obligation"
            ]):
                continue
            
            # Check period
            period_end = _get_period_end(fact.context)
            if not _matches_fiscal_year(period_end, fiscal_year):
                continue
            
            facts_found.append(fact)
    
    except Exception as e:
        logger.error(f"Error extracting facts from role {role_uri}: {e}")
    
    return facts_found


def _get_period_end(context: Any) -> Optional[str]:
    """Extract period end date from Arelle context."""
    if not context:
        return None
    
    if hasattr(context, "instantDatetime") and context.instantDatetime:
        return context.instantDatetime.date().isoformat()
    
    if hasattr(context, "endDatetime") and context.endDatetime:
        return context.endDatetime.date().isoformat()
    
    return None


def _matches_fiscal_year(period_end: Optional[str], fiscal_year: int) -> bool:
    """Check if period end matches fiscal year."""
    if not period_end:
        return False
    
    try:
        date_obj = datetime.fromisoformat(period_end).date()
        return date_obj.year == fiscal_year
    except (ValueError, TypeError):
        return False


def _extract_fact_value(fact: Any) -> Optional[float]:
    """Extract numeric value from Arelle fact."""
    if not fact:
        return None
    
    try:
        value = fact.xValue
        if value is None:
            return None
        
        if isinstance(value, (int, float)):
            return float(value)
        
        return float(str(value))
    
    except (ValueError, TypeError, AttributeError):
        return None


def extract_note18_debt(
    model_xbrl: Any,
    fiscal_year: int,
    company_name: str = "Unknown Company",
    cik: str = "",
) -> Note18DebtTable:
    """
    Extract Note 18 - Debt and Commitments from Arelle ModelXbrl.
    
    This function:
    1. Finds the Note 18 role
    2. Extracts all debt-related facts from that role
    3. Classifies each fact by segment and maturity
    4. Creates DebtCell objects
    5. Aggregates into Note18DebtTable
    
    Args:
        model_xbrl: Arelle ModelXbrl object
        fiscal_year: Target fiscal year (e.g., 2024)
        company_name: Company name (for metadata)
        cik: Company CIK (for metadata)
        
    Returns:
        Note18DebtTable with all extracted debt cells
    """
    logger.info(f"Extracting Note 18 debt for fiscal year {fiscal_year}")
    
    # Find Note 18 role
    note18_role = find_note18_role(model_xbrl)
    if not note18_role:
        logger.warning("Could not find Note 18 role, searching all debt facts")
        # Fall back to searching all debt facts
    
    # Extract facts (either from role or all debt facts)
    if note18_role:
        facts = extract_facts_from_role(model_xbrl, note18_role, fiscal_year)
    else:
        # Fallback: search all facts for debt-related concepts
        facts = []
        for fact in model_xbrl.facts:
            if not fact.concept:
                continue
            
            concept_qname = str(fact.concept.qname) if hasattr(fact.concept, "qname") else ""
            concept_lower = concept_qname.lower()
            
            # Check if debt-related
            if not any(keyword in concept_lower for keyword in [
                "debt", "borrowing", "notespayable", "lease", "obligation"
            ]):
                continue
            
            # Check period
            period_end = _get_period_end(fact.context)
            if not _matches_fiscal_year(period_end, fiscal_year):
                continue
            
            facts.append(fact)
    
    logger.info(f"Found {len(facts)} debt-related facts for Note 18")
    
    # Convert facts to DebtCells
    cells: List[DebtCell] = []
    period_end = None
    
    for fact in facts:
        # Extract value
        value = _extract_fact_value(fact)
        if value is None:
            continue
        
        # Get concept info
        concept = fact.concept
        concept_qname = str(concept.qname) if concept and hasattr(concept, "qname") else ""
        label = concept.label() if concept and hasattr(concept, "label") else None
        
        # Normalize line item name
        line_item = normalize_line_item_name(concept_qname, label)
        
        # Classify segment and maturity
        segment = classify_segment_from_dimensions(fact.context)
        maturity_bucket = classify_maturity_from_dimensions(fact.context)
        
        # Get period end
        fact_period_end = _get_period_end(fact.context)
        if fact_period_end:
            period_end = fact_period_end
        
        # Get unit
        unit = "USD"
        if fact.unitID and hasattr(model_xbrl, "units"):
            unit_obj = model_xbrl.units.get(fact.unitID)
            if unit_obj:
                if hasattr(unit_obj, "measures"):
                    measures = unit_obj.measures
                    if measures and len(measures) > 0:
                        unit = str(measures[0][0]) if isinstance(measures[0], tuple) else str(measures[0])
        
        # Get context ID
        context_id = fact.contextID if hasattr(fact, "contextID") else None
        
        # Create DebtCell
        cell = DebtCell(
            line_item=line_item,
            raw_concept=concept_qname,
            segment=segment,
            maturity_bucket=maturity_bucket,
            value=value,
            unit=unit,
            period_end=fact_period_end or "",
            context_id=context_id,
            label=label,
        )
        
        cells.append(cell)
    
    # Use most common period_end if we have cells
    if cells and not period_end:
        period_ends = [c.period_end for c in cells if c.period_end]
        if period_ends:
            period_end = max(set(period_ends), key=period_ends.count)
    
    # Create Note18DebtTable
    table = Note18DebtTable(
        company=company_name,
        cik=cik,
        fiscal_year=fiscal_year,
        period_end=period_end or f"{fiscal_year}-12-31",
        cells=cells,
    )
    
    # Log summary
    consolidated_total = table.get_consolidated_total()
    company_excl_total = table.get_total_by_segment("company_excl_ford_credit")
    ford_credit_total = table.get_total_by_segment("ford_credit")
    
    logger.info(
        f"Note 18 extraction complete: "
        f"{len(cells)} cells, "
        f"Consolidated: ${consolidated_total:,.0f}, "
        f"Company excl. Ford Credit: ${company_excl_total:,.0f}, "
        f"Ford Credit: ${ford_credit_total:,.0f}"
    )
    
    return table

