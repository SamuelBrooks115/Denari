"""
types.py — Shared Data Layer for Modeling Modules

Purpose:
- Define common data structures used across modeling modules
- Provide helpers for extracting and aggregating historical financial data
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


Year = int


@dataclass
class HistoricalSeries:
    """
    Historical financial data aggregated by model_role and year.
    
    Example:
        by_role = {
            "IS_REVENUE": {2022: 1000000.0, 2023: 1100000.0},
            "IS_COGS": {2022: 600000.0, 2023: 660000.0}
        }
    """
    by_role: Dict[str, Dict[Year, float]]


@dataclass
class CompanyModelInput:
    """
    Input data structure for modeling modules.
    
    Contains company identification and historical financial data.
    """
    ticker: str
    name: str
    historicals: HistoricalSeries


def build_historical_series(line_items: List[Dict[str, Any]]) -> HistoricalSeries:
    """
    Build HistoricalSeries from structured JSON line items.
    
    Aggregates values by model_role and year. Multiple items with the same
    model_role for a given year are summed.
    
    Args:
        line_items: List of line item dictionaries from JSON
            Each item should have:
            - "model_role": str (e.g., "IS_REVENUE")
            - "periods": Dict[str, float] (e.g., {"2022-12-31": 1000000.0})
        
    Returns:
        HistoricalSeries with aggregated data by role and year
    """
    by_role: Dict[str, Dict[int, float]] = defaultdict(lambda: defaultdict(float))
    
    for item in line_items:
        role = (item.get("model_role") or "").strip()
        if not role:
            continue
        
        periods = item.get("periods") or {}
        for period_str, raw_val in periods.items():
            if period_str is None or raw_val is None:
                continue
            
            # Extract year from YYYY-MM-DD format
            try:
                year = int(str(period_str).split("-")[0])
                val = float(raw_val)
                by_role[role][year] += val
            except (ValueError, IndexError, TypeError):
                # Skip invalid periods/values
                continue
    
    return HistoricalSeries(by_role=dict(by_role))


def build_company_model_input_from_normalized_facts(
    ticker: str,
    name: str,
    financials_by_statement: Dict[str, Dict[str, Dict[str, float]]],
    periods: List[str],
) -> CompanyModelInput:
    """
    Build CompanyModelInput from normalized facts structure (from fetch_company_live).
    
    Converts normalized facts organized by statement type and period into line items
    with model_role, then builds HistoricalSeries.
    
    Args:
        ticker: Company ticker symbol
        name: Company name
        financials_by_statement: Dict organized as:
            {
                "IS": {"2022-12-31": {"Revenues": 1000000.0, ...}, ...},
                "BS": {"2022-12-31": {"Assets": 5000000.0, ...}, ...},
                "CF": {"2022-12-31": {"NetCashFlow": 200000.0, ...}, ...}
            }
        periods: List of period end dates (YYYY-MM-DD format)
        
    Returns:
        CompanyModelInput with company info and historical data
    """
    # Simple tag-to-model_role mapping for common tags
    # This is a simplified mapping - in production, use structured_output classification
    TAG_TO_MODEL_ROLE: Dict[str, str] = {
        # Income Statement
        "Revenues": "IS_REVENUE",
        "RevenueFromContractWithCustomerExcludingAssessedTax": "IS_REVENUE",
        "CostOfGoodsAndServicesSold": "IS_COGS",
        "CostOfRevenue": "IS_COGS",
        "OperatingExpenses": "IS_OPERATING_EXPENSE",
        "SellingGeneralAndAdministrativeExpense": "IS_OPERATING_EXPENSE",
        "ResearchAndDevelopmentExpense": "IS_OPERATING_EXPENSE",
        "OperatingIncomeLoss": "IS_OPERATING_INCOME",
        "IncomeBeforeEquityMethodInvestments": "IS_PRETAX_INCOME",
        "IncomeTaxExpenseBenefit": "IS_TAX_EXPENSE",
        "NetIncomeLoss": "IS_NET_INCOME",
        # Balance Sheet
        "CashAndCashEquivalentsAtCarryingValue": "BS_CASH",
        "Assets": "BS_ASSETS",
        "PropertyPlantAndEquipmentNet": "BS_PP_AND_E",
        "InventoryNet": "BS_INVENTORY",
        "AccountsReceivableNetCurrent": "BS_ACCOUNTS_RECEIVABLE",
        "AccountsPayableCurrent": "BS_ACCOUNTS_PAYABLE",
        "Liabilities": "BS_LIABILITIES",
        "LongTermDebt": "BS_TOTAL_DEBT",
        "DebtCurrent": "BS_TOTAL_DEBT",
        # Cash Flow
        "NetCashProvidedByUsedInOperatingActivities": "CF_NET_INCOME",  # Approximation
        "DepreciationDepletionAndAmortization": "CF_DEPRECIATION",
        "CapitalExpenditures": "CF_CAPEX",
        "PaymentsForRepurchaseOfCommonStock": "CF_SHARE_REPURCHASES",
        "PaymentsOfDividends": "CF_DIVIDENDS_PAID",
    }
    
    # Convert normalized facts to line items with model_role
    line_items: List[Dict[str, Any]] = []
    
    for stmt_type, periods_dict in financials_by_statement.items():
        for period_end, metrics in periods_dict.items():
            for tag, value in metrics.items():
                # Map tag to model_role
                model_role = TAG_TO_MODEL_ROLE.get(tag, "")
                if not model_role:
                    # Skip tags we don't know how to map
                    continue
                
                # Check if we already have a line item for this tag
                existing_item = None
                for item in line_items:
                    if item.get("tag") == tag:
                        existing_item = item
                        break
                
                if existing_item:
                    # Add period to existing item
                    existing_item["periods"][period_end] = value
                else:
                    # Create new line item
                    line_items.append({
                        "tag": tag,
                        "label": tag,  # Use tag as label fallback
                        "model_role": model_role,
                        "unit": "USD",  # Default unit
                        "periods": {period_end: value},
                    })
    
    # Build historical series
    historicals = build_historical_series(line_items)
    
    return CompanyModelInput(
        ticker=ticker,
        name=name,
        historicals=historicals
    )


def build_company_model_input(json_data: Dict[str, Any]) -> CompanyModelInput:
    """
    Build CompanyModelInput from structured JSON data.
    
    Extracts company info and builds historical series from line items.
    
    Args:
        json_data: Structured JSON data with:
            - "company": Dict with "ticker" and "company_name"
            - "filings": List[Dict] (multi-year) OR "statements": Dict (single-year)
        
    Returns:
        CompanyModelInput with company info and historical data
    """
    # Extract company info
    company_info = json_data.get("company", {})
    ticker = company_info.get("ticker", "").strip()
    name = company_info.get("company_name", "").strip()
    
    if not ticker:
        raise ValueError("JSON data must contain company.ticker")
    
    # Extract line items (reuse logic from excel_export.py)
    line_items: List[Dict[str, Any]] = []
    
    # Check if it's multi-year format (has "filings" key)
    if "filings" in json_data:
        filings = json_data.get("filings", [])
        for filing in filings:
            statements = filing.get("statements", {})
            for stmt_type, stmt_data in statements.items():
                if isinstance(stmt_data, dict):
                    items = stmt_data.get("line_items", [])
                    line_items.extend(items)
    # Check if it's single-year format (has "statements" key at root)
    elif "statements" in json_data:
        statements = json_data.get("statements", {})
        for stmt_type, stmt_data in statements.items():
            if isinstance(stmt_data, dict):
                items = stmt_data.get("line_items", [])
                line_items.extend(items)
    
    # Build historical series
    historicals = build_historical_series(line_items)
    
    return CompanyModelInput(
        ticker=ticker,
        name=name,
        historicals=historicals
    )


# ============================================================================
# Output Dataclasses for Modeling Modules
# ============================================================================


@dataclass
class DcfYearResult:
    """Yearly DCF calculation result."""
    year: Year
    ufcf: float  # Unlevered Free Cash Flow
    discount_factor: float
    pv_ufcf: float  # Present Value of UFCF


@dataclass
class DcfOutput:
    """DCF valuation output."""
    yearly_results: List[DcfYearResult]
    terminal_value: float
    pv_terminal_value: float
    enterprise_value: float
    equity_value: Optional[float]
    implied_share_price: Optional[float]
    wacc: float
    terminal_growth_rate: float


@dataclass
class ThreeStatementOutput:
    """3-Statement model output with IS/BS/CF projections."""
    periods: List[str]  # Period end dates (YYYY-MM-DD)
    # Income Statement
    revenue: List[float]
    cogs: List[float]
    gross_profit: List[float]
    operating_expense: List[float]
    operating_income: List[float]
    net_income: List[float]
    # Cash Flow Statement
    capex: List[float]
    depreciation: List[float]
    free_cash_flow: List[float]
    # Balance Sheet (minimal for MVP)
    # Can be extended later with assets, liabilities, equity


@dataclass
class ComparableCompany:
    """Single comparable company data."""
    name: str
    ev_ebitda: Optional[float]
    pe: Optional[float]
    ev_sales: Optional[float]


@dataclass
class RelativeValuationOutput:
    """Relative valuation (comps) output."""
    subject_company: str
    subject_metrics: Dict[str, float]  # revenue, ebitda, net_income
    comparables: List[ComparableCompany]
    implied_values: Dict[str, Optional[float]]  # ev_ebitda_implied, pe_implied, etc.

