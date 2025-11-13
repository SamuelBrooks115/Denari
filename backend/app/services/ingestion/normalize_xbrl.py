"""
Compatibility facade for legacy imports.

All new code should import from `app.services.ingestion.xbrl.normalizer`.
"""

from __future__ import annotations

from typing import Dict, List, Mapping

from app.services.ingestion.xbrl.normalizer import CompanyFactsNormalizer, normalize_companyfacts  # noqa: F401

# Backwards-compatible function name --------------------------------------------------------- #

def normalize_xbrl(company_meta: Dict, taxonomy: str, statements_by_period: Mapping[str, object]) -> Dict[str, List[Dict]]:
    """
    Wrapper maintained so legacy call sites using `normalize_xbrl` keep working.
    """
    normalizer = CompanyFactsNormalizer()
    return normalizer.normalize_companyfacts(company_meta, taxonomy, statements_by_period)
