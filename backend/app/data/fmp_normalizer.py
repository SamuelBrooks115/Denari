"""
fmp_normalizer.py — Normalize FMP raw data into internal schema.

This module converts FMP's standardized JSON fields into a single,
normalized view for a given ticker and fiscal year.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class NormalizedFinancials:
    """
    Normalized financial data for a single company and fiscal year.
    
    This dataclass represents a unified view of income statement, balance sheet,
    and cash flow data for a specific fiscal year.
    """
    ticker: str
    fiscal_year: int
    period_end_date: str
    
    # Income statement
    revenue: Optional[float] = None
    cost_of_revenue: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_expenses: Optional[float] = None
    operating_income: Optional[float] = None
    ebitda: Optional[float] = None
    pretax_income: Optional[float] = None
    income_tax_expense: Optional[float] = None
    net_income: Optional[float] = None
    
    # Balance sheet
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    cash_and_equivalents: Optional[float] = None
    inventory: Optional[float] = None
    accounts_receivable: Optional[float] = None
    accounts_payable: Optional[float] = None
    accrued_expenses: Optional[float] = None
    ppe_net: Optional[float] = None
    total_debt: Optional[float] = None
    
    # Cash flow
    dividends_paid: Optional[float] = None
    share_repurchases: Optional[float] = None


def _safe_float(value: Any) -> Optional[float]:
    """
    Safely convert value to float, returning None if conversion fails.
    
    Args:
        value: Value to convert (can be None, string, int, float)
        
    Returns:
        Float value or None
    """
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _find_statement_for_year(
    statements: List[Dict[str, Any]],
    fiscal_year: int,
) -> Optional[Dict[str, Any]]:
    """
    Find the statement entry matching the given fiscal year.
    
    FMP statements typically have 'calendarYear' or 'date' fields.
    We match on calendarYear if available, otherwise try to parse date.
    
    Args:
        statements: List of statement dictionaries (most recent first)
        fiscal_year: Target fiscal year (e.g., 2024)
        
    Returns:
        Matching statement dictionary or None
    """
    for stmt in statements:
        # Try calendarYear first (most common)
        if "calendarYear" in stmt and stmt["calendarYear"]:
            try:
                year = int(stmt["calendarYear"])
                if year == fiscal_year:
                    return stmt
            except (ValueError, TypeError):
                continue
        
        # Try date field (format: "YYYY-MM-DD")
        if "date" in stmt and stmt["date"]:
            try:
                date_str = str(stmt["date"])
                year = int(date_str.split("-")[0])
                if year == fiscal_year:
                    return stmt
            except (ValueError, TypeError, IndexError):
                continue
    
    return None


def normalize_for_year(
    ticker: str,
    fiscal_year: int,
    income_stmt_raw: List[Dict[str, Any]],
    balance_sheet_raw: List[Dict[str, Any]],
    cash_flow_raw: List[Dict[str, Any]],
) -> NormalizedFinancials:
    """
    Normalize FMP raw data for a specific fiscal year.
    
    Args:
        ticker: Stock ticker symbol
        fiscal_year: Target fiscal year
        income_stmt_raw: List of income statement dictionaries from FMP
        balance_sheet_raw: List of balance sheet dictionaries from FMP
        cash_flow_raw: List of cash flow statement dictionaries from FMP
        
    Returns:
        NormalizedFinancials dataclass instance
        
    Raises:
        ValueError: If no statement found for the given fiscal year
    """
    # Find statements for the target fiscal year
    income_stmt = _find_statement_for_year(income_stmt_raw, fiscal_year)
    balance_sheet = _find_statement_for_year(balance_sheet_raw, fiscal_year)
    cash_flow = _find_statement_for_year(cash_flow_raw, fiscal_year)
    
    if not income_stmt and not balance_sheet and not cash_flow:
        raise ValueError(
            f"No financial statements found for {ticker} fiscal year {fiscal_year}. "
            f"Available years may differ. Check the raw data files."
        )
    
    # Extract period end date (prefer from income statement, fallback to others)
    period_end_date = None
    if income_stmt:
        period_end_date = income_stmt.get("date") or income_stmt.get("period")
    elif balance_sheet:
        period_end_date = balance_sheet.get("date") or balance_sheet.get("period")
    elif cash_flow:
        period_end_date = cash_flow.get("date") or cash_flow.get("period")
    
    if not period_end_date:
        period_end_date = f"{fiscal_year}-12-31"  # Default fallback
    
    # Extract income statement fields
    revenue = _safe_float(income_stmt.get("revenue") if income_stmt else None)
    cost_of_revenue = _safe_float(
        income_stmt.get("costOfRevenue") if income_stmt else None
    )
    gross_profit = _safe_float(
        income_stmt.get("grossProfit") if income_stmt else None
    )
    operating_expenses = _safe_float(
        income_stmt.get("operatingExpenses") if income_stmt else None
    )
    operating_income = _safe_float(
        income_stmt.get("operatingIncome") if income_stmt else None
    )
    ebitda = _safe_float(income_stmt.get("ebitda") if income_stmt else None)
    pretax_income = _safe_float(
        income_stmt.get("incomeBeforeTax")
        or income_stmt.get("incomeBeforeTaxAndMinorityInterest")
        if income_stmt
        else None
    )
    income_tax_expense = _safe_float(
        income_stmt.get("incomeTaxExpense") if income_stmt else None
    )
    net_income = _safe_float(income_stmt.get("netIncome") if income_stmt else None)
    
    # Extract balance sheet fields
    total_assets = _safe_float(
        balance_sheet.get("totalAssets") if balance_sheet else None
    )
    total_liabilities = _safe_float(
        balance_sheet.get("totalLiabilities") if balance_sheet else None
    )
    cash_and_equivalents = _safe_float(
        balance_sheet.get("cashAndCashEquivalents")
        or balance_sheet.get("cashAndShortTermInvestments")
        if balance_sheet
        else None
    )
    inventory = _safe_float(
        balance_sheet.get("inventory") if balance_sheet else None
    )
    accounts_receivable = _safe_float(
        balance_sheet.get("accountsReceivables")
        or balance_sheet.get("netReceivables")
        if balance_sheet
        else None
    )
    accounts_payable = _safe_float(
        balance_sheet.get("accountPayables")
        or balance_sheet.get("accountsPayables")
        if balance_sheet
        else None
    )
    accrued_expenses = _safe_float(
        balance_sheet.get("otherCurrentLiabilities")
        or balance_sheet.get("accruedLiabilities")
        if balance_sheet
        else None
    )
    ppe_net = _safe_float(
        balance_sheet.get("propertyPlantEquipmentNet")
        or balance_sheet.get("netPPE")
        if balance_sheet
        else None
    )
    
    # Calculate total_debt from multiple components
    total_debt = None
    if balance_sheet:
        short_term_debt = _safe_float(balance_sheet.get("shortTermDebt"))
        long_term_debt = _safe_float(balance_sheet.get("longTermDebt"))
        long_term_debt_noncurrent = _safe_float(
            balance_sheet.get("longTermDebtNoncurrent")
        )
        other_current_borrowings = _safe_float(
            balance_sheet.get("otherCurrentBorrowings")
        )
        
        # Try FMP's totalDebt field first
        total_debt = _safe_float(balance_sheet.get("totalDebt"))
        
        # If not available, sum components
        if total_debt is None:
            components = [
                short_term_debt,
                long_term_debt,
                long_term_debt_noncurrent,
                other_current_borrowings,
            ]
            valid_components = [c for c in components if c is not None]
            if valid_components:
                total_debt = sum(valid_components)
    
    # Extract cash flow fields
    dividends_paid = _safe_float(
        cash_flow.get("dividendsPaid") if cash_flow else None
    )
    share_repurchases = _safe_float(
        cash_flow.get("stockRepurchases")
        or cash_flow.get("repurchaseOfCommonStock")
        or cash_flow.get("commonStockRepurchased")
        if cash_flow
        else None
    )
    
    return NormalizedFinancials(
        ticker=ticker,
        fiscal_year=fiscal_year,
        period_end_date=str(period_end_date),
        revenue=revenue,
        cost_of_revenue=cost_of_revenue,
        gross_profit=gross_profit,
        operating_expenses=operating_expenses,
        operating_income=operating_income,
        ebitda=ebitda,
        pretax_income=pretax_income,
        income_tax_expense=income_tax_expense,
        net_income=net_income,
        total_assets=total_assets,
        total_liabilities=total_liabilities,
        cash_and_equivalents=cash_and_equivalents,
        inventory=inventory,
        accounts_receivable=accounts_receivable,
        accounts_payable=accounts_payable,
        accrued_expenses=accrued_expenses,
        ppe_net=ppe_net,
        total_debt=total_debt,
        dividends_paid=dividends_paid,
        share_repurchases=share_repurchases,
    )

