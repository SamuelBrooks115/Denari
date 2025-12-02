"""
test_ford_interest_bearing_debt.py — Ground Truth Test for Ford FY 2024 Interest-Bearing Debt

This test reproduces and verifies the calculation of Ford Motor Company's total
consolidated interest-bearing debt for FY 2024 using hard-coded inputs from the
2024 Form 10-K Note 17/18 tables.

Source: Ford Motor Company 2024 Form 10-K
- Note 18: Debt and Commitments
- Note 17: Lease Commitments

This is a ground truth test to validate dynamic XBRL-based debt extraction.
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class FordDebtBreakdown:
    """Breakdown of Ford Motor Company interest-bearing debt by segment and maturity."""
    company_excl_ford_credit_within_one_year: int
    company_excl_ford_credit_after_one_year: int
    company_excl_ford_credit_total: int
    
    ford_credit_within_one_year: int
    ford_credit_after_one_year: int
    ford_credit_total: int
    
    consolidated_total: int


def compute_ford_interest_bearing_debt_2024() -> FordDebtBreakdown:
    """
    Reproduce Ford Motor Company's FY 2024 interest-bearing debt calculation (in millions),
    using numbers from Note 18 (Debt and Commitments) of the 2024 Form 10-K.
    
    The goal is to make it trivial for an analyst to trace:
      - Company excluding Ford Credit debt (short-term + long-term)
      - Ford Credit debt (short-term + long-term)
      - Consolidated total interest-bearing debt
    
    All amounts are in millions of USD.
    
    Source: Ford Motor Company 2024 Form 10-K, Note 18 (Debt and Commitments)
    """
    
    # ========================================================================
    # Company excluding Ford Credit – 2024
    # ========================================================================
    # Source: Note 18, "Company excluding Ford Credit" section
    
    # Debt payable within one year (Company excluding Ford Credit)
    # Components:
    #   - Short-term debt: 632
    #   - Long-term payable within one year:
    #     - U.K. Export Finance Program: 784
    #     - Public unsecured debt securities: 176
    #     - Other debt (including finance leases): 176
    #   - Adjustments:
    #     - Unamortized (discount)/premium: -11
    #     - Unamortized issuance costs: -1
    # Total: 632 + 784 + 176 + 176 - 11 - 1 = 1,756
    company_within_one_year = 1_756
    
    # Long-term debt payable after one year (Company excluding Ford Credit)
    # Components:
    #   - Public unsecured debt securities: 14,759
    #   - Convertible notes: 2,300
    #   - U.K. Export Finance Program: 940
    #   - Other debt (including finance leases): 1,160
    #   - Adjustments:
    #     - Unamortized (discount)/premium: -109
    #     - Unamortized issuance costs: -152
    # Total: 14,759 + 2,300 + 940 + 1,160 - 109 - 152 = 18,898
    company_after_one_year = 18_898
    
    # Total Company excluding Ford Credit interest-bearing debt
    # Total: 1,756 + 18,898 = 20,654
    company_total = company_within_one_year + company_after_one_year
    assert company_total == 20_654, f"Company total should be 20,654, got {company_total}"
    
    # ========================================================================
    # Ford Credit – 2024
    # ========================================================================
    # Source: Note 18, "Ford Credit" section
    
    # Debt payable within one year (Ford Credit)
    # Components:
    #   - Short-term debt: 17,413
    #   - Long-term payable within one year:
    #     - Unsecured debt: 12,871
    #     - Asset-backed debt: 23,050
    #   - Adjustments:
    #     - Unamortized (discount)/premium: 2
    #     - Unamortized issuance costs: -18
    #     - Fair value adjustments: -125
    # Total: 17,413 + 12,871 + 23,050 + 2 - 18 - 125 = 53,193
    ford_credit_within_one_year = 53_193
    
    # Long-term debt payable after one year (Ford Credit)
    # Components:
    #   - Unsecured debt: 49,607
    #   - Asset-backed debt: 36,224
    #   - Adjustments:
    #     - Unamortized (discount)/premium: -20
    #     - Unamortized issuance costs: -217
    #     - Fair value adjustments: -919
    # Total: 49,607 + 36,224 - 20 - 217 - 919 = 84,675
    ford_credit_after_one_year = 84_675
    
    # Total Ford Credit interest-bearing debt
    # Total: 53,193 + 84,675 = 137,868
    ford_credit_total = ford_credit_within_one_year + ford_credit_after_one_year
    assert ford_credit_total == 137_868, f"Ford Credit total should be 137,868, got {ford_credit_total}"
    
    # ========================================================================
    # Consolidated Ford interest-bearing debt (2024)
    # ========================================================================
    # Interest-bearing debt (total) = Company excluding Ford Credit + Ford Credit
    # Total: 20,654 + 137,868 = 158,522
    consolidated_total = company_total + ford_credit_total
    assert consolidated_total == 158_522, f"Consolidated total should be 158,522, got {consolidated_total}"
    
    return FordDebtBreakdown(
        company_excl_ford_credit_within_one_year=company_within_one_year,
        company_excl_ford_credit_after_one_year=company_after_one_year,
        company_excl_ford_credit_total=company_total,
        ford_credit_within_one_year=ford_credit_within_one_year,
        ford_credit_after_one_year=ford_credit_after_one_year,
        ford_credit_total=ford_credit_total,
        consolidated_total=consolidated_total,
    )


def format_ford_debt_breakdown(b: FordDebtBreakdown) -> str:
    """
    Return a multi-line string that explains the calculation in plain language,
    suitable for manual verification against the 2024 Form 10-K.
    
    Args:
        b: FordDebtBreakdown dataclass instance
        
    Returns:
        Human-readable breakdown string
    """
    lines = []
    lines.append("=" * 80)
    lines.append("Ford Motor Company - Interest-Bearing Debt (FY 2024, in millions)")
    lines.append("Source: 2024 Form 10-K, Note 18 (Debt and Commitments)")
    lines.append("=" * 80)
    lines.append("")
    
    lines.append("1. Company excluding Ford Credit:")
    lines.append(f"   Debt payable within one year:     {b.company_excl_ford_credit_within_one_year:>10,}")
    lines.append(f"   Debt payable after one year:      {b.company_excl_ford_credit_after_one_year:>10,}")
    lines.append(f"   " + "-" * 47)
    lines.append(f"   Total Company excl. Ford Credit:  {b.company_excl_ford_credit_total:>10,}")
    lines.append("")
    
    lines.append("2. Ford Credit:")
    lines.append(f"   Debt payable within one year:     {b.ford_credit_within_one_year:>10,}")
    lines.append(f"   Debt payable after one year:      {b.ford_credit_after_one_year:>10,}")
    lines.append(f"   " + "-" * 47)
    lines.append(f"   Total Ford Credit:                 {b.ford_credit_total:>10,}")
    lines.append("")
    
    lines.append("3. Consolidated Ford interest-bearing debt:")
    lines.append(f"   = Company excl. Ford Credit + Ford Credit")
    lines.append(f"   = {b.company_excl_ford_credit_total:,} + {b.ford_credit_total:,}")
    lines.append(f"   = {b.consolidated_total:,}")
    lines.append("")
    lines.append(f"   Expected: 158,522")
    lines.append(f"   Actual:   {b.consolidated_total:,}")
    lines.append("")
    
    if b.consolidated_total == 158_522:
        lines.append("[OK] Calculation matches expected total")
    else:
        lines.append(f"[ERROR] Calculation does NOT match expected total (difference: {b.consolidated_total - 158_522:,})")
    
    lines.append("=" * 80)
    
    return "\n".join(lines)


# ============================================================================
# Pytest Tests
# ============================================================================

def test_ford_interest_bearing_debt_2024_totals():
    """
    Test that the Ford FY 2024 interest-bearing debt calculation produces
    the correct sub-totals and consolidated total.
    """
    breakdown = compute_ford_interest_bearing_debt_2024()
    
    # Check Company excluding Ford Credit sub-totals
    assert breakdown.company_excl_ford_credit_within_one_year == 1_756, \
        "Company within one year should be 1,756"
    assert breakdown.company_excl_ford_credit_after_one_year == 18_898, \
        "Company after one year should be 18,898"
    assert breakdown.company_excl_ford_credit_total == 20_654, \
        "Company total should be 20,654"
    
    # Verify Company total is sum of components
    calculated_company_total = (
        breakdown.company_excl_ford_credit_within_one_year +
        breakdown.company_excl_ford_credit_after_one_year
    )
    assert calculated_company_total == breakdown.company_excl_ford_credit_total, \
        f"Company total should equal sum of components: {calculated_company_total} != {breakdown.company_excl_ford_credit_total}"
    
    # Check Ford Credit sub-totals
    assert breakdown.ford_credit_within_one_year == 53_193, \
        "Ford Credit within one year should be 53,193"
    assert breakdown.ford_credit_after_one_year == 84_675, \
        "Ford Credit after one year should be 84,675"
    assert breakdown.ford_credit_total == 137_868, \
        "Ford Credit total should be 137,868"
    
    # Verify Ford Credit total is sum of components
    calculated_ford_credit_total = (
        breakdown.ford_credit_within_one_year +
        breakdown.ford_credit_after_one_year
    )
    assert calculated_ford_credit_total == breakdown.ford_credit_total, \
        f"Ford Credit total should equal sum of components: {calculated_ford_credit_total} != {breakdown.ford_credit_total}"
    
    # Check consolidated total
    assert breakdown.consolidated_total == 158_522, \
        f"Consolidated total should be 158,522, got {breakdown.consolidated_total}"
    
    # Verify consolidated total is sum of segment totals
    calculated_consolidated = (
        breakdown.company_excl_ford_credit_total +
        breakdown.ford_credit_total
    )
    assert calculated_consolidated == breakdown.consolidated_total, \
        f"Consolidated total should equal sum of segment totals: {calculated_consolidated} != {breakdown.consolidated_total}"


def test_ford_interest_bearing_debt_2024_human_readable():
    """
    Test that the human-readable breakdown includes all key numbers and
    provides a clear explanation for manual verification.
    """
    breakdown = compute_ford_interest_bearing_debt_2024()
    text = format_ford_debt_breakdown(breakdown)
    
    # Basic sanity checks - ensure key numbers are present
    assert "1,756" in text or "1,756" in text.replace(",", ""), \
        "Company within one year (1,756) should be in output"
    assert "18,898" in text or "18,898" in text.replace(",", ""), \
        "Company after one year (18,898) should be in output"
    assert "20,654" in text or "20,654" in text.replace(",", ""), \
        "Company total (20,654) should be in output"
    
    assert "53,193" in text or "53,193" in text.replace(",", ""), \
        "Ford Credit within one year (53,193) should be in output"
    assert "84,675" in text or "84,675" in text.replace(",", ""), \
        "Ford Credit after one year (84,675) should be in output"
    assert "137,868" in text or "137,868" in text.replace(",", ""), \
        "Ford Credit total (137,868) should be in output"
    
    assert "158,522" in text or "158,522" in text.replace(",", ""), \
        "Consolidated total (158,522) should be in output"
    
    # Check that the explanation includes the formula
    assert "Company excl. Ford Credit" in text or "Company excluding Ford Credit" in text, \
        "Output should mention Company excluding Ford Credit"
    assert "Ford Credit" in text, \
        "Output should mention Ford Credit"
    assert "Consolidated" in text, \
        "Output should mention Consolidated"
    
    # Verify the breakdown shows the calculation
    assert str(breakdown.company_excl_ford_credit_total) in text.replace(",", ""), \
        "Company total should appear in calculation"
    assert str(breakdown.ford_credit_total) in text.replace(",", ""), \
        "Ford Credit total should appear in calculation"
    assert str(breakdown.consolidated_total) in text.replace(",", ""), \
        "Consolidated total should appear in calculation"


def test_ford_interest_bearing_debt_2024_structure():
    """
    Test that the FordDebtBreakdown dataclass has the expected structure
    and all fields are populated correctly.
    """
    breakdown = compute_ford_interest_bearing_debt_2024()
    
    # Verify all fields are integers
    assert isinstance(breakdown.company_excl_ford_credit_within_one_year, int)
    assert isinstance(breakdown.company_excl_ford_credit_after_one_year, int)
    assert isinstance(breakdown.company_excl_ford_credit_total, int)
    assert isinstance(breakdown.ford_credit_within_one_year, int)
    assert isinstance(breakdown.ford_credit_after_one_year, int)
    assert isinstance(breakdown.ford_credit_total, int)
    assert isinstance(breakdown.consolidated_total, int)
    
    # Verify all values are positive
    assert breakdown.company_excl_ford_credit_within_one_year > 0
    assert breakdown.company_excl_ford_credit_after_one_year > 0
    assert breakdown.company_excl_ford_credit_total > 0
    assert breakdown.ford_credit_within_one_year > 0
    assert breakdown.ford_credit_after_one_year > 0
    assert breakdown.ford_credit_total > 0
    assert breakdown.consolidated_total > 0
    
    # Verify Ford Credit is larger than Company (expected for Ford)
    assert breakdown.ford_credit_total > breakdown.company_excl_ford_credit_total, \
        "Ford Credit debt should be larger than Company excluding Ford Credit debt"


def test_ford_interest_bearing_debt_2024_printable():
    """
    Test that the breakdown can be printed and provides useful information.
    This ensures the dataclass __repr__ works and the format function is callable.
    """
    breakdown = compute_ford_interest_bearing_debt_2024()
    
    # Test that we can get string representation
    breakdown_str = str(breakdown)
    assert "FordDebtBreakdown" in breakdown_str or "consolidated_total" in breakdown_str
    
    # Test that format function returns a string
    formatted = format_ford_debt_breakdown(breakdown)
    assert isinstance(formatted, str)
    assert len(formatted) > 100  # Should be substantial output
    
    # Test that formatted output can be printed (no exceptions)
    # Note: We don't actually print here to avoid encoding issues in test output
    # The format function should produce valid strings
    assert "\n" in formatted  # Should have line breaks


if __name__ == "__main__":
    # Allow running directly for quick verification
    import sys
    
    breakdown = compute_ford_interest_bearing_debt_2024()
    print(format_ford_debt_breakdown(breakdown))
    
    # Quick assertion
    if breakdown.consolidated_total == 158_522:
        print("\n[OK] All calculations correct!")
        sys.exit(0)
    else:
        print(f"\n[ERROR] Calculation error: expected 158,522, got {breakdown.consolidated_total}")
        sys.exit(1)

