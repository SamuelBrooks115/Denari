"""
Normalization entry points that convert structured Company Facts data into
canonical XBRL fact payloads ready for persistence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional

from .canonical_maps import get_canonical_map
from .companyfacts_parser import PeriodStatements, StatementLine, infer_canonical_line

STATEMENT_TYPE_BY_CANONICAL: Mapping[str, str] = {
    # Income statement
    "revenue": "IS",
    "cogs": "IS",
    "gross_profit": "IS",
    "operating_expense": "IS",
    "research_and_development": "IS",
    "selling_general_administrative": "IS",
    "operating_income": "IS",
    "interest_expense": "IS",
    "depreciation_amortization": "IS",
    "nonoperating_income": "IS",
    "pretax_income": "IS",
    "income_tax": "IS",
    "net_income": "IS",
    # Cash flow
    "cfo": "CF",
    "cfi": "CF",
    "cff": "CF",
    "capex": "CF",
    "stock_based_compensation": "CF",
    "working_capital_changes": "CF",
    "dividends_paid": "CF",
    "debt_issued": "CF",
    "debt_repaid": "CF",
    "share_repurchases": "CF",
    "fcf": "CF",
    # Balance sheet
    "total_assets": "BS",
    "current_assets": "BS",
    "cash_and_equivalents": "BS",
    "accounts_receivable": "BS",
    "inventory": "BS",
    "ppe_net": "BS",
    "goodwill": "BS",
    "intangible_assets": "BS",
    "total_liabilities": "BS",
    "current_liabilities": "BS",
    "accounts_payable": "BS",
    "long_term_debt": "BS",
    "shareholders_equity": "BS",
    # Share data
    "shares_basic": "SHARES",
    "shares_diluted": "SHARES",
    "eps_basic": "SHARES",
    "eps_diluted": "SHARES",
    "shares_outstanding": "SHARES",
}


@dataclass
class NormalizedFact:
    company_id: Optional[int]
    filing_id: Optional[int]
    period_end: Any
    statement_type: str
    tag: str
    value: float
    unit: Optional[str]
    source_tag: Optional[str]
    method: str
    confidence: float
    taxonomy: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "company_id": self.company_id,
            "filing_id": self.filing_id,
            "period_end": self.period_end,
            "statement_type": self.statement_type,
            "tag": self.tag,
            "value": self.value,
            "unit": self.unit,
            "source_tag": self.source_tag,
            "method": self.method,
            "confidence": self.confidence,
            "taxonomy": self.taxonomy,
        }


class CompanyFactsNormalizer:
    """
    Convert parsed Company Facts statements into canonical fact rows.
    """

    def normalize_companyfacts(
        self,
        company_meta: Dict[str, Any],
        taxonomy: str,
        statements_by_period: Mapping[str, PeriodStatements],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Normalize multiple reporting periods."""
        normalized: Dict[str, List[Dict[str, Any]]] = {}

        for period_end, statements in statements_by_period.items():
            filing_meta = dict(company_meta)
            filing_meta["period_end"] = period_end
            facts = self.normalize_filing(filing_meta, taxonomy, statements)
            normalized[period_end] = [fact.as_dict() for fact in facts]
        return normalized

    def normalize_filing(
        self,
        filing_meta: Dict[str, Any],
        taxonomy: str,
        statements: PeriodStatements,
    ) -> List[NormalizedFact]:
        """Normalize one period's statements."""
        canonical_map = get_canonical_map(taxonomy)
        canonical_entries: Dict[str, Dict[str, Any]] = {}

        def consume(statement_type: str, lines: Dict[str, StatementLine]) -> None:
            for line in lines.values():
                if line.amount is None:
                    continue
                method = "map"
                confidence = 1.0
                canonical_key = None

                if line.tag_used and line.tag_used in canonical_map:
                    canonical_key = canonical_map[line.tag_used]
                else:
                    inferred = infer_canonical_line(line)
                    if inferred:
                        canonical_key = inferred
                        method = "label"
                        confidence = 0.7

                if not canonical_key:
                    continue

                prior = canonical_entries.get(canonical_key)
                if prior and prior["confidence"] >= confidence:
                    continue  # keep higher-confidence fact

                canonical_entries[canonical_key] = {
                    "value": float(line.amount),
                    "unit": line.unit,
                    "source_tag": line.tag_used,
                    "method": method,
                    "confidence": confidence,
                    "statement_type": statement_type,
                }

        consume("IS", statements.income_statement)
        consume("CF", statements.cash_flow_statement)
        consume("BS", statements.balance_sheet)
        consume("SHARES", statements.share_data)

        self._apply_derivations(canonical_entries)

        facts: List[NormalizedFact] = []
        for canonical_key, payload in canonical_entries.items():
            statement_type = payload.get("statement_type") or STATEMENT_TYPE_BY_CANONICAL.get(canonical_key, "IS")
            fact = NormalizedFact(
                company_id=filing_meta["company_id"],
                filing_id=filing_meta.get("filing_id"),
                period_end=filing_meta["period_end"],
                statement_type=statement_type,
                tag=canonical_key,
                value=payload["value"],
                unit=payload.get("unit"),
                source_tag=payload.get("source_tag"),
                method=payload.get("method", "map"),
                confidence=payload.get("confidence", 1.0),
                taxonomy=taxonomy,
            )
            facts.append(fact)

        facts.sort(key=lambda f: (f.statement_type, f.tag))
        return facts

    # ------------------------------------------------------------------ #
    def _apply_derivations(self, canonical_entries: Dict[str, Dict[str, Any]]) -> None:
        # Gross Profit
        if "gross_profit" not in canonical_entries and {"revenue", "cogs"}.issubset(canonical_entries):
            revenue = canonical_entries["revenue"]["value"]
            cogs = canonical_entries["cogs"]["value"]
            canonical_entries["gross_profit"] = {
                "value": revenue - cogs,
                "unit": canonical_entries["revenue"].get("unit"),
                "source_tag": None,
                "method": "derived",
                "confidence": 0.6,
                "statement_type": "IS",
            }

        # Free Cash Flow
        if "fcf" not in canonical_entries and {"cfo", "capex"}.issubset(canonical_entries):
            cfo = canonical_entries["cfo"]["value"]
            capex = canonical_entries["capex"]["value"]
            canonical_entries["fcf"] = {
                "value": cfo - abs(capex),
                "unit": canonical_entries["cfo"].get("unit"),
                "source_tag": None,
                "method": "derived",
                "confidence": 0.6,
                "statement_type": "CF",
            }


# Convenience facade ------------------------------------------------------- #
def normalize_companyfacts(
    company_meta: Dict[str, Any],
    taxonomy: str,
    statements_by_period: Mapping[str, PeriodStatements],
) -> Dict[str, List[Dict[str, Any]]]:
    normalizer = CompanyFactsNormalizer()
    return normalizer.normalize_companyfacts(company_meta, taxonomy, statements_by_period)


