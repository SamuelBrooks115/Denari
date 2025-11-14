"""
clients package — External data access layers for ingestion.

Expose high-level client classes so adapters/pipelines can import without
touching concrete HTTP implementations directly.
"""

from .edgar_client import EdgarClient  # noqa: F401





