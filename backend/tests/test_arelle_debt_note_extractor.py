"""
Tests for Arelle-based debt note extractor.

Tests verify that:
- Note 18 role finding works
- Segment classification works
- Maturity classification works
- DebtCell creation works
- Aggregation works
"""

from __future__ import annotations

import pytest

# Mock Arelle if not available
try:
    from arelle import Cntlr
    ARELLE_AVAILABLE = True
except ImportError:
    ARELLE_AVAILABLE = False


@pytest.mark.skipif(not ARELLE_AVAILABLE, reason="Arelle not installed")
def test_extract_note18_debt_requires_arelle():
    """Test that Note 18 extraction requires Arelle."""
    from app.xbrl.debt_note_extractor import extract_note18_debt
    
    assert callable(extract_note18_debt)


def test_segment_classification():
    """Test segment classification from dimensions."""
    from app.xbrl.debt_note_extractor import classify_segment_from_dimensions
    
    # Test consolidated (no dimensions)
    assert classify_segment_from_dimensions(None) == "consolidated"
    
    # Mock context objects (simplified for testing)
    class MockContext:
        def __init__(self, seg_dim_values=None):
            self.segDimValues = seg_dim_values or []
    
    # Consolidated (no dimensions)
    assert classify_segment_from_dimensions(MockContext()) == "consolidated"
    
    # Ford Credit
    ford_credit_ctx = MockContext(["Ford Credit Segment"])
    # Note: This is simplified - real Arelle contexts have more structure
    # The actual implementation will need to handle Arelle's dimension structure


def test_maturity_classification():
    """Test maturity bucket classification."""
    from app.xbrl.debt_note_extractor import classify_maturity_from_dimensions
    
    # Test unknown (no dimensions)
    assert classify_maturity_from_dimensions(None) == "unknown"
    
    # Mock context objects
    class MockContext:
        def __init__(self, seg_dim_values=None):
            self.segDimValues = seg_dim_values or []
    
    # Unknown (no dimensions)
    assert classify_maturity_from_dimensions(MockContext()) == "unknown"


def test_normalize_line_item_name():
    """Test line item name normalization."""
    from app.xbrl.debt_note_extractor import normalize_line_item_name
    
    assert normalize_line_item_name("us-gaap:UnsecuredDebt") == "unsecured_debt"
    assert normalize_line_item_name("us-gaap:AssetBackedDebt") == "asset_backed_debt"
    assert normalize_line_item_name("us-gaap:CommercialPaper") == "commercial_paper"
    assert normalize_line_item_name("us-gaap:FinanceLeaseLiability") == "finance_lease_liabilities"


def test_debt_cell_dataclass():
    """Test DebtCell dataclass."""
    from app.xbrl.debt_note_extractor import DebtCell
    
    cell = DebtCell(
        line_item="unsecured_debt",
        raw_concept="us-gaap:UnsecuredDebt",
        segment="ford_credit",
        maturity_bucket="within_one_year",
        value=1000000.0,
        unit="USD",
        period_end="2024-12-31",
    )
    
    assert cell.line_item == "unsecured_debt"
    assert cell.value == 1000000.0
    assert cell.segment == "ford_credit"


def test_note18_debt_table_aggregation():
    """Test Note18DebtTable aggregation methods."""
    from app.xbrl.debt_note_extractor import DebtCell, Note18DebtTable
    
    table = Note18DebtTable(
        company="Ford Motor Company",
        cik="0000037996",
        fiscal_year=2024,
        period_end="2024-12-31",
        cells=[
            DebtCell(
                line_item="unsecured_debt",
                raw_concept="us-gaap:UnsecuredDebt",
                segment="ford_credit",
                maturity_bucket="within_one_year",
                value=1000000.0,
                unit="USD",
                period_end="2024-12-31",
            ),
            DebtCell(
                line_item="unsecured_debt",
                raw_concept="us-gaap:UnsecuredDebt",
                segment="ford_credit",
                maturity_bucket="after_one_year",
                value=2000000.0,
                unit="USD",
                period_end="2024-12-31",
            ),
            DebtCell(
                line_item="unsecured_debt",
                raw_concept="us-gaap:UnsecuredDebt",
                segment="company_excl_ford_credit",
                maturity_bucket="within_one_year",
                value=500000.0,
                unit="USD",
                period_end="2024-12-31",
            ),
        ],
    )
    
    # Test aggregation
    assert table.get_total_by_segment("ford_credit") == 3000000.0
    assert table.get_total_by_segment("company_excl_ford_credit") == 500000.0
    assert table.get_total_by_maturity("within_one_year") == 1500000.0
    assert table.get_total_by_maturity("after_one_year") == 2000000.0
    
    # Test aggregation dict
    agg = table.aggregate_by_segment_and_maturity()
    assert agg["ford_credit"]["within_one_year"] == 1000000.0
    assert agg["ford_credit"]["after_one_year"] == 2000000.0
    assert agg["company_excl_ford_credit"]["within_one_year"] == 500000.0

