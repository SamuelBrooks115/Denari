"""
three_statement.py — Forward Financial Projections (3-Statement Model)

Purpose:
- Generate forecasted:
    * Income Statement (Revenue → EBIT → Net Income)
    * Balance Sheet (minimal for MVP)
    * Cash Flow Statement (Free Cash Flow focus)

This module is unit-testable without Excel and uses structured dataclass outputs.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

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


# Formula template dictionary for 3-statement model Excel output
# Format: {cell_address: formula_string}
# All formulas reference cells in the same sheet
THREE_STATEMENT_FORMULAS: Dict[str, str] = {
    # Revenue growth formulas
    "G5": "=F5*(1+O5)",
    "H5": "=G5*(1+P5)",
    "I5": "=H5*(1+Q5)",
    "J5": "=I5*(1+R5)",
    "K5": "=J5*(1+S5)",
    
    # Gross profit calculations
    "F6": "=F5-F7",
    "G6": "=G5-G7",
    "H6": "=H5-H7",
    "I6": "=I5-I7",
    "J6": "=J5-J7",
    "K6": "=K5-K7",
    
    # COGS calculations
    "F7": "=F8*F5",
    "G7": "=G8*G5",
    "H7": "=H8*H5",
    "I7": "=I8*I5",
    "J7": "=J8*J5",
    "K7": "=K8*K5",
    
    # COGS margin
    "G8": "=F8+(O6)",
    "H8": "=G8+(P6)",
    "I8": "=H8+(Q6)",
    "J8": "=I8+(R6)",
    "K8": "=J8+(S6)",
    
    # Operating expenses
    "G9": "=(F9/F12)*(G7-G12)",
    "H9": "=(G9/G12)*(H7-H12)",
    "I9": "=(H9/H12)*(I7-I12)",
    "J9": "=(I9/I12)*(J7-J12)",
    "K9": "=(J9/J12)*(K7-K12)",
    
    "G10": "=(F10/F12)*(G7-G12)",
    "H10": "=(G10/G12)*(H7-H12)",
    "I10": "=(H10/H12)*(I7-I12)",
    "J10": "=(I10/I12)*(J7-J12)",
    "K10": "=(J10/J12)*(K7-K12)",
    
    "G11": "=(F11/F12)*(G7-G12)",
    "H11": "=(G11/G12)*(H7-H12)",
    "I11": "=(H11/H12)*(I7-I12)",
    "J11": "=(I11/I12)*(J7-J12)",
    "K11": "=(J11/J12)*(K7-K12)",
    
    # Total operating expenses
    "F12": "=SUM(F9:F11)",
    "G12": "=G13*G5",
    "H12": "=H13*H5",
    "I12": "=I13*I5",
    "J12": "=J13*J5",
    "K12": "=K13*K5",
    
    # Operating expense margin
    "G13": "=F13+O7",
    "H13": "=G13+P7",
    "I13": "=H13+Q7",
    "J13": "=I13+R7",
    "K13": "=J13+S7",
    
    # Other income statement items
    "G14": "=($F$14/$F$5)*G5",
    "H14": "=($F$14/$F$5)*H5",
    "I14": "=($F$14/$F$5)*I5",
    "J14": "=($F$14/$F$5)*J5",
    "K14": "=($F$14/$F$5)*K5",
    
    "G15": "=($F$15/$F$5)*G5",
    "H15": "=($F$15/$F$5)*H5",
    "I15": "=($F$15/$F$5)*I5",
    "J15": "=($F$15/$F$5)*J5",
    "K15": "=($F$15/$F$5)*K5",
    
    # Operating income
    "G16": "=G12-G14-G15",
    "H16": "=H12-H14-H15",
    "I16": "=I12-I14-I15",
    "J16": "=J12-J14-J15",
    "K16": "=K12-K14-K15",
    
    # Tax
    "G17": "=G16*O9",
    "H17": "=H16*P9",
    "I17": "=I16*Q9",
    "J17": "=J16*R9",
    "K17": "=K16*S9",
    
    # Net income
    "G18": "=G16-G17",
    "H18": "=H16-H17",
    "I18": "=I16-I17",
    "J18": "=J16-J17",
    "K18": "=K16-K17",
    
    # Net income margin
    "G19": "=G18/G5",
    "H19": "=H18/H5",
    "I19": "=I18/I5",
    "J19": "=J18/J5",
    "K19": "=K18/K5",
    
    # Shares outstanding
    "G20": "=G18/G21",
    "H20": "=H18/H21",
    "I20": "=I18/I21",
    "J20": "=J18/J21",
    "K20": "=K18/K21",
    
    "G21": "=F21+O72",
    "H21": "=G21+P72",
    "I21": "=H21+Q72",
    "J21": "=I21+R72",
    "K21": "=J21+S72",
    
    # Balance Sheet items
    "G25": "=G114",
    "H25": "=H114",
    "I25": "=I114",
    "J25": "=J114",
    "K25": "=K114",
    
    "G26": "=(F$26/$F$5)*G$5",
    "H26": "=(G$26/$F$5)*H$5",
    "I26": "=(H$26/$F$5)*I$5",
    "J26": "=(I$26/$F$5)*J$5",
    "K26": "=(J$26/$F$5)*K$5",
    
    "G27": "=(F$27/$F$5)*G$5",
    "H27": "=(G$27/$F$5)*H$5",
    "I27": "=(H$27/$F$5)*I$5",
    "J27": "=(I$27/$F$5)*J$5",
    "K27": "=(J$27/$F$5)*K$5",
    
    "G28": "=G5*O26",
    "H28": "=H5*P26",
    "I28": "=I5*Q26",
    "J28": "=J5*R26",
    "K28": "=K5*S26",
    
    "G29": "=(F$29/$F$5)*G$5",
    "H29": "=(G$29/$F$5)*H$5",
    "I29": "=(H$29/$F$5)*I$5",
    "J29": "=(I$29/$F$5)*J$5",
    "K29": "=(J$29/$F$5)*K$5",
    
    "G30": "=(F$30/$F$5)*G$5",
    "H30": "=(G$30/$F$5)*H$5",
    "I30": "=(H$30/$F$5)*I$5",
    "J30": "=(I$30/$F$5)*J$5",
    "K30": "=(J$30/$F$5)*K$5",
    
    "G31": "=SUM(G25:G30)",
    "H31": "=SUM(H25:H30)",
    "I31": "=SUM(I25:I30)",
    "J31": "=SUM(J25:J30)",
    "K31": "=SUM(K25:K30)",
    
    "G32": "=(F$32/$F$5)*G$5",
    "H32": "=(G$32/$F$5)*H$5",
    "I32": "=(H$32/$F$5)*I$5",
    "J32": "=(I$32/$F$5)*J$5",
    "K32": "=(J$32/$F$5)*K$5",
    
    "G33": "=(F$33/$F$5)*G$5",
    "H33": "=(G$33/$F$5)*H$5",
    "I33": "=(H$33/$F$5)*I$5",
    "J33": "=(I$33/$F$5)*J$5",
    "K33": "=(J$33/$F$5)*K$5",
    
    "G34": "=(F$34/$F$5)*G$5",
    "H34": "=(G$34/$F$5)*H$5",
    "I34": "=(H$34/$F$5)*I$5",
    "J34": "=(I$34/$F$5)*J$5",
    "K34": "=(J$34/$F$5)*K$5",
    
    "G35": "=(F$35/$F$5)*G$5",
    "H35": "=(G$35/$F$5)*H$5",
    "I35": "=(H$35/$F$5)*I$5",
    "J35": "=(I$35/$F$5)*J$5",
    "K35": "=(J$35/$F$5)*K$5",
    
    "G36": "=(F$36/$F$5)*G$5",
    "H36": "=(G$36/$F$5)*H$5",
    "I36": "=(H$36/$F$5)*I$5",
    "J36": "=(I$36/$F$5)*J$5",
    "K36": "=(J$36/$F$5)*K$5",
    
    "G37": "=(F$37/$F$5)*G$5",
    "H37": "=(G$37/$F$5)*H$5",
    "I37": "=(H$37/$F$5)*I$5",
    "J37": "=(I$37/$F$5)*J$5",
    "K37": "=(J$37/$F$5)*K$5",
    
    "G38": "=(F$38/$F$5)*G$5",
    "H38": "=(G$38/$F$5)*H$5",
    "I38": "=(H$38/$F$5)*I$5",
    "J38": "=(I$38/$F$5)*J$5",
    "K38": "=(J$38/$F$5)*K$5",
    
    "G39": "=(F$39/$F$5)*G$5",
    "H39": "=(G$39/$F$5)*H$5",
    "I39": "=(H$39/$F$5)*I$5",
    "J39": "=(I$39/$F$5)*J$5",
    "K39": "=(J$39/$F$5)*K$5",
    
    "G40": "=G69-SUM(G32:G39)",
    "H40": "=H69-SUM(H32:H39)",
    "I40": "=I69-SUM(I32:I39)",
    "J40": "=J69-SUM(J32:J39)",
    "K40": "=K69-SUM(K32:K39)",
    
    "G41": "=SUM(G32:G38)",
    "H41": "=SUM(H32:H38)",
    "I41": "=SUM(I32:I38)",
    "J41": "=SUM(J32:J38)",
    "K41": "=SUM(K32:K38)",
    
    "G42": "=SUM(G31,G41)",
    "H42": "=SUM(H31,H41)",
    "I42": "=SUM(I31,I41)",
    "J42": "=SUM(J31,J41)",
    "K42": "=SUM(K31,K41)",
    
    "G44": "=(F$44/$F$5)*G$5",
    "H44": "=(G$44/$F$5)*H$5",
    "I44": "=(H$44/$F$5)*I$5",
    "J44": "=(I$44/$F$5)*J$5",
    "K44": "=(J$44/$F$5)*K$5",
    
    "G45": "=(F$45/$F$5)*G$5",
    "H45": "=(G$45/$F$5)*H$5",
    "I45": "=(H$45/$F$5)*I$5",
    "J45": "=(I$45/$F$5)*J$5",
    "K45": "=(J$45/$F$5)*K$5",
    
    "G46": "=(F$46/$F$5)*G$5",
    "H46": "=(G$46/$F$5)*H$5",
    "I46": "=(H$46/$F$5)*I$5",
    "J46": "=(I$46/$F$5)*J$5",
    "K46": "=(J$46/$F$5)*K$5",
    
    "G47": "=(F$47/$F$5)*G$5",
    "H47": "=(G$47/$F$5)*H$5",
    "I47": "=(H$47/$F$5)*I$5",
    "J47": "=(I$47/$F$5)*J$5",
    "K47": "=(J$47/$F$5)*K$5",
    
    "G48": "=(F$48/$F$5)*G$5",
    "H48": "=(G$48/$F$5)*H$5",
    "I48": "=(H$48/$F$5)*I$5",
    "J48": "=(I$48/$F$5)*J$5",
    "K48": "=(J$48/$F$5)*K$5",
    
    "G49": "=(F$49/$F$5)*G$5",
    "H49": "=(G$49/$F$5)*H$5",
    "I49": "=(H$49/$F$5)*I$5",
    "J49": "=(I$49/$F$5)*J$5",
    "K49": "=(J$49/$F$5)*K$5",
    
    "G50": "=(F$50/$F$5)*G$5",
    "H50": "=(G$50/$F$5)*H$5",
    "I50": "=(H$50/$F$5)*I$5",
    "J50": "=(I$50/$F$5)*J$5",
    "K50": "=(J$50/$F$5)*K$5",
    
    "G51": "=(F$51/$F$5)*G$5",
    "H51": "=(G$51/$F$5)*H$5",
    "I51": "=(H$51/$F$5)*I$5",
    "J51": "=(I$51/$F$5)*J$5",
    "K51": "=(J$51/$F$5)*K$5",
    
    "G52": "=SUM(G44:G51)",
    "H52": "=SUM(H44:H51)",
    "I52": "=SUM(I44:I51)",
    "J52": "=SUM(J44:J51)",
    "K52": "=SUM(K44:K51)",
    
    "G53": "=F53*(1+O27)",
    "H53": "=G53*(1+P27)",
    "I53": "=H53*(1+Q27)",
    "J53": "=I53*(1+R27)",
    "K53": "=J53*(1+S27)",
    
    "G54": "=(F$54/$F$5)*G$5",
    "H54": "=(G$54/$F$5)*H$5",
    "I54": "=(H$54/$F$5)*I$5",
    "J54": "=(I$54/$F$5)*J$5",
    "K54": "=(J$54/$F$5)*K$5",
    
    "G55": "=(F$55/$F$5)*G$5",
    "H55": "=(G$55/$F$5)*H$5",
    "I55": "=(H$55/$F$5)*I$5",
    "J55": "=(I$55/$F$5)*J$5",
    "K55": "=(J$55/$F$5)*K$5",
    
    "G56": "=(F$56/$F$5)*G$5",
    "H56": "=(G$56/$F$5)*H$5",
    "I56": "=(H$56/$F$5)*I$5",
    "J56": "=(I$56/$F$5)*J$5",
    "K56": "=(J$56/$F$5)*K$5",
    
    "G57": "=(F$57/$F$5)*G$5",
    "H57": "=(G$57/$F$5)*H$5",
    "I57": "=(H$57/$F$5)*I$5",
    "J57": "=(I$57/$F$5)*J$5",
    "K57": "=(J$57/$F$5)*K$5",
    
    "G58": "=SUM(G53:G57)",
    "H58": "=SUM(H53:H57)",
    "I58": "=SUM(I53:I57)",
    "J58": "=SUM(J53:J57)",
    "K58": "=SUM(K53:K57)",
    
    "G59": "=SUM(G52,G58)",
    "H59": "=SUM(H52,H58)",
    "I59": "=SUM(I52,I58)",
    "J59": "=SUM(J52,J58)",
    "K59": "=SUM(K52,K58)",
    
    "G61": "=(F$61/$F$5)*G$5",
    "H61": "=(G$61/$F$5)*H$5",
    "I61": "=(H$61/$F$5)*I$5",
    "J61": "=(I$61/$F$5)*J$5",
    "K61": "=(J$61/$F$5)*K$5",
    
    "G62": "=(F$62/$F$5)*G$5",
    "H62": "=(G$62/$F$5)*H$5",
    "I62": "=(H$62/$F$5)*I$5",
    "J62": "=(I$62/$F$5)*J$5",
    "K62": "=(J$62/$F$5)*K$5",
    
    "G63": "=(F$63/$F$5)*G$5",
    "H63": "=(G$63/$F$5)*H$5",
    "I63": "=(H$63/$F$5)*I$5",
    "J63": "=(I$63/$F$5)*J$5",
    "K63": "=(J$63/$F$5)*K$5",
    
    "G64": "=(F$64/$F$5)*G$5",
    "H64": "=(G$64/$F$5)*H$5",
    "I64": "=(H$64/$F$5)*I$5",
    "J64": "=(I$64/$F$5)*J$5",
    "K64": "=(J$64/$F$5)*K$5",
    
    "G65": "=(F$65/$F$5)*G$5",
    "H65": "=(G$65/$F$5)*H$5",
    "I65": "=(H$65/$F$5)*I$5",
    "J65": "=(I$65/$F$5)*J$5",
    "K65": "=(J$65/$F$5)*K$5",
    
    "G66": "=(F$66/$F$5)*G$5",
    "H66": "=(G$66/$F$5)*H$5",
    "I66": "=(H$66/$F$5)*I$5",
    "J66": "=(I$66/$F$5)*J$5",
    "K66": "=(J$66/$F$5)*K$5",
    
    "G67": "=(F$67/$F$5)*G$5",
    "H67": "=(G$67/$F$5)*H$5",
    "I67": "=(H$67/$F$5)*I$5",
    "J67": "=(I$67/$F$5)*J$5",
    "K67": "=(J$67/$F$5)*K$5",
    
    "G68": "=SUM(G61:G67)",
    "H68": "=SUM(H61:H67)",
    "I68": "=SUM(I61:I67)",
    "J68": "=SUM(J61:J67)",
    "K68": "=SUM(K61:K67)",
    
    "G69": "=SUM(G68,G59)",
    "H69": "=SUM(H68,H59)",
    "I69": "=SUM(I68,I59)",
    "J69": "=SUM(J68,J59)",
    "K69": "=SUM(K68,K59)",
    
    # Cash Flow Statement
    "G72": "=G18",
    "H72": "=H18",
    "I72": "=I18",
    "J72": "=J18",
    "K72": "=K18",
    
    "G73": "=O25*G32",
    "H73": "=P25*H32",
    "I73": "=Q25*I32",
    "J73": "=R25*J32",
    "K73": "=S25*K32",
    
    "G74": "=(F$74/$F$5)*G$5",
    "H74": "=(G$74/$F$5)*H$5",
    "I74": "=(H$74/$F$5)*I$5",
    "J74": "=(I$74/$F$5)*J$5",
    "K74": "=(J$74/$F$5)*K$5",
    
    "G75": "=(F$75/$F$5)*G$5",
    "H75": "=(G$75/$F$5)*H$5",
    "I75": "=(H$75/$F$5)*I$5",
    "J75": "=(I$75/$F$5)*J$5",
    "K75": "=(J$75/$F$5)*K$5",
    
    "G76": "=(G31-G52)-(F31-F52)",
    "H76": "=(H31-H52)-(G31-G52)",
    "I76": "=(I31-I52)-(H31-H52)",
    "J76": "=(J31-J52)-(I31-I52)",
    "K76": "=(K31-K52)-(J31-J52)",
    
    "G77": "=G27-F27",
    "H77": "=H27-G27",
    "I77": "=I27-H27",
    "J77": "=J27-I27",
    "K77": "=K27-J27",
    
    "G78": "=G28-F28",
    "H78": "=H28-G28",
    "I78": "=I28-H28",
    "J78": "=J28-I28",
    "K78": "=K28-J28",
    
    "G79": "=G44-F44",
    "H79": "=H44-G44",
    "I79": "=I44-H44",
    "J79": "=J44-I44",
    "K79": "=K44-J44",
    
    "G80": "=(F$80/$F$5)*G$5",
    "H80": "=(G$80/$F$5)*H$5",
    "I80": "=(H$80/$F$5)*I$5",
    "J80": "=(I$80/$F$5)*J$5",
    "K80": "=(J$80/$F$5)*K$5",
    
    "G81": "=(F$81/$F$5)*G$5",
    "H81": "=(G$81/$F$5)*H$5",
    "I81": "=(H$81/$F$5)*I$5",
    "J81": "=(I$81/$F$5)*J$5",
    "K81": "=(J$81/$F$5)*K$5",
    
    "G82": "=SUM(G72:G81)",
    "H82": "=SUM(H72:H81)",
    "I82": "=SUM(I72:I81)",
    "J82": "=SUM(J72:J81)",
    "K82": "=SUM(K72:K81)",
    
    "G84": "=O74",
    "H84": "=P74",
    "I84": "=Q74",
    "J84": "=R74",
    "K84": "=S74",
    
    "G85": "=(F$85/$F$5)*G$5",
    "H85": "=(G$85/$F$5)*H$5",
    "I85": "=(H$85/$F$5)*I$5",
    "J85": "=(I$85/$F$5)*J$5",
    "K85": "=(J$85/$F$5)*K$5",
    
    "G86": "=(F$86/$F$5)*G$5",
    "H86": "=(G$86/$F$5)*H$5",
    "I86": "=(H$86/$F$5)*I$5",
    "J86": "=(I$86/$F$5)*J$5",
    "K86": "=(J$86/$F$5)*K$5",
    
    "G87": "=(F$87/$F$5)*G$5",
    "H87": "=(G$87/$F$5)*H$5",
    "I87": "=(H$87/$F$5)*I$5",
    "J87": "=(I$87/$F$5)*J$5",
    "K87": "=(J$87/$F$5)*K$5",
    
    "G88": "=(F$88/$F$5)*G$5",
    "H88": "=(G$88/$F$5)*H$5",
    "I88": "=(H$88/$F$5)*I$5",
    "J88": "=(I$88/$F$5)*J$5",
    "K88": "=(J$88/$F$5)*K$5",
    
    "G89": "=SUM(G84:G88)",
    "H89": "=SUM(H84:H88)",
    "I89": "=SUM(I84:I88)",
    "J89": "=SUM(J84:J88)",
    "K89": "=SUM(K84:K88)",
    
    "G91": "=(F$91/$F$5)*G$5",
    "H91": "=(G$91/$F$5)*H$5",
    "I91": "=(H$91/$F$5)*I$5",
    "J91": "=(I$91/$F$5)*J$5",
    "K91": "=(J$91/$F$5)*K$5",
    
    "G92": "=(F$92/$F$5)*G$5",
    "H92": "=(G$92/$F$5)*H$5",
    "I92": "=(H$92/$F$5)*I$5",
    "J92": "=(I$92/$F$5)*J$5",
    "K92": "=(J$92/$F$5)*K$5",
    
    "G93": "=(F$87/$F$5)*G$5",
    "H93": "=(G$87/$F$5)*H$5",
    "I93": "=(H$87/$F$5)*I$5",
    "J93": "=(I$87/$F$5)*J$5",
    "K93": "=(J$87/$F$5)*K$5",
    
    "G94": "=(F$94/$F$5)*G$5",
    "H94": "=(G$94/$F$5)*H$5",
    "I94": "=(H$94/$F$5)*I$5",
    "J94": "=(I$94/$F$5)*J$5",
    "K94": "=(J$94/$F$5)*K$5",
    
    "G95": "=(F$95/$F$5)*G$5",
    "H95": "=(G$95/$F$5)*H$5",
    "I95": "=(H$95/$F$5)*I$5",
    "J95": "=(I$95/$F$5)*J$5",
    "K95": "=(J$95/$F$5)*K$5",
    
    "G96": "=(F$96/$F$5)*G$5",
    "H96": "=(G$96/$F$5)*H$5",
    "I96": "=(H$96/$F$5)*I$5",
    "J96": "=(I$96/$F$5)*J$5",
    "K96": "=(J$96/$F$5)*K$5",
    
    "G97": "=(F$97/$F$5)*G$5",
    "H97": "=(G$97/$F$5)*H$5",
    "I97": "=(H$97/$F$5)*I$5",
    "J97": "=(I$97/$F$5)*J$5",
    "K97": "=(J$97/$F$5)*K$5",
    
    "G98": "=(F$98/$F$5)*G$5",
    "H98": "=(G$98/$F$5)*H$5",
    "I98": "=(H$98/$F$5)*I$5",
    "J98": "=(I$98/$F$5)*J$5",
    "K98": "=(J$98/$F$5)*K$5",
    
    "G99": "=(F$99/$F$5)*G$5",
    "H99": "=(G$99/$F$5)*H$5",
    "I99": "=(H$99/$F$5)*I$5",
    "J99": "=(I$99/$F$5)*J$5",
    "K99": "=(J$99/$F$5)*K$5",
    
    "G100": "=(F$100/$F$5)*G$5",
    "H100": "=(G$100/$F$5)*H$5",
    "I100": "=(H$100/$F$5)*I$5",
    "J100": "=(I$100/$F$5)*J$5",
    "K100": "=(J$100/$F$5)*K$5",
    
    "G101": "=(F$101/$F$5)*G$5",
    "H101": "=(G$101/$F$5)*H$5",
    "I101": "=(H$101/$F$5)*I$5",
    "J101": "=(I$101/$F$5)*J$5",
    "K101": "=(J$101/$F$5)*K$5",
    
    "G102": "=(F$102/$F$5)*G$5",
    "H102": "=(G$102/$F$5)*H$5",
    "I102": "=(H$102/$F$5)*I$5",
    "J102": "=(I$102/$F$5)*J$5",
    "K102": "=(J$102/$F$5)*K$5",
    
    "G103": "=(F$103/$F$5)*G$5",
    "H103": "=(G$103/$F$5)*H$5",
    "I103": "=(H$103/$F$5)*I$5",
    "J103": "=(I$103/$F$5)*J$5",
    "K103": "=(J$103/$F$5)*K$5",
    
    "G104": "=(F$104/$F$5)*G$5",
    "H104": "=(G$104/$F$5)*H$5",
    "I104": "=(H$104/$F$5)*I$5",
    "J104": "=(I$104/$F$5)*J$5",
    "K104": "=(J$104/$F$5)*K$5",
    
    "G105": "=(F$105/$F$5)*G$5",
    "H105": "=(G$105/$F$5)*H$5",
    "I105": "=(H$105/$F$5)*I$5",
    "J105": "=(I$105/$F$5)*J$5",
    "K105": "=(J$105/$F$5)*K$5",
    
    "G106": "=(F$106/$F$5)*G$5",
    "H106": "=(G$106/$F$5)*H$5",
    "I106": "=(H$106/$F$5)*I$5",
    "J106": "=(I$106/$F$5)*J$5",
    "K106": "=(J$106/$F$5)*K$5",
    
    "G107": "=(F$106/$F$5)*G$5",
    "H107": "=(G$106/$F$5)*H$5",
    "I107": "=(H$106/$F$5)*I$5",
    "J107": "=(I$106/$F$5)*J$5",
    "K107": "=(J$106/$F$5)*K$5",
    
    "G108": "=SUM(G91:G107)",
    "H108": "=SUM(H91:H107)",
    "I108": "=SUM(I91:I107)",
    "J108": "=SUM(J91:J107)",
    "K108": "=SUM(K91:K107)",
    
    "G113": "=SUM(G72:G81)+SUM(G84:G88+SUM(G91:G107)+G110)",
    "H113": "=SUM(H72:H81)+SUM(H84:H88+SUM(H91:H107)+H110)",
    "I113": "=SUM(I72:I81)+SUM(I84:I88+SUM(I91:I107)+I110)",
    "J113": "=SUM(J72:J81)+SUM(J84:J88+SUM(J91:J107)+J110)",
    "K113": "=SUM(K72:K81)+SUM(K84:K88+SUM(K91:K107)+K110)",
    
    "G116": "=G12*(1-O9)+G73-G84-G76",
    "H116": "=H12*(1-P9)+H73-H84-H76",
    "I116": "=I12*(1-Q9)+I73-I84-I76",
    "J116": "=J12*(1-R9)+J73-J84-J76",
    "K116": "=K12*(1-S9)+K73-K84-K76",
}


def _col_to_letter(col_num: int) -> str:
    """
    Convert 0-indexed column number to Excel column letter(s).
    
    Args:
        col_num: 0-indexed column number (0 = A, 1 = B, ..., 25 = Z, 26 = AA, etc.)
    
    Returns:
        Excel column letter(s) (e.g., "A", "B", "Z", "AA", "AB")
    """
    result = ""
    col_num += 1  # Convert to 1-indexed
    while col_num > 0:
        col_num -= 1
        result = chr(65 + (col_num % 26)) + result
        col_num //= 26
    return result


def write_three_statement_sheet(
    workbook,
    projections: Dict[str, Any],
    sheet_name: str = "Three Statement Model",
    start_row: int = 0,
    start_col: int = 0,
    include_historical: bool = False,
    historical_data: Optional[Dict[str, Dict[str, float]]] = None,
    custom_formulas: Optional[Dict[str, str]] = None,
) -> None:
    """
    Write 3-statement model projections to Excel worksheet with formulas.
    
    Helper for excel_export.py to write the three-statement model to Excel.
    This function writes both calculated values and Excel formulas for
    interactive modeling.
    
    Expected usage:
        workbook = xlsxwriter.Workbook(...)
        projections = run_three_statement(...)
        write_three_statement_sheet(workbook, projections)
    
    Args:
        workbook: xlsxwriter Workbook object
        projections: Output from run_three_statement() containing:
            - periods: List[str] - Period end dates
            - revenue: List[float]
            - cogs: List[float]
            - gross_profit: List[float]
            - operating_expense: List[float]
            - operating_income: List[float]
            - net_income: List[float]
            - free_cash_flow: List[float]
            - capex: List[float]
            - depreciation: List[float]
        sheet_name: Name of the Excel worksheet (default: "Three Statement Model")
        start_row: Starting row for the table (0-indexed, default: 0)
        start_col: Starting column for the table (0-indexed, default: 0)
        include_historical: Whether to include historical data rows (default: False)
        historical_data: Optional historical financials dict (if include_historical=True)
        custom_formulas: Optional dict mapping cell addresses to formula strings.
                        If provided, these formulas will be used instead of default formulas.
                        Example: {"B10": "=SUM(B2:B9)", "C10": "=B10*0.21"}
    
    The sheet contains:
        - Header row with period labels
        - Income Statement section (Revenue, COGS, Gross Profit, Operating Expenses, etc.)
        - Balance Sheet section (if applicable)
        - Cash Flow Statement section (FCF focus)
        - Excel formulas for calculations (from THREE_STATEMENT_FORMULAS or custom_formulas)
    """
    import xlsxwriter
    
    worksheet = workbook.add_worksheet(sheet_name)
    
    # Create formats
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#D3D3D3',
        'align': 'center',
        'valign': 'vcenter',
    })
    
    label_format = workbook.add_format({
        'bold': True,
        'align': 'left',
    })
    
    number_format = workbook.add_format({
        'num_format': '#,##0',
    })
    
    currency_format = workbook.add_format({
        'num_format': '$#,##0',
    })
    
    percent_format = workbook.add_format({
        'num_format': '0.00%',
    })
    
    formula_format = workbook.add_format({
        'num_format': '#,##0',
        'italic': True,
    })
    
    # Get periods and data
    periods = projections.get("periods", [])
    num_periods = len(periods)
    
    if num_periods == 0:
        worksheet.write(start_row, start_col, "No projection data available")
        return
    
    # Write header row with period labels
    # Column A: Labels, Columns B onwards: Period data
    worksheet.write(start_row, start_col, "Line Item", header_format)
    for col_idx, period in enumerate(periods):
        worksheet.write(start_row, start_col + 1 + col_idx, period, header_format)
    
    current_row = start_row + 1
    
    # Write Income Statement section
    worksheet.write(current_row, start_col, "Income Statement", label_format)
    current_row += 1
    
    # Revenue
    worksheet.write(current_row, start_col, "Revenue", label_format)
    for col_idx in range(num_periods):
        col_letter = _col_to_letter(start_col + 1 + col_idx)
        cell_address = f"{col_letter}{current_row + 1}"
        # Check for custom formula first, then template, then use calculated value
        if custom_formulas and cell_address in custom_formulas:
            worksheet.write(current_row, start_col + 1 + col_idx, custom_formulas[cell_address], formula_format)
        elif cell_address in THREE_STATEMENT_FORMULAS:
            worksheet.write(current_row, start_col + 1 + col_idx, THREE_STATEMENT_FORMULAS[cell_address], formula_format)
        else:
            worksheet.write(current_row, start_col + 1 + col_idx, projections["revenue"][col_idx], currency_format)
    current_row += 1
    
    # COGS
    worksheet.write(current_row, start_col, "Cost of Goods Sold", label_format)
    for col_idx in range(num_periods):
        col_letter = _col_to_letter(start_col + 1 + col_idx)
        cell_address = f"{col_letter}{current_row + 1}"
        if custom_formulas and cell_address in custom_formulas:
            worksheet.write(current_row, start_col + 1 + col_idx, custom_formulas[cell_address], formula_format)
        elif cell_address in THREE_STATEMENT_FORMULAS:
            worksheet.write(current_row, start_col + 1 + col_idx, THREE_STATEMENT_FORMULAS[cell_address], formula_format)
        else:
            worksheet.write(current_row, start_col + 1 + col_idx, projections["cogs"][col_idx], currency_format)
    current_row += 1
    
    # Gross Profit
    worksheet.write(current_row, start_col, "Gross Profit", label_format)
    for col_idx in range(num_periods):
        col_letter = _col_to_letter(start_col + 1 + col_idx)
        cell_address = f"{col_letter}{current_row + 1}"
        if custom_formulas and cell_address in custom_formulas:
            worksheet.write(current_row, start_col + 1 + col_idx, custom_formulas[cell_address], formula_format)
        elif cell_address in THREE_STATEMENT_FORMULAS:
            worksheet.write(current_row, start_col + 1 + col_idx, THREE_STATEMENT_FORMULAS[cell_address], formula_format)
        else:
            worksheet.write(current_row, start_col + 1 + col_idx, projections["gross_profit"][col_idx], currency_format)
    current_row += 1
    
    # Operating Expenses
    worksheet.write(current_row, start_col, "Operating Expenses", label_format)
    for col_idx in range(num_periods):
        col_letter = _col_to_letter(start_col + 1 + col_idx)
        cell_address = f"{col_letter}{current_row + 1}"
        if custom_formulas and cell_address in custom_formulas:
            worksheet.write(current_row, start_col + 1 + col_idx, custom_formulas[cell_address], formula_format)
        elif cell_address in THREE_STATEMENT_FORMULAS:
            worksheet.write(current_row, start_col + 1 + col_idx, THREE_STATEMENT_FORMULAS[cell_address], formula_format)
        else:
            worksheet.write(current_row, start_col + 1 + col_idx, projections["operating_expense"][col_idx], currency_format)
    current_row += 1
    
    # Operating Income
    worksheet.write(current_row, start_col, "Operating Income", label_format)
    for col_idx in range(num_periods):
        col_letter = _col_to_letter(start_col + 1 + col_idx)
        cell_address = f"{col_letter}{current_row + 1}"
        if custom_formulas and cell_address in custom_formulas:
            worksheet.write(current_row, start_col + 1 + col_idx, custom_formulas[cell_address], formula_format)
        elif cell_address in THREE_STATEMENT_FORMULAS:
            worksheet.write(current_row, start_col + 1 + col_idx, THREE_STATEMENT_FORMULAS[cell_address], formula_format)
        else:
            worksheet.write(current_row, start_col + 1 + col_idx, projections["operating_income"][col_idx], currency_format)
    current_row += 1
    
    # Net Income
    worksheet.write(current_row, start_col, "Net Income", label_format)
    for col_idx in range(num_periods):
        col_letter = _col_to_letter(start_col + 1 + col_idx)
        cell_address = f"{col_letter}{current_row + 1}"
        if custom_formulas and cell_address in custom_formulas:
            worksheet.write(current_row, start_col + 1 + col_idx, custom_formulas[cell_address], formula_format)
        elif cell_address in THREE_STATEMENT_FORMULAS:
            worksheet.write(current_row, start_col + 1 + col_idx, THREE_STATEMENT_FORMULAS[cell_address], formula_format)
        else:
            worksheet.write(current_row, start_col + 1 + col_idx, projections["net_income"][col_idx], currency_format)
    current_row += 2
    
    # Cash Flow Statement section
    worksheet.write(current_row, start_col, "Cash Flow Statement", label_format)
    current_row += 1
    
    # CapEx
    worksheet.write(current_row, start_col, "Capital Expenditures", label_format)
    for col_idx in range(num_periods):
        col_letter = _col_to_letter(start_col + 1 + col_idx)
        cell_address = f"{col_letter}{current_row + 1}"
        if custom_formulas and cell_address in custom_formulas:
            worksheet.write(current_row, start_col + 1 + col_idx, custom_formulas[cell_address], formula_format)
        elif cell_address in THREE_STATEMENT_FORMULAS:
            worksheet.write(current_row, start_col + 1 + col_idx, THREE_STATEMENT_FORMULAS[cell_address], formula_format)
        else:
            worksheet.write(current_row, start_col + 1 + col_idx, -projections["capex"][col_idx], currency_format)  # Negative
    current_row += 1
    
    # Depreciation & Amortization
    worksheet.write(current_row, start_col, "Depreciation & Amortization", label_format)
    for col_idx in range(num_periods):
        col_letter = _col_to_letter(start_col + 1 + col_idx)
        cell_address = f"{col_letter}{current_row + 1}"
        if custom_formulas and cell_address in custom_formulas:
            worksheet.write(current_row, start_col + 1 + col_idx, custom_formulas[cell_address], formula_format)
        elif cell_address in THREE_STATEMENT_FORMULAS:
            worksheet.write(current_row, start_col + 1 + col_idx, THREE_STATEMENT_FORMULAS[cell_address], formula_format)
        else:
            worksheet.write(current_row, start_col + 1 + col_idx, projections["depreciation"][col_idx], currency_format)
    current_row += 1
    
    # Free Cash Flow
    worksheet.write(current_row, start_col, "Free Cash Flow", label_format)
    for col_idx in range(num_periods):
        col_letter = _col_to_letter(start_col + 1 + col_idx)
        cell_address = f"{col_letter}{current_row + 1}"
        if custom_formulas and cell_address in custom_formulas:
            worksheet.write(current_row, start_col + 1 + col_idx, custom_formulas[cell_address], formula_format)
        elif cell_address in THREE_STATEMENT_FORMULAS:
            worksheet.write(current_row, start_col + 1 + col_idx, THREE_STATEMENT_FORMULAS[cell_address], formula_format)
        else:
            worksheet.write(current_row, start_col + 1 + col_idx, projections["free_cash_flow"][col_idx], currency_format)
    
    # Set column widths for readability
    worksheet.set_column(start_col, start_col, 25)  # Label column
    for col_idx in range(num_periods):
        worksheet.set_column(start_col + 1 + col_idx, start_col + 1 + col_idx, 15)  # Data columns
