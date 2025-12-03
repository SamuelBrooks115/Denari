"""
tagging — LLM-based financial line item classification.

This package provides tools for classifying financial line items from XBRL facts
using OpenAI LLM, assigning calc tags for downstream calculations.
"""

from app.tagging.calc_tags import VALID_CALC_TAGS, get_tag_definitions, is_valid_calc_tag
from app.tagging.models import FactLine, derive_statement_type, normalize_fact_to_factline
from app.tagging.llm_classifier import classify_fact_lines_with_llm
from app.tagging.llm_payload import build_classification_payload
from app.tagging.sanity_checks import print_classification_summary

__all__ = [
    "VALID_CALC_TAGS",
    "get_tag_definitions",
    "is_valid_calc_tag",
    "FactLine",
    "derive_statement_type",
    "normalize_fact_to_factline",
    "classify_fact_lines_with_llm",
    "build_classification_payload",
    "print_classification_summary",
]

