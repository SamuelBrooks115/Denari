"""
fact_table_extractor.py — Extract normalized fact table from Arelle XBRL instance.

DEPRECATED — This module has been replaced by the FMP-based pipeline.
See app/data/fmp_client.py and app/data/fmp_normalizer.py for the new implementation.

This module extracts all facts from an XBRL/iXBRL instance and builds a normalized
fact table with rich metadata for each fact, including concept metadata, labels,
values, context, dimensions, and presentation information.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from decimal import Decimal
from typing import Any, Dict, List, Optional

from arelle import Cntlr, ModelManager, FileSource


@dataclass
class FactRecord:
    # --- Required / non-default fields (must come first) ---
    fact_id: str
    concept_qname: Optional[str]
    concept_local_name: Optional[str]
    namespace_uri: Optional[str]

    is_numeric: bool
    is_abstract: bool
    balance: Optional[str]
    period_type: Optional[str]

    standard_label: Optional[str]
    terse_label: Optional[str]
    documentation_label: Optional[str]

    value_raw: Optional[str]
    value_typed: Optional[float]
    decimals: Optional[str]
    precision: Optional[str]

    unit_id: Optional[str]

    context_id: Optional[str]
    entity_scheme: Optional[str]
    entity_identifier: Optional[str]
    period_start: Optional[str]
    period_end: Optional[str]
    instant: Optional[str]

    # --- Defaulted / collection fields (must come after non-defaults) ---
    unit_measures_numerator: List[str] = field(default_factory=list)
    unit_measures_denominator: List[str] = field(default_factory=list)
    dimensions: Dict[str, str] = field(default_factory=dict)
    presentation: List[Dict[str, Any]] = field(default_factory=list)

    # Derived statement type: "IS", "BS", "CF", or None
    statement_type: Optional[str] = None


def _load_model_xbrl(instance_path: str):
    """
    Load an XBRL/iXBRL instance using Arelle.
    """
    cntlr = Cntlr.Cntlr(logFileName=None)
    model_manager = ModelManager.initialize(cntlr)
    file_source = FileSource.FileSource(instance_path, cntlr)
    model_xbrl = model_manager.load(file_source)
    if model_xbrl is None:
        raise RuntimeError(f"Failed to load XBRL instance from {instance_path}")
    return model_xbrl


def _dimensions_dict(context) -> Dict[str, str]:
    dims: Dict[str, str] = {}
    if not context or not getattr(context, "qnameDims", None):
        return dims

    for dim_qname, dim in context.qnameDims.items():
        member = getattr(dim, "memberQname", None)
        if member is not None:
            dims[str(dim_qname)] = str(member)
        else:
            dims[str(dim_qname)] = "typed_or_unknown_member"
    return dims


def _unit_info(unit) -> (Optional[str], List[str], List[str]):
    if unit is None:
        return None, [], []
    measures = getattr(unit, "measures", None)
    if measures:
        num = [str(m) for m in (measures[0] or [])]
        den = [str(m) for m in (measures[1] or [])]
    else:
        num, den = [], []
    return unit.id, num, den


def _get_labels(concept) -> (Optional[str], Optional[str], Optional[str]):
    if concept is None:
        return None, None, None

    def safe_label(role: Optional[str] = None) -> Optional[str]:
        try:
            if role is None:
                return concept.label()
            return concept.label(role)
        except Exception:
            return None

    std = safe_label()
    terse = safe_label("http://www.xbrl.org/2003/role/terseLabel")
    doc = safe_label("http://www.xbrl.org/2003/role/documentation")
    return std, terse, doc


def _presentation_metadata(model_xbrl, concept) -> List[Dict[str, Any]]:
    """
    For the given concept, gather presentation relationships where it appears as a child.
    """
    results: List[Dict[str, Any]] = []
    if concept is None:
        return results

    pres_rels = model_xbrl.relationshipSet("presentation")
    if pres_rels is None:
        return results

    for rel in pres_rels.toModelObject(concept):
        parent = rel.fromModelObject
        role_uri = rel.linkrole
        preferred = rel.preferredLabel
        try:
            parent_label = parent.label(preferred or "standard") or parent.qname.localName
        except Exception:
            parent_label = parent.qname.localName

        results.append(
            {
                "role_uri": role_uri,
                "parent_concept_qname": str(parent.qname),
                "parent_label": parent_label,
                "order": rel.order,
                "preferred_label_role": preferred,
            }
        )
    return results


def _derive_statement_type(role_uri: Optional[str]) -> Optional[str]:
    if not role_uri:
        return None
    ru = role_uri.lower()
    if "incom" in ru or "operations" in ru or "earnings" in ru:
        return "IS"
    if "balancesheet" in ru or "financialposition" in ru:
        return "BS"
    if "cashflow" in ru or "cashflowstatement" in ru:
        return "CF"
    return None


def _coerce_typed_value(fact) -> Optional[float]:
    try:
        xval = fact.xValue
    except Exception:
        return None
    if isinstance(xval, (int, float, Decimal)):
        return float(xval)
    return None


def extract_fact_table(instance_path: str, fiscal_year: Optional[int] = None) -> List[FactRecord]:
    """
    Extract all facts from an XBRL/iXBRL instance into a list of FactRecord objects.
    Optionally filter by fiscal_year based on the *end* of the reporting period
    (endDatetime or instantDatetime).
    """
    model_xbrl = _load_model_xbrl(instance_path)
    fact_records: List[FactRecord] = []

    for fact in model_xbrl.facts:
        # Skip nil facts
        if getattr(fact, "isNil", False):
            continue

        concept = getattr(fact, "concept", None)
        context = fact.context

        # Require a context
        if context is None:
            continue

        # ---------------------------
        # Period handling (FIXED)
        # ---------------------------
        period_start_dt = None
        period_end_dt = None
        instant_dt = None

        # Arelle usually exposes these helpers:
        if getattr(context, "isInstantPeriod", False):
            instant_dt = getattr(context, "instantDatetime", None)
            period_end_dt = instant_dt
        elif getattr(context, "isStartEndPeriod", False):
            period_start_dt = getattr(context, "startDatetime", None)
            period_end_dt = getattr(context, "endDatetime", None)

        # Fiscal-year filter uses the *end* date of the period
        if fiscal_year is not None and period_end_dt is not None:
            if getattr(period_end_dt, "year", None) != fiscal_year:
                continue

        # Concept identification
        if concept is not None and getattr(concept, "qname", None) is not None:
            concept_qname = str(concept.qname)
            local_name = concept.qname.localName
            namespace_uri = concept.qname.namespaceURI
        else:
            # Fallback to fact.qname if concept resolution fails
            qn = getattr(fact, "qname", None)
            concept_qname = str(qn) if qn is not None else None
            local_name = qn.localName if qn is not None else None
            namespace_uri = qn.namespaceURI if qn is not None else None

        # Concept metadata (with numeric fallback)
        concept_is_numeric = bool(concept and getattr(concept, "isNumeric", False))
        # typed value fallback
        value_raw = fact.value
        value_typed = _coerce_typed_value(fact)
        is_numeric = concept_is_numeric or isinstance(value_typed, (int, float))

        is_abstract = bool(concept and getattr(concept, "isAbstract", False))
        balance = getattr(concept, "balance", None) if concept else None
        period_type = getattr(concept, "periodType", None) if concept else None

        # Labels
        standard_label, terse_label, documentation_label = _get_labels(concept)

        # Fact decimals / precision
        decimals = getattr(fact, "decimals", None)
        precision = getattr(fact, "precision", None)

        # Unit
        unit_id, unit_num, unit_den = _unit_info(fact.unit)

        # Context: entity
        entity_scheme = None
        entity_identifier = None
        if getattr(context, "entityIdentifier", None):
            entity_scheme, entity_identifier = context.entityIdentifier

        # Dimensions
        dims = _dimensions_dict(context)

        # Presentation metadata
        pres_meta = _presentation_metadata(model_xbrl, concept)
        primary_role = pres_meta[0]["role_uri"] if pres_meta else None
        statement_type = _derive_statement_type(primary_role)

        # ---------------------------
        # Optional: skip "empty" rows
        # ---------------------------
        # If you ONLY care about real, numeric facts, uncomment this:
        #
        # if value_raw is None and value_typed is None:
        #     continue

        record = FactRecord(
            fact_id=fact.id,
            concept_qname=concept_qname,
            concept_local_name=local_name,
            namespace_uri=namespace_uri,
            is_numeric=is_numeric,
            is_abstract=is_abstract,
            balance=balance,
            period_type=period_type,
            standard_label=standard_label,
            terse_label=terse_label,
            documentation_label=documentation_label,
            value_raw=value_raw,
            value_typed=value_typed,
            decimals=decimals,
            precision=precision,
            unit_id=unit_id,
            unit_measures_numerator=unit_num,
            unit_measures_denominator=unit_den,
            context_id=context.id,
            entity_scheme=entity_scheme,
            entity_identifier=entity_identifier,
            period_start=str(period_start_dt) if period_start_dt else None,
            period_end=str(period_end_dt) if period_end_dt else None,
            instant=str(instant_dt) if instant_dt else None,
            dimensions=dims,
            presentation=pres_meta,
            statement_type=statement_type,
        )

        fact_records.append(record)

    return fact_records



def write_fact_table_json(
    instance_path: str,
    output_path: str,
    fiscal_year: Optional[int] = None,
) -> None:
    """
    High-level helper used by build_ford_fact_table.py:
    extracts facts and writes them as a JSON fact table.
    """
    facts = extract_fact_table(instance_path, fiscal_year=fiscal_year)
    data = {
        "instance_path": instance_path,
        "fiscal_year": fiscal_year,
        "facts": [asdict(f) for f in facts],
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
