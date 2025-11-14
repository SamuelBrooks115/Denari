"""
xbrl package — Utilities for transforming EDGAR Company Facts into Denari's
canonical financial data model.

Submodules:
    - canonical_maps: canonical tag definitions and alias tables.
    - utils: shared helpers for period filtering, unit selection, etc.
    - companyfacts_parser: converts company facts JSON to structured statements.
    - normalizer: high-level normalization entry points.
"""

from .normalizer import CompanyFactsNormalizer, normalize_companyfacts  # noqa: F401





