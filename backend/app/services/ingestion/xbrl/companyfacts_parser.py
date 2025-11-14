"""
Helpers for extracting structured statement data from EDGAR Company Facts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from . import canonical_maps
from .utils import flatten_units, infer_canonical_from_label, pick_for_report_date


@dataclass
class StatementLine:
    amount: Optional[float]
    tag_used: Optional[str]
    unit: Optional[str]
    concept_label: Optional[str]


@dataclass
class PeriodStatements:
    income_statement: Dict[str, StatementLine]
    balance_sheet: Dict[str, StatementLine]
    cash_flow_statement: Dict[str, StatementLine]
    share_data: Dict[str, StatementLine]


def detect_primary_taxonomy(facts: Dict[str, Any]) -> Optional[str]:
    keys = set((facts or {}).get("facts", {}).keys())
    if "us-gaap" in keys:
        return "us-gaap"
    if "ifrs-full" in keys:
        return "ifrs-full"
    return None


def extract_annual_report_dates(submissions: Dict[str, Any], years: int = 5) -> List[str]:
    recent = (submissions or {}).get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    report_dates = recent.get("reportDate", [])
    filing_dates = recent.get("filingDate", [])

    rows: List[Tuple[str, str]] = []
    for form, report_end, filed in zip(forms, report_dates, filing_dates):
        if form in {"10-K", "10-K/A"} and report_end:
            filing_key = filed or ""
            rows.append((filing_key, report_end))

    if not rows:
        return []

    # Sort by filing date descending (latest first), keep unique report dates
    rows.sort(key=lambda row: row[0], reverse=True)
    seen = set()
    ordered: List[str] = []
    for _, report_end in rows:
        if report_end not in seen:
            ordered.append(report_end)
            seen.add(report_end)
        if len(ordered) >= years:
            break
    return ordered


def build_period_statements(
    taxonomy_facts: Dict[str, Any],
    report_date: str,
) -> PeriodStatements:
    income = _build_statement(taxonomy_facts, canonical_maps.IS_ALIASES, report_date, instant=False)
    cash = _build_statement(taxonomy_facts, canonical_maps.CF_ALIASES, report_date, instant=False)
    balance = _build_statement(taxonomy_facts, canonical_maps.BS_ALIASES, report_date, instant=True)
    share_data = _build_statement(taxonomy_facts, canonical_maps.SHARE_ALIASES, report_date, instant=False)
    return PeriodStatements(
        income_statement=income,
        cash_flow_statement=cash,
        balance_sheet=balance,
        share_data=share_data,
    )


def _build_statement(
    taxonomy_facts: Dict[str, Any],
    alias_map: Mapping[str, List[str]],
    report_date: str,
    instant: bool,
) -> Dict[str, StatementLine]:
    statement: Dict[str, StatementLine] = {}
    for label, aliases in alias_map.items():
        tag, amount, unit, concept_label = _first_value_for_aliases(taxonomy_facts, aliases, report_date, duration=not instant)
        statement[label] = StatementLine(
            amount=amount,
            tag_used=tag,
            unit=unit,
            concept_label=concept_label,
        )
    return statement


def _first_value_for_aliases(
    taxonomy_facts: Dict[str, Any],
    aliases: Iterable[str],
    report_date: str,
    duration: bool,
) -> Tuple[Optional[str], Optional[float], Optional[str], Optional[str]]:
    for tag in aliases:
        node = taxonomy_facts.get(tag)
        if not node:
            continue
        units = node.get("units")
        if not isinstance(units, dict):
            continue

        flattened = flatten_units(units)
        selected = pick_for_report_date(flattened, report_date, duration)
        if selected:
            label = node.get("label") or node.get("description") or tag
            value = selected.get("val")
            try:
                amount = float(value) if value is not None else None
            except (TypeError, ValueError):
                amount = None
            return tag, amount, selected.get("_unit"), label

    return None, None, None, None


def infer_canonical_line(statement_line: StatementLine) -> Optional[str]:
    """
    Infer a canonical key when direct mapping via tag failed.
    """
    return infer_canonical_from_label(statement_line.concept_label or "")





