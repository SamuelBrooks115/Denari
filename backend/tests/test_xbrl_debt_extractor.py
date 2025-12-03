"""
Tests for XBRL debt extractor module.

Tests verify that:
1. Standard us-gaap debt tags are picked up
2. Extension tags with debt keywords are picked up
3. Segment classification works correctly (consolidated vs Ford Credit vs company excl. Ford Credit)
4. The result contains expected DebtFact entries
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

import pytest

from app.xbrl.debt_extractor import (
    DebtExtractionResult,
    DebtFact,
    DebtSegment,
    _is_debt_tag,
    _is_monetary_fact,
    classify_debt_segment,
    extract_debt_facts_from_instance,
)


# ============================================================================
# Test Fixtures - Mock XBRL Data
# ============================================================================

def create_mock_facts_payload(
    company_name: str = "Ford Motor Co",
    cik: str = "0000037996",
    facts: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """Create a mock company facts payload."""
    if facts is None:
        facts = {}
    
    return {
        "cik": cik,
        "entityName": company_name,
        "facts": facts,
    }


def create_mock_tag_node(
    label: str,
    units_data: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Create a mock tag node structure."""
    units: Dict[str, List[Dict[str, Any]]] = {}
    for unit_record in units_data:
        unit_name = unit_record.pop("_unit", "USD")
        if unit_name not in units:
            units[unit_name] = []
        units[unit_name].append(unit_record)
    
    return {
        "label": label,
        "units": units,
    }


# ============================================================================
# Test: Debt Tag Detection
# ============================================================================

def test_is_debt_tag_standard_tags():
    """Test that standard us-gaap debt tags are detected."""
    assert _is_debt_tag("ShortTermBorrowings")
    assert _is_debt_tag("DebtCurrent")
    assert _is_debt_tag("LongTermDebtNoncurrent")
    assert _is_debt_tag("FinanceLeaseLiabilityCurrent")
    assert _is_debt_tag("CommercialPaper")
    
    # Non-debt tags should not be detected
    assert not _is_debt_tag("Assets")
    assert not _is_debt_tag("Revenue")
    assert not _is_debt_tag("CashAndCashEquivalentsAtCarryingValue")


def test_is_debt_tag_extension_tags():
    """Test that extension tags with debt keywords are detected."""
    assert _is_debt_tag("ford:FordCreditDebt")
    assert _is_debt_tag("ford:UnsecuredDebt")
    assert _is_debt_tag("ford:AssetBackedDebt")
    assert _is_debt_tag("company:BorrowingsUnderCreditFacility")
    
    # Check label-based detection
    assert _is_debt_tag("SomeTag", label="Total Debt and Borrowings")
    assert _is_debt_tag("SomeTag", label="Notes Payable")


def test_is_debt_tag_namespace_handling():
    """Test that namespace prefixes are handled correctly."""
    assert _is_debt_tag("us-gaap:ShortTermBorrowings")
    assert _is_debt_tag("ford:FordCreditDebt")
    assert _is_debt_tag("http://www.ford.com/xbrl#Debt")


# ============================================================================
# Test: Monetary Fact Detection
# ============================================================================

def test_is_monetary_fact():
    """Test monetary fact detection."""
    assert _is_monetary_fact({"_unit": "USD", "val": 1000})
    assert _is_monetary_fact({"_unit": "EUR", "val": 1000})
    assert _is_monetary_fact({"val": 1000})  # No unit but numeric
    
    assert not _is_monetary_fact({"_unit": "shares", "val": 1000})
    assert not _is_monetary_fact({"_unit": "pure", "val": 0.5})


# ============================================================================
# Test: Segment Classification
# ============================================================================

def test_classify_debt_segment_consolidated():
    """Test classification of consolidated (dimensionless) facts."""
    # No dimensions
    record = {"val": 1000, "end": "2024-12-31"}
    assert classify_debt_segment(record) == DebtSegment.CONSOLIDATED
    
    # Empty dimensions
    record = {"val": 1000, "end": "2024-12-31", "dimensions": {}}
    assert classify_debt_segment(record) == DebtSegment.CONSOLIDATED


def test_classify_debt_segment_ford_credit():
    """Test classification of Ford Credit segment facts."""
    # Ford Credit via ConsolidationItemsAxis
    record = {
        "val": 1000,
        "end": "2024-12-31",
        "dimensions": {
            "us-gaap:ConsolidationItemsAxis": {
                "value": "Ford Credit Segment"
            }
        }
    }
    assert classify_debt_segment(record) == DebtSegment.FORD_CREDIT
    
    # Ford Credit via segment field
    record = {
        "val": 1000,
        "end": "2024-12-31",
        "segment": {
            "member": "Ford Credit"
        }
    }
    assert classify_debt_segment(record) == DebtSegment.FORD_CREDIT
    
    # Ford Credit via tag/label
    assert classify_debt_segment({}, tag="FordCreditDebt") == DebtSegment.FORD_CREDIT
    assert classify_debt_segment({}, label="Ford Credit Debt") == DebtSegment.FORD_CREDIT


def test_classify_debt_segment_company_excl_ford_credit():
    """Test classification of Company excluding Ford Credit facts."""
    # Company excl. Ford Credit via dimensions
    record = {
        "val": 1000,
        "end": "2024-12-31",
        "dimensions": {
            "us-gaap:ConsolidationItemsAxis": {
                "value": "Company excluding Ford Credit"
            }
        }
    }
    assert classify_debt_segment(record) == DebtSegment.COMPANY_EXCL_FORD_CREDIT
    
    # Automotive segment
    record = {
        "val": 1000,
        "end": "2024-12-31",
        "dimensions": {
            "us-gaap:ConsolidationItemsAxis": {
                "value": "Automotive Segment"
            }
        }
    }
    assert classify_debt_segment(record) == DebtSegment.COMPANY_EXCL_FORD_CREDIT
    
    # Via tag/label
    assert classify_debt_segment({}, tag="CompanyExclFordCreditDebt") == DebtSegment.COMPANY_EXCL_FORD_CREDIT


def test_classify_debt_segment_other():
    """Test classification of other segment facts."""
    # Unknown segment
    record = {
        "val": 1000,
        "end": "2024-12-31",
        "dimensions": {
            "us-gaap:ConsolidationItemsAxis": {
                "value": "Geographic Segment - Europe"
            }
        }
    }
    assert classify_debt_segment(record) == DebtSegment.OTHER


# ============================================================================
# Test: Full Extraction
# ============================================================================

def test_extract_debt_facts_standard_tags():
    """Test extraction of standard us-gaap debt tags."""
    facts_payload = create_mock_facts_payload(
        facts={
            "us-gaap": {
                "LongTermDebtNoncurrent": create_mock_tag_node(
                    label="Long-term debt, noncurrent",
                    units_data=[
                        {
                            "_unit": "USD",
                            "val": 1000000000,
                            "end": "2024-12-31",
                            "form": "10-K",
                            "filed": "2025-02-06",
                            "accn": "0000037996-25-000013",
                        }
                    ],
                ),
                "DebtCurrent": create_mock_tag_node(
                    label="Debt, current",
                    units_data=[
                        {
                            "_unit": "USD",
                            "val": 500000000,
                            "end": "2024-12-31",
                            "form": "10-K",
                            "filed": "2025-02-06",
                            "accn": "0000037996-25-000013",
                        }
                    ],
                ),
                # Non-debt tag (should be excluded)
                "Assets": create_mock_tag_node(
                    label="Assets",
                    units_data=[
                        {
                            "_unit": "USD",
                            "val": 50000000000,
                            "end": "2024-12-31",
                        }
                    ],
                ),
            }
        }
    )
    
    result = extract_debt_facts_from_instance(facts_payload, report_date="2024-12-31")
    
    assert result.company == "Ford Motor Co"
    assert result.cik == 37996
    assert len(result.facts) == 2
    
    # Check facts
    tags = {f.tag for f in result.facts}
    assert "LongTermDebtNoncurrent" in tags
    assert "DebtCurrent" in tags
    
    # Check values
    long_term = next(f for f in result.facts if f.tag == "LongTermDebtNoncurrent")
    assert long_term.value == 1000000000
    assert long_term.segment == DebtSegment.CONSOLIDATED
    assert long_term.is_standard_gaap_tag is True


def test_extract_debt_facts_with_segments():
    """Test extraction with segment classification."""
    facts_payload = create_mock_facts_payload(
        facts={
            "us-gaap": {
                "LongTermDebtNoncurrent": create_mock_tag_node(
                    label="Long-term debt, noncurrent",
                    units_data=[
                        # Consolidated
                        {
                            "_unit": "USD",
                            "val": 1000000000,
                            "end": "2024-12-31",
                            "form": "10-K",
                        },
                        # Ford Credit
                        {
                            "_unit": "USD",
                            "val": 500000000,
                            "end": "2024-12-31",
                            "form": "10-K",
                            "dimensions": {
                                "us-gaap:ConsolidationItemsAxis": {
                                    "value": "Ford Credit Segment"
                                }
                            },
                        },
                        # Company excl. Ford Credit
                        {
                            "_unit": "USD",
                            "val": 500000000,
                            "end": "2024-12-31",
                            "form": "10-K",
                            "dimensions": {
                                "us-gaap:ConsolidationItemsAxis": {
                                    "value": "Company excluding Ford Credit"
                                }
                            },
                        },
                    ],
                ),
            }
        }
    )
    
    result = extract_debt_facts_from_instance(facts_payload, report_date="2024-12-31")
    
    assert len(result.facts) == 3
    
    # Check segments
    consolidated = result.get_consolidated_facts()
    ford_credit = result.get_ford_credit_facts()
    company_excl = result.get_company_excl_ford_credit_facts()
    
    assert len(consolidated) == 1
    assert len(ford_credit) == 1
    assert len(company_excl) == 1
    
    assert consolidated[0].value == 1000000000
    assert ford_credit[0].value == 500000000
    assert company_excl[0].value == 500000000


def test_extract_debt_facts_extension_tags():
    """Test extraction of company extension tags."""
    facts_payload = create_mock_facts_payload(
        facts={
            "us-gaap": {
                "LongTermDebtNoncurrent": create_mock_tag_node(
                    label="Long-term debt, noncurrent",
                    units_data=[
                        {
                            "_unit": "USD",
                            "val": 1000000000,
                            "end": "2024-12-31",
                        }
                    ],
                ),
            },
            "ford": {
                "FordCreditUnsecuredDebt": create_mock_tag_node(
                    label="Ford Credit unsecured debt",
                    units_data=[
                        {
                            "_unit": "USD",
                            "val": 2000000000,
                            "end": "2024-12-31",
                        }
                    ],
                ),
                "AssetBackedDebt": create_mock_tag_node(
                    label="Asset-backed debt",
                    units_data=[
                        {
                            "_unit": "USD",
                            "val": 3000000000,
                            "end": "2024-12-31",
                        }
                    ],
                ),
            }
        }
    )
    
    result = extract_debt_facts_from_instance(facts_payload, report_date="2024-12-31")
    
    assert len(result.facts) == 3
    
    tags = {f.tag for f in result.facts}
    assert "LongTermDebtNoncurrent" in tags
    assert "FordCreditUnsecuredDebt" in tags
    assert "AssetBackedDebt" in tags
    
    # Check namespaces
    ford_facts = [f for f in result.facts if f.namespace == "ford"]
    assert len(ford_facts) == 2
    assert all(f.is_standard_gaap_tag is False for f in ford_facts)


def test_extract_debt_facts_period_filtering():
    """Test that period filtering works correctly."""
    facts_payload = create_mock_facts_payload(
        facts={
            "us-gaap": {
                "LongTermDebtNoncurrent": create_mock_tag_node(
                    label="Long-term debt, noncurrent",
                    units_data=[
                        {
                            "_unit": "USD",
                            "val": 1000000000,
                            "end": "2023-12-31",
                        },
                        {
                            "_unit": "USD",
                            "val": 1200000000,
                            "end": "2024-12-31",
                        },
                    ],
                ),
            }
        }
    )
    
    # Filter by 2024
    result_2024 = extract_debt_facts_from_instance(facts_payload, report_date="2024-12-31")
    assert len(result_2024.facts) == 1
    assert result_2024.facts[0].value == 1200000000
    
    # No filter (all periods)
    result_all = extract_debt_facts_from_instance(facts_payload, report_date=None)
    assert len(result_all.facts) == 2


def test_extract_debt_facts_excludes_non_monetary():
    """Test that non-monetary facts are excluded."""
    facts_payload = create_mock_facts_payload(
        facts={
            "us-gaap": {
                "LongTermDebtNoncurrent": create_mock_tag_node(
                    label="Long-term debt, noncurrent",
                    units_data=[
                        {
                            "_unit": "USD",
                            "val": 1000000000,
                            "end": "2024-12-31",
                        },
                        {
                            "_unit": "shares",  # Non-monetary
                            "val": 1000,
                            "end": "2024-12-31",
                        },
                    ],
                ),
            }
        }
    )
    
    result = extract_debt_facts_from_instance(facts_payload, report_date="2024-12-31")
    
    # Should only have one fact (the USD one)
    assert len(result.facts) == 1
    assert result.facts[0].unit == "USD"


# ============================================================================
# Test: Result Structure
# ============================================================================

def test_debt_extraction_result_structure():
    """Test that DebtExtractionResult has expected structure and methods."""
    result = DebtExtractionResult(
        company="Ford Motor Co",
        cik=37996,
        fiscal_year=2024,
        report_date="2024-12-31",
    )
    
    # Add some test facts
    result.facts = [
        DebtFact(
            tag="LongTermDebtNoncurrent",
            label="Long-term debt, noncurrent",
            value=1000000000,
            unit="USD",
            period_end="2024-12-31",
            segment=DebtSegment.CONSOLIDATED,
        ),
        DebtFact(
            tag="FordCreditDebt",
            label="Ford Credit debt",
            value=500000000,
            unit="USD",
            period_end="2024-12-31",
            segment=DebtSegment.FORD_CREDIT,
        ),
    ]
    
    # Test segment filtering methods
    assert len(result.get_consolidated_facts()) == 1
    assert len(result.get_ford_credit_facts()) == 1
    assert len(result.get_company_excl_ford_credit_facts()) == 0
    assert len(result.get_facts_by_segment(DebtSegment.OTHER)) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

