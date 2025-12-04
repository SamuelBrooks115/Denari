"""
historical_metrics.py — Calculate historical financial metrics from FMP API data.

This module fetches historical financial statements from FMP API and calculates
various metrics including growth rates, margins, and derived ratios.

Used ONLY for the "Create New Project" page to provide historical context.
NOT used for Excel export (which uses only user-entered values).
"""

from typing import Dict, List, Any, Optional
from app.data.fmp_client import (
    fetch_income_statement,
    fetch_balance_sheet,
    fetch_cash_flow,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if denominator is zero."""
    if denominator == 0 or denominator is None:
        return default
    return numerator / denominator


def safe_get(data: Dict[str, Any], key: str, default: Any = 0.0) -> Any:
    """Safely get a value from a dictionary, handling None and missing keys."""
    value = data.get(key)
    if value is None:
        return default
    return value


def calculate_revenue_growth(income_statements: List[Dict[str, Any]]) -> List[float]:
    """
    Calculate revenue growth rates.
    
    Prefers revenueGrowth from income-statement-growth endpoint if available.
    Falls back to calculating: (revenue[t] - revenue[t-1]) / revenue[t-1]
    
    Args:
        income_statements: List of income statement dicts (most recent first)
        
    Returns:
        List of revenue growth rates as decimals (e.g., 0.05 for 5%)
    """
    growth_rates = []
    
    for i in range(len(income_statements)):
        current = income_statements[i]
        
        # Try to get revenueGrowth directly from the data
        revenue_growth = safe_get(current, "revenueGrowth")
        if revenue_growth is not None and revenue_growth != 0:
            growth_rates.append(float(revenue_growth) / 100.0 if abs(revenue_growth) > 1 else float(revenue_growth))
            continue
        
        # Fallback: calculate from consecutive periods
        if i < len(income_statements) - 1:
            prev = income_statements[i + 1]
            current_revenue = safe_get(current, "revenue", 0.0)
            prev_revenue = safe_get(prev, "revenue", 0.0)
            
            growth = safe_divide(current_revenue - prev_revenue, prev_revenue, 0.0)
            growth_rates.append(growth)
        else:
            # Last period, no growth to calculate
            growth_rates.append(0.0)
    
    return growth_rates


def calculate_margins(income_statements: List[Dict[str, Any]]) -> Dict[str, List[float]]:
    """
    Calculate gross margin and operating margin.
    
    Args:
        income_statements: List of income statement dicts (most recent first)
        
    Returns:
        Dict with "grossMargin" and "operatingMargin" lists
    """
    gross_margins = []
    operating_margins = []
    
    for stmt in income_statements:
        revenue = safe_get(stmt, "revenue", 0.0)
        gross_profit = safe_get(stmt, "grossProfit", 0.0)
        operating_income = safe_get(stmt, "operatingIncome", 0.0)
        
        gross_margin = safe_divide(gross_profit, revenue, 0.0)
        operating_margin = safe_divide(operating_income, revenue, 0.0)
        
        gross_margins.append(gross_margin)
        operating_margins.append(operating_margin)
    
    return {
        "grossMargin": gross_margins,
        "operatingMargin": operating_margins,
    }


def calculate_tax_rate(income_statements: List[Dict[str, Any]]) -> List[float]:
    """
    Calculate tax rate: incomeTaxExpense / incomeBeforeTax
    
    Args:
        income_statements: List of income statement dicts (most recent first)
        
    Returns:
        List of tax rates as decimals (e.g., 0.21 for 21%)
    """
    tax_rates = []
    
    for stmt in income_statements:
        income_before_tax = safe_get(stmt, "incomeBeforeTax", 0.0)
        income_tax_expense = safe_get(stmt, "incomeTaxExpense", 0.0)
        
        tax_rate = safe_divide(income_tax_expense, income_before_tax, 0.0)
        tax_rates.append(tax_rate)
    
    return tax_rates


def calculate_depreciation_pct_ppe(
    income_statements: List[Dict[str, Any]],
    balance_sheets: List[Dict[str, Any]]
) -> List[float]:
    """
    Calculate depreciation % of PPE: depreciationAndAmortization / PPE
    
    Args:
        income_statements: List of income statement dicts (most recent first)
        balance_sheets: List of balance sheet dicts (most recent first)
        
    Returns:
        List of depreciation % of PPE as decimals
    """
    depreciation_pcts = []
    
    # Match periods by index (assuming same ordering)
    min_len = min(len(income_statements), len(balance_sheets))
    
    for i in range(min_len):
        dep_amort = safe_get(income_statements[i], "depreciationAndAmortization", 0.0)
        ppe = safe_get(balance_sheets[i], "propertyPlantEquipmentNet", 0.0)
        
        pct = safe_divide(dep_amort, ppe, 0.0)
        depreciation_pcts.append(pct)
    
    # Pad with zeros if lengths don't match
    while len(depreciation_pcts) < len(income_statements):
        depreciation_pcts.append(0.0)
    
    return depreciation_pcts


def calculate_capex_metrics(
    cash_flows: List[Dict[str, Any]],
    balance_sheets: List[Dict[str, Any]],
    income_statements: List[Dict[str, Any]]
) -> Dict[str, List[float]]:
    """
    Calculate CAPEX metrics:
    - CAPEX % of PPE = capitalExpenditure / PPE
    - CAPEX % of Revenue = capitalExpenditure / revenue
    
    Args:
        cash_flows: List of cash flow dicts (most recent first)
        balance_sheets: List of balance sheet dicts (most recent first)
        income_statements: List of income statement dicts (most recent first)
        
    Returns:
        Dict with "capexPctPPE" and "capexPctRevenue" lists
    """
    capex_pct_ppe = []
    capex_pct_revenue = []
    
    min_len = min(len(cash_flows), len(balance_sheets), len(income_statements))
    
    for i in range(min_len):
        capex = abs(safe_get(cash_flows[i], "capitalExpenditure", 0.0))  # Make positive for calculation
        ppe = safe_get(balance_sheets[i], "propertyPlantEquipmentNet", 0.0)
        revenue = safe_get(income_statements[i], "revenue", 0.0)
        
        pct_ppe = safe_divide(capex, ppe, 0.0)
        pct_revenue = safe_divide(capex, revenue, 0.0)
        
        capex_pct_ppe.append(pct_ppe)
        capex_pct_revenue.append(pct_revenue)
    
    # Pad with zeros if lengths don't match
    while len(capex_pct_ppe) < len(cash_flows):
        capex_pct_ppe.append(0.0)
        capex_pct_revenue.append(0.0)
    
    return {
        "capexPctPPE": capex_pct_ppe,
        "capexPctRevenue": capex_pct_revenue,
    }


def normalize_share_repurchases(value: float) -> float:
    """
    Normalize share repurchases to always be negative.
    
    Rules:
    - If value is 1 or -1, return -1
    - Otherwise, return -abs(value)
    
    Args:
        value: Raw share repurchases value
        
    Returns:
        Always negative value
    """
    if value == 1 or value == -1:
        return -1.0
    return -abs(value)


def calculate_dividends_pct_ni(
    cash_flows: List[Dict[str, Any]],
    income_statements: List[Dict[str, Any]]
) -> List[float]:
    """
    Calculate dividends % of Net Income: abs(dividendsPaid) / netIncome
    
    Args:
        cash_flows: List of cash flow dicts (most recent first)
        income_statements: List of income statement dicts (most recent first)
        
    Returns:
        List of dividends % of NI as decimals
    """
    dividends_pcts = []
    
    min_len = min(len(cash_flows), len(income_statements))
    
    for i in range(min_len):
        dividends_paid = abs(safe_get(cash_flows[i], "dividendsPaid", 0.0))
        net_income = safe_get(income_statements[i], "netIncome", 0.0)
        
        pct = safe_divide(dividends_paid, net_income, 0.0)
        dividends_pcts.append(pct)
    
    # Pad with zeros if lengths don't match
    while len(dividends_pcts) < len(cash_flows):
        dividends_pcts.append(0.0)
    
    return dividends_pcts


def calculate_change_in_working_capital(balance_sheets: List[Dict[str, Any]]) -> List[float]:
    """
    Calculate change in working capital.
    
    workingCapital = totalCurrentAssets - totalCurrentLiabilities
    changeInWC = workingCapital[t] - workingCapital[t-1]
    
    Args:
        balance_sheets: List of balance sheet dicts (most recent first)
        
    Returns:
        List of change in working capital values
    """
    changes = []
    
    for i in range(len(balance_sheets)):
        current = balance_sheets[i]
        current_assets = safe_get(current, "totalCurrentAssets", 0.0)
        current_liabilities = safe_get(current, "totalCurrentLiabilities", 0.0)
        working_capital = current_assets - current_liabilities
        
        if i < len(balance_sheets) - 1:
            prev = balance_sheets[i + 1]
            prev_assets = safe_get(prev, "totalCurrentAssets", 0.0)
            prev_liabilities = safe_get(prev, "totalCurrentLiabilities", 0.0)
            prev_working_capital = prev_assets - prev_liabilities
            
            change = working_capital - prev_working_capital
            changes.append(change)
        else:
            # Last period, no change to calculate
            changes.append(0.0)
    
    return changes


def fetch_and_calculate_historical_metrics(ticker: str, limit: int = 40) -> Dict[str, Any]:
    """
    Fetch historical financial data from FMP API and calculate all metrics.
    
    This function:
    1. Fetches income statements, balance sheets, and cash flow statements
    2. Calculates all historical metrics
    3. Returns structured data ready for storage in project JSON
    
    Args:
        ticker: Stock ticker symbol (e.g., "F" for Ford)
        limit: Number of periods to fetch (default: 40, minimum 5)
        
    Returns:
        Dict with structure:
        {
            "ticker": str,
            "historicals": {
                "revenueGrowth": List[float],
                "grossMargin": List[float],
                "operatingMargin": List[float],
                "taxRate": List[float],
                "depreciationPctPPE": List[float],
                "totalDebt": List[float],
                "inventory": List[float],
                "capexPctPPE": List[float],
                "capexPctRevenue": List[float],
                "shareRepurchases": List[float],  # Always negative
                "dividendsPctNI": List[float],
                "changeInWorkingCapital": List[float],
            }
        }
        
    Raises:
        RuntimeError: If API calls fail or data is insufficient
    """
    logger.info(f"Fetching historical metrics for {ticker} (limit={limit})")
    
    # Ensure minimum limit of 5
    limit = max(limit, 5)
    
    try:
        # Fetch all three statement types
        income_statements = fetch_income_statement(ticker, limit=limit)
        balance_sheets = fetch_balance_sheet(ticker, limit=limit)
        cash_flows = fetch_cash_flow(ticker, limit=limit)
        
        if not income_statements or len(income_statements) < 2:
            raise RuntimeError(f"Insufficient income statement data for {ticker}")
        
        if not balance_sheets or len(balance_sheets) < 2:
            raise RuntimeError(f"Insufficient balance sheet data for {ticker}")
        
        if not cash_flows or len(cash_flows) < 2:
            raise RuntimeError(f"Insufficient cash flow data for {ticker}")
        
        # Calculate all metrics
        revenue_growth = calculate_revenue_growth(income_statements)
        margins = calculate_margins(income_statements)
        tax_rates = calculate_tax_rate(income_statements)
        depreciation_pct_ppe = calculate_depreciation_pct_ppe(income_statements, balance_sheets)
        capex_metrics = calculate_capex_metrics(cash_flows, balance_sheets, income_statements)
        dividends_pct_ni = calculate_dividends_pct_ni(cash_flows, income_statements)
        change_in_wc = calculate_change_in_working_capital(balance_sheets)
        
        # Extract simple lists from balance sheets and cash flows
        total_debt = [safe_get(bs, "totalDebt", 0.0) for bs in balance_sheets]
        inventory = [safe_get(bs, "inventory", 0.0) for bs in balance_sheets]
        
        # Extract share repurchases and normalize to always be negative
        share_repurchases_raw = [safe_get(cf, "commonStockRepurchased", 0.0) for cf in cash_flows]
        share_repurchases = [normalize_share_repurchases(val) for val in share_repurchases_raw]
        
        # Build result structure
        result = {
            "ticker": ticker,
            "historicals": {
                "revenueGrowth": revenue_growth,
                "grossMargin": margins["grossMargin"],
                "operatingMargin": margins["operatingMargin"],
                "taxRate": tax_rates,
                "depreciationPctPPE": depreciation_pct_ppe,
                "totalDebt": total_debt,
                "inventory": inventory,
                "capexPctPPE": capex_metrics["capexPctPPE"],
                "capexPctRevenue": capex_metrics["capexPctRevenue"],
                "shareRepurchases": share_repurchases,
                "dividendsPctNI": dividends_pct_ni,
                "changeInWorkingCapital": change_in_wc,
            }
        }
        
        logger.info(f"Successfully calculated historical metrics for {ticker}")
        return result
        
    except Exception as e:
        logger.error(f"Error fetching/calculating historical metrics for {ticker}: {e}")
        raise RuntimeError(f"Failed to fetch historical metrics for {ticker}: {str(e)}") from e

