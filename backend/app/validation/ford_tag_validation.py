"""
ford_tag_validation.py — Ford-specific validation harness.

Validates tag classification for Ford (ticker F) against required DCF variables.
Works with both single-year and multi-year structured output formats.

Usage Examples:

    # Relative paths (recommended - works on all platforms):
    python -m app.validation.ford_tag_validation \
        --single-year outputs/F_FY2024_single_year_llm_classified.json \
        --multi-year outputs/F_multi_year_3years_llm_classified.json \
        --output outputs/ford_tag_validation_report.json

    # Windows PowerShell (use backtick for line continuation):
    python -m app.validation.ford_tag_validation `
        --single-year "outputs/F_FY2024_single_year_llm_classified.json" `
        --multi-year "outputs/F_multi_year_3years_llm_classified.json" `
        --output "outputs/ford_tag_validation_report.json"

    # Windows CMD (use caret for line continuation):
    python -m app.validation.ford_tag_validation ^
        --single-year "outputs/F_FY2024_single_year_llm_classified.json" ^
        --multi-year "outputs/F_multi_year_3years_llm_classified.json" ^
        --output "outputs/ford_tag_validation_report.json"

    # Absolute paths (use quotes if path contains spaces):
    python -m app.validation.ford_tag_validation \
        --single-year "C:/Users/abees/Denari/backend/outputs/F_FY2024_single_year_llm_classified.json" \
        --multi-year "C:/Users/abees/Denari/backend/outputs/F_multi_year_3years_llm_classified.json" \
        --output "C:/Users/abees/Denari/backend/outputs/ford_tag_validation_report.json"

    # Override only one file; the other will use the default Ford path:
    python -m app.validation.ford_tag_validation \
        --single-year outputs/F_FY2024_single_year_llm_classified.json

Note: Use forward slashes (/) in paths - they work on Windows, Linux, and macOS.
      Use quotes around paths if they contain spaces or special characters.

To extend to other companies:
    1. Update REQUIRED_VARIABLE_ROLES in role_map.py if needed
    2. Change file paths in this script or pass as arguments
    3. Update company name in metadata
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.validation.parser import parse_structured_output
from app.validation.reporter import (
    format_console_table,
    generate_json_report,
    print_detailed_failures,
)
from app.validation.validator import validate_all_variables


DEFAULT_SINGLE_YEAR = "outputs/F_FY2024_single_year_llm_classified.json"
DEFAULT_MULTI_YEAR = "outputs/F_multi_year_3years_llm_classified.json"
DEFAULT_OUTPUT = "outputs/ford_tag_validation_report.json"


def validate_ford_files(
    single_year_path: Optional[str | Path] = DEFAULT_SINGLE_YEAR,
    multi_year_path: Optional[str | Path] = DEFAULT_MULTI_YEAR,
    output_path: str | Path = DEFAULT_OUTPUT,
) -> Dict[str, Any]:
    """
    Validate Ford structured output files.

    Args:
        single_year_path: Path to single-year JSON file
        multi_year_path: Path to multi-year JSON file
        output_path: Path to save validation report

    Returns:
        Dictionary with validation results and metadata
    """
    results_by_file: Dict[str, List[Dict[str, Any]]] = {}
    all_results: List[Dict[str, Any]] = []

    if single_year_path:
        print(f"\n[Validating] single-year file: {single_year_path}")
        normalized = parse_structured_output(single_year_path)
        results = validate_all_variables(normalized)
        results_by_file["single_year"] = results
        all_results.extend(results)
        print(f"[OK] Processed {len(results)} variables")

    if multi_year_path:
        print(f"\n[Validating] multi-year file: {multi_year_path}")
        normalized = parse_structured_output(multi_year_path)
        results = validate_all_variables(normalized)
        results_by_file["multi_year"] = results
        if not single_year_path:
            all_results.extend(results)
        print(f"[OK] Processed {len(results)} variables")

    if not all_results:
        raise ValueError("No validation results generated. Check file paths.")

    print("\n" + "=" * 120)
    print("VALIDATION RESULTS")
    print("=" * 120)

    console_output = format_console_table(all_results)
    print(console_output)

    print_detailed_failures(all_results)

    metadata = {
        "company": "Ford Motor Company",
        "ticker": "F",
        "files_processed": {
            "single_year": str(single_year_path) if single_year_path else None,
            "multi_year": str(multi_year_path) if multi_year_path else None,
        },
    }

    output_path = Path(output_path)
    generate_json_report(all_results, output_path, metadata)
    print(f"\n[Report] JSON report saved to: {output_path}")

    return {
        "results": all_results,
        "results_by_file": results_by_file,
        "metadata": metadata,
    }


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Validate Ford tag classification against required DCF variables"
    )
    parser.add_argument(
        "--single-year",
        type=str,
        default=DEFAULT_SINGLE_YEAR,
        help="Path to single-year structured output JSON file",
    )
    parser.add_argument(
        "--multi-year",
        type=str,
        default=DEFAULT_MULTI_YEAR,
        help="Path to multi-year structured output JSON file",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=DEFAULT_OUTPUT,
        help="Path to save validation report JSON",
    )

    args = parser.parse_args()

    validate_ford_files(
        single_year_path=args.single_year,
        multi_year_path=args.multi_year,
        output_path=args.output,
    )


if __name__ == "__main__":
    main()
