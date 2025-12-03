"""
Unit tests for debt_extractor.py

Tests all methods and ensures full auditability.
"""

import pytest
from dataclasses import asdict
from typing import Dict, Any

from app.valuation.debt_extractor import (
    DebtComponent,
    DebtMethodResult,
    InterestBearingDebtResult,
    get_xbrl_debt_values,
    get_statement_debt_values,
    get_total_debt_summarized,
    get_segmented_debt_if_applicable,
    compute_interest_bearing_debt,
    _is_debt_tag,
    _is_debt_label,
)


# Test data fixtures
@pytest.fixture
def mock_xbrl_json() -> Dict[str, Any]:
    """Mock XBRL JSON structure (EDGAR Company Facts format)."""
    return {
        "facts": {
            "us-gaap": {
                "ShortTermBorrowings": {
                    "label": "Short-Term Borrowings",
                    "units": {
                        "USD": [
                            {
                                "end": "2024-12-31",
                                "val": 5000000000.0,
                                "dimensions": {}
                            }
                        ]
                    }
                },
                "LongTermDebtNoncurrent": {
                    "label": "Long-Term Debt, Noncurrent",
                    "units": {
                        "USD": [
                            {
                                "end": "2024-12-31",
                                "val": 20000000000.0,
                                "dimensions": {}
                            }
                        ]
                    }
                },
                "FinanceLeaseLiabilityCurrent": {
                    "label": "Finance Lease Liability, Current",
                    "units": {
                        "USD": [
                            {
                                "end": "2024-12-31",
                                "val": 1000000000.0,
                                "dimensions": {}
                            }
                        ]
                    }
                },
            }
        }
    }


@pytest.fixture
def mock_structured_json() -> Dict[str, Any]:
    """Mock structured JSON (from generate_ford_json output)."""
    return {
        "statements": {
            "balance_sheet": {
                "line_items": [
                    {
                        "tag": "us-gaap:ShortTermBorrowings",
                        "label": "Short-Term Borrowings",
                        "model_role": "BS_DEBT_CURRENT",
                        "periods": {
                            "2024-12-31": 5000000000.0
                        }
                    },
                    {
                        "tag": "us-gaap:LongTermDebtNoncurrent",
                        "label": "Long-Term Debt, Noncurrent",
                        "model_role": "BS_DEBT_NONCURRENT",
                        "periods": {
                            "2024-12-31": 20000000000.0
                        }
                    },
                    {
                        "tag": "us-gaap:FinanceLeaseLiabilityCurrent",
                        "label": "Finance Lease Liability, Current",
                        "model_role": "",
                        "periods": {
                            "2024-12-31": 1000000000.0
                        }
                    },
                    {
                        "tag": "us-gaap:AccountsPayableCurrent",
                        "label": "Accounts Payable",
                        "model_role": "BS_ACCOUNTS_PAYABLE",
                        "periods": {
                            "2024-12-31": 15000000000.0
                        }
                    },
                ]
            },
            "income_statement": {
                "line_items": [
                    {
                        "tag": "us-gaap:InterestExpense",
                        "label": "Interest Expense",
                        "model_role": "IS_INTEREST_EXPENSE",
                        "periods": {
                            "2024-12-31": 1560000000.0
                        }
                    }
                ]
            }
        },
        "periods": ["2024-12-31"]
    }


@pytest.fixture
def mock_structured_json_with_total_debt() -> Dict[str, Any]:
    """Mock structured JSON with explicit Total Debt line."""
    return {
        "statements": {
            "balance_sheet": {
                "line_items": [
                    {
                        "tag": "us-gaap:Debt",
                        "label": "Total Debt",
                        "model_role": "",
                        "periods": {
                            "2024-12-31": 26000000000.0
                        }
                    }
                ]
            }
        }
    }


@pytest.fixture
def mock_ford_segmented_json() -> Dict[str, Any]:
    """Mock Ford-style segmented JSON."""
    return {
        "statements": {
            "balance_sheet": {
                "line_items": [
                    {
                        "tag": "ford:AutomotiveDebt",
                        "label": "Ford Automotive Debt",
                        "model_role": "",
                        "periods": {
                            "2024-12-31": 10000000000.0
                        }
                    },
                    {
                        "tag": "ford:FordCreditDebt",
                        "label": "Ford Credit Debt",
                        "model_role": "",
                        "periods": {
                            "2024-12-31": 16000000000.0
                        }
                    }
                ]
            }
        }
    }


# Test helper functions
def test_is_debt_tag():
    """Test debt tag identification."""
    assert _is_debt_tag("us-gaap:ShortTermBorrowings") is True
    assert _is_debt_tag("us-gaap:LongTermDebtNoncurrent") is True
    assert _is_debt_tag("us-gaap:AccountsPayableCurrent") is False
    assert _is_debt_tag("ShortTermBorrowings") is True


def test_is_debt_label():
    """Test debt label identification."""
    assert _is_debt_label("Short-Term Borrowings") is True
    assert _is_debt_label("Long-Term Debt") is True
    assert _is_debt_label("Accounts Payable") is False
    assert _is_debt_label("Operating Lease Liability") is False
    assert _is_debt_label("Total Debt") is True


# Test Method 1: XBRL Aggregation
def test_get_xbrl_debt_values(mock_xbrl_json):
    """Test XBRL debt extraction from raw XBRL JSON."""
    result = get_xbrl_debt_values(mock_xbrl_json, period="2024-12-31")
    
    assert result.method_name == "XBRL_AGGREGATION"
    assert result.value == 26000000000.0  # 5B + 20B + 1B
    assert len(result.components) == 3
    
    # Check components
    component_names = [c.name for c in result.components]
    assert "Short-Term Borrowings" in component_names
    assert "Long-Term Debt, Noncurrent" in component_names
    assert "Finance Lease Liability, Current" in component_names


def test_get_xbrl_debt_values_from_structured(mock_structured_json):
    """Test XBRL debt extraction from structured JSON."""
    result = get_xbrl_debt_values(mock_structured_json, period="2024-12-31")
    
    assert result.method_name == "XBRL_AGGREGATION"
    assert result.value == 26000000000.0
    assert len(result.components) == 3


# Test Method 2: Structured Statement
def test_get_statement_debt_values(mock_structured_json):
    """Test debt extraction from structured balance sheet."""
    result = get_statement_debt_values(mock_structured_json, period="2024-12-31")
    
    assert result.method_name == "STRUCTURED_STATEMENT"
    assert result.value == 26000000000.0
    assert len(result.components) == 3
    
    # Should not include Accounts Payable
    component_names = [c.name for c in result.components]
    assert "Accounts Payable" not in component_names


# Test Method 3: Total Debt Summarized
def test_get_total_debt_summarized(mock_structured_json_with_total_debt):
    """Test extraction of explicit Total Debt line."""
    result = get_total_debt_summarized(mock_structured_json_with_total_debt, period="2024-12-31")
    
    assert result.method_name == "TOTAL_DEBT_SUMMARIZED"
    assert result.value == 26000000000.0
    assert len(result.components) == 1
    assert result.components[0].name == "Total Debt"


# Test Method 4: Segmented Debt
def test_get_segmented_debt_if_applicable(mock_ford_segmented_json):
    """Test Ford-style segmented debt extraction."""
    result = get_segmented_debt_if_applicable(mock_ford_segmented_json, period="2024-12-31")
    
    assert result.method_name == "SEGMENTED_DEBT"
    assert result.value == 26000000000.0  # 10B + 16B
    assert len(result.components) == 2
    
    # Check segments
    automotive_comp = next((c for c in result.components if "Automotive" in c.name), None)
    credit_comp = next((c for c in result.components if "Credit" in c.name), None)
    
    assert automotive_comp is not None
    assert credit_comp is not None
    assert automotive_comp.value == 10000000000.0
    assert credit_comp.value == 16000000000.0


# Test Method 5: Interest Expense Backsolve
def test_compute_interest_bearing_debt_with_interest_expense(mock_structured_json):
    """Test interest expense backsolve method."""
    data_sources = {
        "structured_statements_json": mock_structured_json
    }
    
    result = compute_interest_bearing_debt(
        data_sources,
        period="2024-12-31",
        assumed_interest_rate=0.06
    )
    
    # Should have multiple methods
    assert len(result.all_methods) >= 2
    
    # Find interest expense method
    interest_method = next(
        (m for m in result.all_methods if m.method_name == "INTEREST_EXPENSE_BACKSOLVE"),
        None
    )
    
    assert interest_method is not None
    # Interest expense 1.56B / 0.06 = 26B
    assert interest_method.value == pytest.approx(26000000000.0, rel=0.01)


# Test Main Orchestrator
def test_compute_interest_bearing_debt_priority_order(mock_structured_json):
    """Test that methods are attempted in priority order."""
    data_sources = {
        "structured_statements_json": mock_structured_json
    }
    
    result = compute_interest_bearing_debt(
        data_sources,
        period="2024-12-31"
    )
    
    # Should have multiple methods
    assert len(result.all_methods) >= 2
    
    # First reliable method should be primary
    if result.primary_method:
        primary = next((m for m in result.all_methods if m.method_name == result.primary_method), None)
        assert primary is not None
        assert primary.is_reliable()
        assert result.final_value == primary.value


# Test Human-Readable Output
def test_to_human_readable(mock_structured_json):
    """Test human-readable audit trail generation."""
    data_sources = {
        "structured_statements_json": mock_structured_json
    }
    
    result = compute_interest_bearing_debt(
        data_sources,
        period="2024-12-31"
    )
    
    readable = result.to_human_readable()
    
    # Should contain key information
    assert "INTEREST-BEARING DEBT EXTRACTION REPORT" in readable
    assert "Final Interest-Bearing Debt" in readable
    assert "Primary Method" in readable
    assert "METHOD DETAILS" in readable
    
    # Should list components
    if result.primary_method:
        primary = next((m for m in result.all_methods if m.method_name == result.primary_method), None)
        if primary and primary.components:
            assert primary.components[0].name in readable


# Test Edge Cases
def test_empty_data():
    """Test with empty/missing data."""
    result = compute_interest_bearing_debt({}, period="2024-12-31")
    
    assert result.final_value is None
    assert result.primary_method is None
    assert len(result.all_methods) > 0  # Methods should still be attempted


def test_debt_component_repr():
    """Test DebtComponent string representation."""
    comp = DebtComponent(
        name="Short-Term Debt",
        source_type="xbrl",
        source_identifier="us-gaap:ShortTermBorrowings",
        context="Consolidated",
        value=5000000000.0
    )
    
    repr_str = repr(comp)
    assert "Short-Term Debt" in repr_str
    assert "us-gaap:ShortTermBorrowings" in repr_str
    assert "5,000,000,000" in repr_str or "5000000000" in repr_str


def test_debt_method_result_is_reliable():
    """Test reliability check for method results."""
    # Reliable result
    reliable = DebtMethodResult(
        method_name="TEST",
        description="Test",
        components=[DebtComponent("Test", "xbrl", "test:tag", value=1000.0)],
        value=1000.0
    )
    assert reliable.is_reliable() is True
    
    # Unreliable: no value
    unreliable1 = DebtMethodResult(
        method_name="TEST",
        description="Test",
        components=[],
        value=None
    )
    assert unreliable1.is_reliable() is False
    
    # Unreliable: negative value
    unreliable2 = DebtMethodResult(
        method_name="TEST",
        description="Test",
        components=[DebtComponent("Test", "xbrl", "test:tag", value=-1000.0)],
        value=-1000.0
    )
    assert unreliable2.is_reliable() is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

