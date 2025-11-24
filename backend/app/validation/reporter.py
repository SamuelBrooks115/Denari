"""
reporter.py — Report generation for validation results.

Produces both console output (tables) and JSON reports.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def format_console_table(results: List[Dict[str, Any]]) -> str:
    """
    Format validation results as a console table.
    
    Args:
        results: List of validation result dictionaries
        
    Returns:
        Formatted table string
    """
    lines = []
    lines.append("=" * 120)
    lines.append("FORD TAG VALIDATION REPORT")
    lines.append("=" * 120)
    lines.append("")
    
    # Group by statement type
    by_statement: Dict[str, List[Dict[str, Any]]] = {
        "income_statement": [],
        "balance_sheet": [],
        "cash_flow_statement": [],
    }
    
    for result in results:
        stmt_type = result.get("statement_type", "unknown")
        if stmt_type in by_statement:
            by_statement[stmt_type].append(result)
    
    for statement_type, stmt_results in by_statement.items():
        if not stmt_results:
            continue
        
        lines.append(f"\n{statement_type.upper().replace('_', ' ')}")
        lines.append("-" * 120)
        lines.append(
            f"{'Variable':<30} {'Expected Role(s)':<25} {'Status':<20} {'Tag':<20} {'Confidence':<10} {'Periods':<15}"
        )
        lines.append("-" * 120)
        
        for result in stmt_results:
            variable = result.get("variable", "")
            expected_roles = ", ".join(result.get("expected_roles", []))
            status = result.get("status", "")
            chosen = result.get("chosen", {})
            # Handle None tag (for computed/proxy values)
            tag_value = chosen.get("tag") if chosen else None
            if tag_value:
                tag = tag_value[:18]
            elif chosen and chosen.get("computation_method"):
                tag = "Computed"
            elif chosen and chosen.get("source") == "proxy":
                tag = "Proxy"
            else:
                tag = "N/A"
            confidence = f"{chosen.get('confidence', 0.0):.2f}" if chosen else "N/A"
            periods = ", ".join(chosen.get("periods_found", [])[:2]) if chosen and chosen.get("periods_found") else "N/A"
            
            # Truncate long strings
            if len(variable) > 28:
                variable = variable[:25] + "..."
            if len(expected_roles) > 23:
                expected_roles = expected_roles[:20] + "..."
            if len(tag) > 18:
                tag = tag[:15] + "..."
            
            lines.append(
                f"{variable:<30} {expected_roles:<25} {status:<20} {tag:<20} {confidence:<10} {periods:<15}"
            )
            
            # Add reason for failures
            if status == "FAIL":
                reason = result.get("reason", "")
                lines.append(f"  -> FAIL: {reason}")
        
        lines.append("")
    
    # Summary - check if status starts with "PASS" to handle "PASS (direct)", "PASS (computed)", "PASS (proxy)"
    total = len(results)
    passed = sum(1 for r in results if r.get("status", "").startswith("PASS"))
    failed = total - passed
    
    lines.append("=" * 120)
    lines.append(f"SUMMARY: {passed}/{total} PASSED, {failed}/{total} FAILED")
    lines.append("=" * 120)
    
    return "\n".join(lines)


def generate_json_report(
    results: List[Dict[str, Any]],
    output_path: str | Path,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Generate JSON report file.
    
    Args:
        results: List of validation result dictionaries
        output_path: Path to save JSON report
        metadata: Optional metadata to include in report
    """
    report = {
        "metadata": metadata or {},
        "summary": {
            "total_variables": len(results),
            "passed": sum(1 for r in results if r.get("status", "").startswith("PASS")),
            "failed": sum(1 for r in results if r.get("status") == "FAIL"),
        },
        "results": results,
    }
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with output_path.open('w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)


def print_detailed_failures(results: List[Dict[str, Any]]) -> None:
    """
    Print detailed information about failures.
    
    Args:
        results: List of validation result dictionaries
    """
    failures = [r for r in results if r.get("status") == "FAIL"]
    
    if not failures:
        print("\n[SUCCESS] All required variables PASSED validation!")
        return
    
    print("\n" + "=" * 120)
    print("DETAILED FAILURE ANALYSIS")
    print("=" * 120)
    
    for failure in failures:
        print(f"\n[FAIL] {failure.get('variable')}")
        print(f"   Statement: {failure.get('statement_type')}")
        print(f"   Expected Roles: {', '.join(failure.get('expected_roles', []))}")
        print(f"   Reason: {failure.get('reason')}")
        
        # Show alternates if any
        alternates = failure.get("alternates", [])
        if alternates:
            print(f"   Found {len(alternates)} alternate candidates:")
            for alt in alternates[:3]:
                print(f"     - {alt.get('tag')} ({alt.get('label')}) - {alt.get('model_role')}")

