"""
scenarios.py — Bear/Bull/Base Scenario Analysis

Purpose:
- Build Bear, Bull, and Base case scenarios for DCF analysis
- Base case: Uses projections from three_statement.py (references 3-statement Excel tab)
- Bear/Bull cases: Build projections from direct assumptions (same calculation logic)
- All scenarios use the same DCF calculation and Excel export format

Key Differences:
- Base: References 3-statement Excel tab for projections
- Bear/Bull: Uses direct assumptions, built from latest historical year
- All three scenarios have identical Excel layout and formulas
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from app.services.modeling.three_statement import run_three_statement
from app.services.modeling.dcf import run_dcf


def build_scenario_projections(
    latest_historical: Dict[str, float],
    assumptions: Dict[str, Any],
    forecast_periods: int = 5,
    frequency: str = "annual",
) -> Dict[str, Any]:
    """
    Build financial projections for a scenario from direct assumptions.
    
    This function uses the same calculation logic as run_three_statement() but
    builds projections from direct assumptions rather than referencing Excel.
    Used for Bear and Bull scenarios.
    
    Args:
        latest_historical: Dict with latest historical financial data:
            - revenue: float
            - cogs: float (optional, can be calculated from margin)
            - operating_expense: float (optional, can be calculated from margin)
            - net_income: float (optional)
        assumptions: Dict with scenario-specific assumptions:
            - revenue_growth: float (annual growth rate, e.g., 0.08 for 8%)
            - gross_profit_margin: float (e.g., 0.40 for 40%)
            - ebit_margin: float (e.g., 0.15 for 15%)
            - tax_rate: float (e.g., 0.21 for 21%)
            - depreciation_amortization: float or None (if None, calculated as % of revenue)
            - depreciation_as_pct_revenue: float (e.g., 0.03 for 3%)
            - capex: float or None (if None, calculated as % of revenue)
            - capex_as_pct_revenue: float (e.g., 0.05 for 5%)
            - working_capital_change: float or None (if None, calculated as % of revenue)
            - working_capital_as_pct_revenue: float (e.g., 0.02 for 2%)
        forecast_periods: Number of periods to project (default: 5)
        frequency: "annual" or "quarterly" (default: "annual")
    
    Returns:
        Dictionary with projections (same format as run_three_statement):
        {
          "periods": [str, ...],  # Period end dates
          "revenue": [float, ...],
          "cogs": [float, ...],
          "gross_profit": [float, ...],
          "operating_expense": [float, ...],
          "operating_income": [float, ...],
          "net_income": [float, ...],
          "free_cash_flow": [float, ...],
          "capex": [float, ...],
          "depreciation": [float, ...],
        }
    """
    if not latest_historical.get("revenue"):
        raise ValueError("Latest historical revenue is required")
    
    # Extract latest historical data
    base_revenue = latest_historical["revenue"]
    base_cogs = latest_historical.get("cogs", 0.0)
    base_operating_expense = latest_historical.get("operating_expense", 0.0)
    
    # Extract assumptions with defaults
    revenue_growth = assumptions.get("revenue_growth", 0.05)
    gross_profit_margin = assumptions.get("gross_profit_margin")
    ebit_margin = assumptions.get("ebit_margin")
    tax_rate = assumptions.get("tax_rate", 0.21)
    
    # D&A assumptions
    depreciation_amortization = assumptions.get("depreciation_amortization")
    depreciation_as_pct_revenue = assumptions.get("depreciation_as_pct_revenue", 0.03)
    
    # CapEx assumptions
    capex = assumptions.get("capex")
    capex_as_pct_revenue = assumptions.get("capex_as_pct_revenue", 0.05)
    
    # Working capital assumptions
    working_capital_change = assumptions.get("working_capital_change")
    working_capital_as_pct_revenue = assumptions.get("working_capital_as_pct_revenue", 0.02)
    
    # Calculate base margins if not provided
    if gross_profit_margin is None:
        if base_cogs > 0:
            gross_profit_margin = (base_revenue - base_cogs) / base_revenue
        else:
            gross_profit_margin = 0.40  # Default 40%
    
    if ebit_margin is None:
        base_operating_income = base_revenue - base_cogs - base_operating_expense
        if base_revenue > 0:
            ebit_margin = base_operating_income / base_revenue
        else:
            ebit_margin = 0.15  # Default 15%
    
    # Generate period dates
    projected_periods = []
    revenue_proj = []
    cogs_proj = []
    gross_profit_proj = []
    operating_expense_proj = []
    operating_income_proj = []
    net_income_proj = []
    capex_proj = []
    depreciation_proj = []
    fcf_proj = []
    
    # Start from next period after latest historical
    if frequency == "annual":
        period_delta = timedelta(days=365)
    else:  # quarterly
        period_delta = timedelta(days=90)
    
    # Get latest period date (assume current date if not provided)
    latest_date_str = latest_historical.get("period_end")
    if latest_date_str:
        try:
            latest_date = datetime.strptime(latest_date_str, "%Y-%m-%d")
        except (ValueError, TypeError):
            latest_date = datetime.now()
    else:
        latest_date = datetime.now()
    
    current_revenue = base_revenue
    
    for i in range(forecast_periods):
        # Calculate period date
        period_date = latest_date + period_delta * (i + 1)
        projected_periods.append(period_date.strftime("%Y-%m-%d"))
        
        # Revenue projection
        current_revenue = current_revenue * (1 + revenue_growth)
        revenue_proj.append(current_revenue)
        
        # COGS (from gross profit margin)
        cogs = current_revenue * (1 - gross_profit_margin)
        cogs_proj.append(cogs)
        
        # Gross profit
        gross_profit = current_revenue - cogs
        gross_profit_proj.append(gross_profit)
        
        # Operating expenses (to achieve target EBIT margin)
        target_operating_income = current_revenue * ebit_margin
        operating_expense = gross_profit - target_operating_income
        operating_expense_proj.append(operating_expense)
        
        # Operating income (EBIT)
        operating_income = gross_profit - operating_expense
        operating_income_proj.append(operating_income)
        
        # Depreciation & Amortization
        if depreciation_amortization is not None:
            # Use absolute value if provided
            depreciation = depreciation_amortization
        else:
            # Calculate as % of revenue
            depreciation = current_revenue * depreciation_as_pct_revenue
        depreciation_proj.append(depreciation)
        
        # CapEx
        if capex is not None:
            # Use absolute value if provided
            current_capex = capex
        else:
            # Calculate as % of revenue
            current_capex = current_revenue * capex_as_pct_revenue
        capex_proj.append(current_capex)
        
        # Net Income (EBIT - Taxes)
        # Tax is applied to EBIT (simplified - ignoring interest, etc.)
        taxes = operating_income * tax_rate
        net_income = operating_income - taxes
        net_income_proj.append(net_income)
        
        # Working Capital Change
        if working_capital_change is not None:
            # Use absolute value if provided
            wc_change = working_capital_change
        else:
            # Calculate as % of revenue change
            if i == 0:
                revenue_change = current_revenue - base_revenue
            else:
                revenue_change = current_revenue - revenue_proj[i - 1]
            wc_change = revenue_change * working_capital_as_pct_revenue
        
        # Free Cash Flow
        # FCF = Net Income + D&A - CapEx - Working Capital Change
        fcf = net_income + depreciation - current_capex - wc_change
        fcf_proj.append(fcf)
    
    return {
        "periods": projected_periods,
        "revenue": revenue_proj,
        "cogs": cogs_proj,
        "gross_profit": gross_profit_proj,
        "operating_expense": operating_expense_proj,
        "operating_income": operating_income_proj,
        "net_income": net_income_proj,
        "capex": capex_proj,
        "depreciation": depreciation_proj,
        "free_cash_flow": fcf_proj,
    }


def run_scenario_dcf(
    projections: Dict[str, Any],
    dcf_assumptions: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Run DCF calculation for a scenario.
    
    This is a wrapper around run_dcf() to maintain consistency.
    
    Args:
        projections: Projections dict (from build_scenario_projections or run_three_statement)
        dcf_assumptions: DCF-specific assumptions:
            - wacc: float
            - terminal_growth_rate: float
            - shares_outstanding: float | None
            - debt: float | None
            - cash: float | None
    
    Returns:
        DCF results dict (same format as run_dcf)
    """
    return run_dcf(projections, dcf_assumptions)


def run_all_scenarios(
    latest_historical: Dict[str, float],
    base_projections: Optional[Dict[str, Any]],
    base_assumptions: Dict[str, Any],
    bear_assumptions: Dict[str, Any],
    bull_assumptions: Dict[str, Any],
    dcf_assumptions_base: Dict[str, Any],
    dcf_assumptions_bear: Dict[str, Any],
    dcf_assumptions_bull: Dict[str, Any],
    forecast_periods: int = 5,
) -> Dict[str, Any]:
    """
    Run Bear, Bull, and Base scenarios and return all results.
    
    Args:
        latest_historical: Latest historical financial data (for Bear/Bull baseline)
        base_projections: Projections from run_three_statement() for base case (if None, will build from assumptions)
        base_assumptions: Income statement assumptions for base case
        bear_assumptions: Income statement assumptions for bear case
        bull_assumptions: Income statement assumptions for bull case
        dcf_assumptions_base: DCF assumptions for base case
        dcf_assumptions_bear: DCF assumptions for bear case
        dcf_assumptions_bull: DCF assumptions for bull case
        forecast_periods: Number of periods to project
    
    Returns:
        Dictionary with all scenario results:
        {
            "base": {
                "projections": {...},
                "dcf": {...}
            },
            "bear": {
                "projections": {...},
                "dcf": {...}
            },
            "bull": {
                "projections": {...},
                "dcf": {...}
            }
        }
    """
    results = {}
    
    # Base case
    if base_projections is None:
        # Build base projections from assumptions if not provided
        base_projections = build_scenario_projections(
            latest_historical,
            base_assumptions,
            forecast_periods
        )
    
    base_dcf = run_scenario_dcf(base_projections, dcf_assumptions_base)
    results["base"] = {
        "projections": base_projections,
        "dcf": base_dcf,
    }
    
    # Bear case
    bear_projections = build_scenario_projections(
        latest_historical,
        bear_assumptions,
        forecast_periods
    )
    bear_dcf = run_scenario_dcf(bear_projections, dcf_assumptions_bear)
    results["bear"] = {
        "projections": bear_projections,
        "dcf": bear_dcf,
    }
    
    # Bull case
    bull_projections = build_scenario_projections(
        latest_historical,
        bull_assumptions,
        forecast_periods
    )
    bull_dcf = run_scenario_dcf(bull_projections, dcf_assumptions_bull)
    results["bull"] = {
        "projections": bull_projections,
        "dcf": bull_dcf,
    }
    
    return results

