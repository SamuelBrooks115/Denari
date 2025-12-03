"""
rule_based_tagger.py — Rule-based tagging for Ford financial facts.

DEPRECATED — This module has been replaced by the FMP-based pipeline.
See app/tagging/fmp_tagger.py for the new implementation.

This module applies Ford-specific tagging rules to assign calculation tags
to facts based on concept QNames, labels, statement types, and dimensions.

TODO: This can be augmented or overridden by an LLM-based classifier later.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from app.core.logging import get_logger
from app.tagging.calc_tags import CalcTag, VALID_CALC_TAGS

logger = get_logger(__name__)


@dataclass
class TaggedFact:
    """
    Fact with assigned calculation tags.
    
    This is a subset of FactRecord with calc_tags added.
    """
    fact_id: str
    concept_qname: str
    standard_label: Optional[str]
    statement_type: Optional[str]
    value_typed: Optional[float]
    period_end: Optional[str]
    dimensions: Dict[str, str]
    presentation: List[Dict[str, Any]]
    calc_tags: List[str] = field(default_factory=list)


def _normalize_label(label: Optional[str]) -> str:
    """
    Normalize label for matching (lowercase, strip).
    
    Args:
        label: Label string or None
        
    Returns:
        Normalized label string (empty string if None)
    """
    if not label:
        return ""
    return str(label).lower().strip()


def _label_contains(label: Optional[str], keywords: List[str]) -> bool:
    """
    Check if label contains any of the given keywords.
    
    Args:
        label: Label string or None
        keywords: List of keywords to search for
        
    Returns:
        True if label contains any keyword
    """
    normalized = _normalize_label(label)
    if not normalized:
        return False
    
    return any(keyword.lower() in normalized for keyword in keywords)


def assign_tags_for_fact(fact: Dict[str, Any]) -> TaggedFact:
    """
    Assign calculation tags to a fact based on Ford-specific rules.
    
    Args:
        fact: Fact dictionary from fact table JSON
        
    Returns:
        TaggedFact with calc_tags populated
    """
    calc_tags: List[str] = []
    
    statement_type = fact.get("statement_type")
    concept_qname = fact.get("concept_qname", "")
    standard_label = fact.get("standard_label")
    terse_label = fact.get("terse_label")
    dimensions = fact.get("dimensions", {})
    
    # Only tag facts with valid statement types
    if statement_type not in ["IS", "BS", "CF"]:
        return TaggedFact(
            fact_id=fact.get("fact_id", ""),
            concept_qname=concept_qname,
            standard_label=standard_label,
            statement_type=statement_type,
            value_typed=fact.get("value_typed"),
            period_end=fact.get("period_end"),
            dimensions=dimensions,
            presentation=fact.get("presentation", []),
            calc_tags=[],
        )
    
    # Use standard_label or terse_label for matching
    label = standard_label or terse_label
    
    # INCOME STATEMENT TAGGING
    if statement_type == "IS":
        # Revenue
        if concept_qname in {
            "us-gaap:Revenues",
            "us-gaap:SalesRevenueNet",
            "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
        } or _label_contains(label, ["total revenues", "total revenue", "net sales"]):
            calc_tags.append(CalcTag.REVENUE_TOTAL.value)
        
        # COGS
        if concept_qname == "us-gaap:CostOfGoodsAndServicesSold" or _label_contains(
            label, ["cost of sales", "cost of goods sold", "cost of revenue"]
        ):
            calc_tags.append(CalcTag.COGS.value)
        
        # Operating expenses
        if _label_contains(
            label,
            ["selling", "administrative", "sg&a", "sga", "engineering", "research and development", "r&d"],
        ):
            calc_tags.append(CalcTag.OPERATING_EXPENSE.value)
        
        # Gross profit
        if _label_contains(label, ["gross profit"]):
            calc_tags.append(CalcTag.GROSS_PROFIT.value)
        
        # Operating income
        if concept_qname == "us-gaap:OperatingIncomeLoss" or _label_contains(
            label, ["operating income", "operating earnings"]
        ):
            calc_tags.append(CalcTag.OPERATING_INCOME.value)
        
        # Depreciation & amortization
        if _label_contains(label, ["depreciation", "amortization", "depreciation and amortization"]):
            calc_tags.append(CalcTag.DEPRECIATION_AMORTIZATION.value)
        
        # Pre-tax income
        if concept_qname in {
            "us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxes",
            "us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
        } or _label_contains(label, ["income before income taxes", "income before taxes"]):
            calc_tags.append(CalcTag.PRE_TAX_INCOME.value)
        
        # Income tax expense
        if concept_qname == "us-gaap:IncomeTaxExpenseBenefit" or _label_contains(
            label, ["provision for income taxes", "income tax expense", "income tax benefit"]
        ):
            calc_tags.append(CalcTag.INCOME_TAX_EXPENSE.value)
        
        # Net income
        if concept_qname in {"us-gaap:NetIncomeLoss", "us-gaap:ProfitLoss"} or _label_contains(
            label, ["net income", "net earnings", "net loss"]
        ):
            calc_tags.append(CalcTag.NET_INCOME.value)
    
    # BALANCE SHEET TAGGING
    elif statement_type == "BS":
        # PP&E
        if concept_qname == "us-gaap:PropertyPlantAndEquipmentNet" or _label_contains(
            label, ["property, plant and equipment", "ppe", "property plant equipment"]
        ):
            calc_tags.append(CalcTag.PPE_NET.value)
        
        # Inventory
        if concept_qname == "us-gaap:InventoryNet" or _label_contains(label, ["inventories", "inventory"]):
            calc_tags.append(CalcTag.INVENTORY.value)
        
        # Accounts payable
        if concept_qname == "us-gaap:AccountsPayableCurrent" or _label_contains(
            label, ["accounts payable", "trade payables"]
        ):
            calc_tags.append(CalcTag.ACCOUNTS_PAYABLE.value)
        
        # Accounts receivable
        if concept_qname == "us-gaap:AccountsReceivableNetCurrent" or _label_contains(
            label, ["accounts receivable", "trade receivables"]
        ):
            calc_tags.append(CalcTag.ACCOUNTS_RECEIVABLE.value)
        
        # Accrued expenses
        if "AccruedLiabilities" in concept_qname or _label_contains(
            label, ["accrued", "accrued liabilities", "accrued expenses"]
        ):
            calc_tags.append(CalcTag.ACCRUED_EXPENSES.value)
        
        # Debt components
        if concept_qname in {
            "us-gaap:DebtCurrent",
            "us-gaap:LongTermDebtNoncurrent",
            "us-gaap:LongTermDebtAndCapitalLeaseObligations",
        } or _label_contains(label, ["debt", "borrowings", "notes payable"]):
            calc_tags.append(CalcTag.TOTAL_DEBT_COMPONENT.value)
    
    # CASH FLOW TAGGING
    elif statement_type == "CF":
        # Share repurchases
        if concept_qname in {
            "us-gaap:PaymentsForRepurchaseOfCommonStock",
            "us-gaap:PaymentsForRepurchaseOfEquity",
        } or _label_contains(label, ["repurchase of common stock", "share repurchase", "stock repurchase"]):
            calc_tags.append(CalcTag.SHARE_REPURCHASES.value)
        
        # Dividends paid
        if concept_qname in {
            "us-gaap:PaymentsOfDividends",
            "us-gaap:PaymentsOfDividendsCommonStock",
        } or _label_contains(label, ["dividends paid", "cash dividends"]):
            calc_tags.append(CalcTag.DIVIDENDS_PAID.value)
    
    # Validate all tags are in vocabulary
    validated_tags = [tag for tag in calc_tags if tag in VALID_CALC_TAGS]
    invalid_tags = [tag for tag in calc_tags if tag not in VALID_CALC_TAGS]
    
    if invalid_tags:
        logger.warning(
            f"Invalid calc_tags for fact {fact.get('fact_id')}: {invalid_tags}. "
            f"Valid tags: {sorted(VALID_CALC_TAGS)}"
        )
    
    return TaggedFact(
        fact_id=fact.get("fact_id", ""),
        concept_qname=concept_qname,
        standard_label=standard_label,
        statement_type=statement_type,
        value_typed=fact.get("value_typed"),
        period_end=fact.get("period_end"),
        dimensions=dimensions,
        presentation=fact.get("presentation", []),
        calc_tags=validated_tags,
    )


def tag_fact_table(input_json: str, output_json: str) -> None:
    """
    Read fact table JSON, apply tagging, and write tagged facts JSON.
    
    Args:
        input_json: Path to input fact table JSON
        output_json: Path to output tagged facts JSON
    """
    logger.info(f"Loading fact table from: {input_json}")
    
    input_path = Path(input_json)
    if not input_path.exists():
        raise FileNotFoundError(f"Input JSON file not found: {input_json}")
    
    with input_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    
    facts = data.get("facts", [])
    if not facts:
        logger.warning("No facts found in input JSON")
    
    logger.info(f"Tagging {len(facts)} facts...")
    
    tagged_facts = []
    for fact in facts:
        tagged = assign_tags_for_fact(fact)
        tagged_facts.append(asdict(tagged))
    
    # Count tagged facts
    tagged_count = sum(1 for f in tagged_facts if f.get("calc_tags"))
    logger.info(f"Tagged {tagged_count}/{len(tagged_facts)} facts with calc tags")
    
    # Build output structure
    output_data = {
        "source": input_json,
        "fiscal_year": data.get("fiscal_year"),
        "total_facts": len(tagged_facts),
        "facts_tagged": tagged_facts,
    }
    
    # Write JSON
    output_path = Path(output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Wrote {len(tagged_facts)} tagged facts to {output_json}")

