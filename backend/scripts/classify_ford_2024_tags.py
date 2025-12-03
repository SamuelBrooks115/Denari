"""
classify_ford_2024_tags.py — Classify Ford 2024 financial line items with LLM.

This script:
1. Loads enriched Arelle facts JSON for Ford 2024
2. Converts to FactLine objects and filters by fiscal year
3. Partitions by statement type (IS, BS, CF)
4. Calls LLM classifier for each statement type
5. Writes tagged JSON output

Usage:
    python scripts/classify_ford_2024_tags.py \
        --facts-json outputs/F_FY2024_arelle_raw_facts.json \
        --output-json outputs/F_FY2024_tagged_lines.json \
        --fiscal-year 2024 \
        --verbose
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from app.tagging.llm_classifier import classify_fact_lines_with_llm
from app.tagging.models import FactLine, normalize_fact_to_factline
from app.tagging.sanity_checks import print_classification_summary


def load_facts_json(facts_json_path: Path) -> Dict[str, Any]:
    """
    Load enriched Arelle facts JSON file.
    
    Args:
        facts_json_path: Path to JSON file
        
    Returns:
        Parsed JSON dictionary
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    if not facts_json_path.exists():
        raise FileNotFoundError(f"Facts JSON file not found: {facts_json_path}")
    
    with facts_json_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def filter_by_fiscal_year(
    facts: List[Dict[str, Any]],
    fiscal_year: int,
) -> List[Dict[str, Any]]:
    """
    Filter facts to a specific fiscal year.
    
    Args:
        facts: List of fact dictionaries
        fiscal_year: Target fiscal year (e.g., 2024)
        
    Returns:
        Filtered list of facts
    """
    filtered = []
    
    for fact in facts:
        period_end = fact.get("period_end") or fact.get("end")
        if not period_end:
            continue
        
        # Extract year from period_end (YYYY-MM-DD format)
        try:
            year = int(period_end.split("-")[0])
            if year == fiscal_year:
                filtered.append(fact)
        except (ValueError, AttributeError):
            continue
    
    return filtered


def partition_by_statement_type(
    fact_lines: List[FactLine],
) -> Dict[str, List[FactLine]]:
    """
    Partition fact lines by statement type.
    
    Args:
        fact_lines: List of FactLine objects
        
    Returns:
        Dictionary mapping statement_type -> list of FactLine objects
    """
    partitioned: Dict[str, List[FactLine]] = {
        "IS": [],
        "BS": [],
        "CF": [],
        "UNKNOWN": [],
    }
    
    for line in fact_lines:
        stmt_type = line.statement_type
        if stmt_type in partitioned:
            partitioned[stmt_type].append(line)
        else:
            partitioned["UNKNOWN"].append(line)
    
    return partitioned


def write_tagged_json(
    output_path: Path,
    company: str,
    fiscal_year: int,
    tagged_lines: List[FactLine],
) -> None:
    """
    Write tagged lines to JSON file.
    
    Args:
        output_path: Path to output JSON file
        company: Company name
        fiscal_year: Fiscal year
        tagged_lines: List of tagged FactLine objects
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert FactLine objects to dictionaries
    lines_data = []
    for line in tagged_lines:
        line_dict: Dict[str, Any] = {
            "line_id": line.line_id,
            "statement_type": line.statement_type,
            "label": line.label,
            "concept_qname": line.concept_qname,
            "value": line.value,
            "calc_tags": line.calc_tags,
        }
        
        # Add optional fields if present
        if line.parent_label:
            line_dict["parent_label"] = line.parent_label
        if line.role_uri:
            line_dict["role_uri"] = line.role_uri
        if line.period_start:
            line_dict["period_start"] = line.period_start
        if line.period_end:
            line_dict["period_end"] = line.period_end
        if line.unit:
            line_dict["unit"] = line.unit
        if line.dimensions:
            line_dict["dimensions"] = line.dimensions
        if line.is_abstract:
            line_dict["is_abstract"] = line.is_abstract
        
        lines_data.append(line_dict)
    
    output_data = {
        "company": company,
        "fiscal_year": fiscal_year,
        "lines": lines_data,
    }
    
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Classify Ford 2024 financial line items with LLM"
    )
    parser.add_argument(
        "--facts-json",
        type=str,
        required=True,
        help="Path to enriched Arelle facts JSON file",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        required=True,
        help="Path to output tagged JSON file",
    )
    parser.add_argument(
        "--fiscal-year",
        type=int,
        default=2024,
        help="Target fiscal year (default: 2024)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output (classification summary)",
    )
    
    args = parser.parse_args()
    
    try:
        # Load facts JSON
        facts_json_path = Path(args.facts_json)
        facts_data = load_facts_json(facts_json_path)
        
        # Extract facts array
        raw_facts = facts_data.get("facts", [])
        if not raw_facts:
            print("ERROR: No facts found in JSON file", file=sys.stderr)
            sys.exit(1)
        
        # Filter by fiscal year
        filtered_facts = filter_by_fiscal_year(raw_facts, args.fiscal_year)
        
        if not filtered_facts:
            print(
                f"ERROR: No facts found for fiscal year {args.fiscal_year}",
                file=sys.stderr,
            )
            sys.exit(1)
        
        # Convert to FactLine objects
        fact_lines = [normalize_fact_to_factline(fact) for fact in filtered_facts]
        
        # Partition by statement type
        partitioned = partition_by_statement_type(fact_lines)
        
        # Classify each statement type
        all_tagged_lines: List[FactLine] = []
        
        for stmt_type in ["IS", "BS", "CF"]:
            lines = partitioned[stmt_type]
            if not lines:
                if args.verbose:
                    print(f"No {stmt_type} lines found, skipping")
                continue
            
            try:
                if args.verbose:
                    print(f"Classifying {len(lines)} {stmt_type} lines...")
                
                tagged = classify_fact_lines_with_llm(lines, stmt_type)
                all_tagged_lines.extend(tagged)
            
            except Exception as e:
                print(
                    f"WARNING: Failed to classify {stmt_type} lines: {e}",
                    file=sys.stderr,
                )
                # Continue with other statement types
                all_tagged_lines.extend(lines)  # Add untagged lines
        
        # Get company name
        company = facts_data.get("company", "Unknown")
        
        # Write output
        output_path = Path(args.output_json)
        write_tagged_json(output_path, company, args.fiscal_year, all_tagged_lines)
        
        # Print summary if verbose
        if args.verbose:
            print_classification_summary(all_tagged_lines, verbose=True)
        
        print(f"Successfully classified Ford {args.fiscal_year} facts and wrote tagged JSON to {output_path}")
    
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in facts file: {e}", file=sys.stderr)
        sys.exit(1)
    
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

