"""
three_statement.py — Forward Financial Projections (3-Statement Model)

Purpose:
- Generate forecasted:
    * Income Statement (Revenue → EBIT → Net Income)
    * Balance Sheet (minimal for MVP)
    * Cash Flow Statement (Free Cash Flow focus)

This module is unit-testable without Excel and uses structured dataclass outputs.
"""

from typing import Dict, Any, List

from app.services.modeling.types import (
    CompanyModelInput,
    ThreeStatementOutput,
)


def run_three_statement(
    model_input: CompanyModelInput,
    assumptions: Dict[str, Any],
    forecast_periods: int = 5,
    frequency: str = "annual",
) -> ThreeStatementOutput:
    """
    Main entrypoint for generating forward projections (MVP - no database).

    Args:
        model_input: CompanyModelInput with historical financial data
        assumptions: Dict with keys:
            - revenue_growth: float (annual growth rate, e.g., 0.08 for 8%)
            - operating_margin_target: float (target operating margin)
            - tax_rate: float (effective tax rate, e.g., 0.21 for 21%)
            - capex_as_pct_revenue: float (CapEx as % of revenue)
            - depreciation_as_pct_revenue: float (D&A as % of revenue)
        forecast_periods: Number of periods to project forward
        frequency: "annual" or "quarterly"

    Returns:
        ThreeStatementOutput with IS/BS/CF projections
    """
    # Extract historical data from CompanyModelInput
    historicals = model_input.historicals.by_role
    
    # Find the latest year with data
    all_years = set()
    for role_values in historicals.values():
        all_years.update(role_values.keys())
    
    if not all_years:
        raise ValueError("No historical financial data provided")
    
    latest_year = max(all_years)
    
    # Extract latest year values by model_role
    latest_revenue = historicals.get("IS_REVENUE", {}).get(latest_year, 0.0)
    latest_cogs = historicals.get("IS_COGS", {}).get(latest_year, 0.0)
    latest_opex = historicals.get("IS_OPERATING_EXPENSE", {}).get(latest_year, 0.0)
    latest_net_income = historicals.get("IS_NET_INCOME", {}).get(latest_year, 0.0)
    latest_capex = historicals.get("CF_CAPEX", {}).get(latest_year, 0.0)
    latest_depreciation = historicals.get("CF_DEPRECIATION", {}).get(latest_year, 0.0)

    # Extract assumptions with defaults
    revenue_growth = assumptions.get("revenue_growth", 0.05)  # 5% default
    operating_margin_target = assumptions.get("operating_margin_target", 0.15)  # 15% default
    tax_rate = assumptions.get("tax_rate", 0.21)  # 21% default
    capex_as_pct_revenue = assumptions.get("capex_as_pct_revenue", 0.05)  # 5% default
    depreciation_as_pct_revenue = assumptions.get("depreciation_as_pct_revenue", 0.03)  # 3% default

    # Validate latest revenue
    if latest_revenue <= 0:
        raise ValueError("Latest period revenue is missing or zero")

    # Initialize projection arrays
    projected_periods: List[str] = []
    revenue_proj: List[float] = []
    cogs_proj: List[float] = []
    gross_profit_proj: List[float] = []
    operating_expense_proj: List[float] = []
    operating_income_proj: List[float] = []
    net_income_proj: List[float] = []
    capex_proj: List[float] = []
    depreciation_proj: List[float] = []
    fcf_proj: List[float] = []

    # Calculate historical margins
    cogs_margin = latest_cogs / latest_revenue if latest_revenue > 0 else 0.0
    opex_margin = latest_opex / latest_revenue if latest_revenue > 0 else 0.0

    # Start projection from latest year
    current_revenue = latest_revenue
    base_year = latest_year

    for i in range(forecast_periods):
        # Calculate next period date
        if frequency == "annual":
            next_year = base_year + i + 1
            next_period = f"{next_year}-12-31"
        else:  # quarterly
            # Simplified: assume Q1, Q2, Q3, Q4
            quarter = (i % 4) + 1
            year = base_year + (i // 4)
            next_period = f"{year}-{quarter*3:02d}-{30 if quarter in [3, 4] else 31}"

        projected_periods.append(next_period)

        # Project revenue
        current_revenue = current_revenue * (1 + revenue_growth)
        revenue_proj.append(current_revenue)

        # Project COGS (maintain margin)
        cogs = current_revenue * cogs_margin
        cogs_proj.append(cogs)

        # Gross profit
        gross_profit = current_revenue - cogs
        gross_profit_proj.append(gross_profit)

        # Operating expenses (maintain margin, but allow for target margin adjustment)
        # If target margin is specified, adjust opex to hit target
        target_opex = current_revenue * (1 - operating_margin_target) - cogs
        if target_opex < 0:
            # Can't hit target margin with current COGS margin
            opex = current_revenue * opex_margin
        else:
            # Blend historical and target
            opex = current_revenue * opex_margin * 0.7 + target_opex * 0.3
        operating_expense_proj.append(opex)

        # Operating income
        operating_income = gross_profit - opex
        operating_income_proj.append(operating_income)

        # Net income (simplified: operating income * (1 - tax_rate))
        # In reality, need to account for interest, etc.
        net_income = operating_income * (1 - tax_rate)
        net_income_proj.append(net_income)

        # CapEx and Depreciation
        capex = current_revenue * capex_as_pct_revenue
        capex_proj.append(capex)
        depreciation = current_revenue * depreciation_as_pct_revenue
        depreciation_proj.append(depreciation)

        # Free Cash Flow (simplified)
        # FCF = Net Income + D&A - CapEx
        # (MVP: ignoring working capital changes)
        fcf = net_income + depreciation - capex
        fcf_proj.append(fcf)

    return ThreeStatementOutput(
        periods=projected_periods,
        revenue=revenue_proj,
        cogs=cogs_proj,
        gross_profit=gross_profit_proj,
        operating_expense=operating_expense_proj,
        operating_income=operating_income_proj,
        net_income=net_income_proj,
        capex=capex_proj,
        depreciation=depreciation_proj,
        free_cash_flow=fcf_proj,
    )
