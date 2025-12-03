"""
sanity_checks.py — Sanity checks and summary functions for classification results.

This module provides functions to validate and summarize classification results.
"""

from collections import defaultdict
from typing import List

from app.tagging.models import FactLine


def print_classification_summary(tagged_lines: List[FactLine], verbose: bool = False) -> None:
    """
    Print a summary of classification results.
    
    Counts lines per statement type and per calc tag, then prints a formatted summary.
    
    Args:
        tagged_lines: List of tagged FactLine objects
        verbose: Whether to print the summary (if False, does nothing)
    """
    if not verbose:
        return
    
    if not tagged_lines:
        print("No lines to summarize")
        return
    
    # Count by statement type
    stmt_counts: dict[str, int] = defaultdict(int)
    for line in tagged_lines:
        stmt_counts[line.statement_type] += 1
    
    # Count by calc tag
    tag_counts: dict[str, int] = defaultdict(int)
    for line in tagged_lines:
        for tag in line.calc_tags:
            tag_counts[tag] += 1
    
    # Count tagged vs untagged
    tagged_count = sum(1 for line in tagged_lines if line.calc_tags)
    untagged_count = len(tagged_lines) - tagged_count
    
    print("\n" + "=" * 80)
    print("Classification Summary")
    print("=" * 80)
    
    print(f"\nTotal lines: {len(tagged_lines)}")
    print(f"Tagged: {tagged_count}")
    print(f"Untagged: {untagged_count}")
    
    print("\nLines by statement type:")
    for stmt_type in sorted(stmt_counts.keys()):
        count = stmt_counts[stmt_type]
        print(f"  {stmt_type}: {count} lines")
    
    if tag_counts:
        print("\nLines by calc tag:")
        for tag in sorted(tag_counts.keys()):
            count = tag_counts[tag]
            print(f"  {tag}: {count} line{'s' if count != 1 else ''}")
    else:
        print("\nNo calc tags assigned")
    
    # Print summary by statement type
    print("\nDetailed summary by statement type:")
    for stmt_type in ["IS", "BS", "CF"]:
        stmt_lines = [line for line in tagged_lines if line.statement_type == stmt_type]
        if not stmt_lines:
            continue
        
        stmt_tag_counts: dict[str, int] = defaultdict(int)
        for line in stmt_lines:
            for tag in line.calc_tags:
                stmt_tag_counts[tag] += 1
        
        if stmt_tag_counts:
            tag_list = ", ".join(
                f"{tag}: {count} line{'s' if count != 1 else ''}"
                for tag, count in sorted(stmt_tag_counts.items())
            )
            print(f"  {stmt_type}: {tag_list}")
        else:
            print(f"  {stmt_type}: No tags assigned")
    
    print("=" * 80 + "\n")

