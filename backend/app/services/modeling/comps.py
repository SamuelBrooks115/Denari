"""
comps.py — Comparable Companies Valuation Logic

Purpose:
- Compute valuation multiples for a company based on its financial metrics.
- For MVP: Simplified version without peer database (would require fetching multiple companies).

Inputs (MVP - no database):
- target_financials: Dict with latest period financial metrics
- market_data: Dict with market cap, enterprise value, etc. (if available)

Outputs (JSON-serializable):
{
  "target_metrics": {
    "revenue": float,
    "ebitda": float,
    "net_income": float,
  },
  "multiples": {
    "ev_rev": float | None,
    "ev_ebitda": float | None,
    "pe": float | None,
  },
  "note": str (explaining MVP limitations)
}

Note: Full comps analysis requires peer company data which is not available in MVP.
This simplified version computes multiples for the target company only.
"""

from typing import Dict, Any, Optional, List


def run_comps(
    target_financials: Dict[str, float],
    market_data: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Simplified comps valuation entrypoint (MVP - no peer database).

    Args:
        target_financials: Dict with keys:
            - revenue: float
            - ebitda: float (optional)
            - operating_income: float (optional, used if EBITDA not available)
            - net_income: float
        market_data: Optional Dict with:
            - market_cap: float
            - enterprise_value: float
            - shares_outstanding: float

    Returns:
        Dictionary with computed multiples for target company
    """
    revenue = target_financials.get("revenue", 0.0)
    ebitda = target_financials.get("ebitda")
    operating_income = target_financials.get("operating_income")
    net_income = target_financials.get("net_income", 0.0)

    # Use EBITDA if available, otherwise approximate with operating income
    if ebitda is None and operating_income is not None:
        # Rough approximation: EBITDA ≈ Operating Income + D&A
        # For MVP, use operating income as proxy
        ebitda = operating_income

    multiples: Dict[str, Optional[float]] = {}
    
    if market_data:
        ev = market_data.get("enterprise_value")
        market_cap = market_data.get("market_cap")
        
        # EV/Revenue
        if ev is not None and revenue > 0:
            multiples["ev_rev"] = ev / revenue
        
        # EV/EBITDA
        if ev is not None and ebitda is not None and ebitda > 0:
            multiples["ev_ebitda"] = ev / ebitda
        
        # P/E (Price to Earnings)
        if market_cap is not None and net_income > 0:
            multiples["pe"] = market_cap / net_income
    else:
        multiples = {
            "ev_rev": None,
            "ev_ebitda": None,
            "pe": None,
        }

    return {
        "target_metrics": {
            "revenue": revenue,
            "ebitda": ebitda,
            "net_income": net_income,
        },
        "multiples": multiples,
        "note": "MVP: Comps analysis limited to target company only. Full peer analysis requires database of comparable companies.",
    }


# Formula template dictionary for comps/relative valuation Excel output
# Format: {cell_address: formula_string}
# All formulas reference cells in the same sheet
COMPS_FORMULAS: Dict[str, str] = {
    # Multiple calculations for peer companies (rows 5-9)
    "D5": "=G16/F16",
    "E5": "=E16/(F16/K16)",
    "F5": "=E16/I16",
    "G5": "=E16/(J16/K16)",
    
    "D6": "=G17/F17",
    "E6": "=E17/(F17/K17)",
    "F6": "=E17/I17",
    "G6": "=E17/(J17/K17)",
    
    "D7": "=G18/F18",
    "E7": "=E18/(F18/J18)",
    "F7": "=E18/H18",
    "G7": "=E18/(I18/J18)",
    
    "D8": "=G19/F19",
    "E8": "=E19/(F19/J19)",
    "F8": "=E19/H19",
    "G8": "=E19/(I19/J19)",
    
    "D9": "=G20/F20",
    "E9": "=E20/(F20/J20)",
    "F9": "=E20/H20",
    "G9": "=E20/(I20/J20)",
    
    # Minimum multiples (row 10)
    "D10": "=MIN(D5:D9)",
    "E10": "=MIN(E5:E9)",
    "F10": "=MIN(F5:F9)",
    "G10": "=MIN(G5:G9)",
    
    # Weighted calculation
    "J10": "=(D13*J5)+(E13*J6)+(F13*J7)+(G13*J8)",
    
    # Average multiples (row 11)
    "D11": "=AVERAGE(D5:D9)",
    "E11": "=AVERAGE(E5:E9)",
    "F11": "=AVERAGE(F5:F9)",
    "G11": "=AVERAGE(G5:G9)",
    
    # Implied valuation calculation
    "J11": "=(J10/E20)-1",
    
    # Maximum multiples (row 12)
    "D12": "=MAX(D5:D9)",
    "E12": "=MAX(E5:E9)",
    "F12": "=MAX(F5:F9)",
    "G12": "=MAX(G5:G9)",
    
    # Final valuation calculations (row 13)
    "D13": "=(D11*(F16-H16))/K16",
    "E13": "=E11*(F16/K16)",
    "F13": "=F11*(I16)",
    "G13": "=G11*(J16/K16)",
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


def write_comps_sheet(
    workbook,
    comps_data: Dict[str, Any],
    peer_companies: Optional[List[Dict[str, Any]]] = None,
    sheet_name: str = "Comps Analysis",
    start_row: int = 0,
    start_col: int = 0,
    custom_formulas: Optional[Dict[str, str]] = None,
) -> None:
    """
    Write comparable companies (comps) analysis to Excel worksheet with formulas.
    
    Helper for excel_export.py to write the relative valuation/comps analysis to Excel.
    This function writes both calculated values and Excel formulas for
    interactive modeling.
    
    Expected usage:
        workbook = xlsxwriter.Workbook(...)
        comps_data = run_comps(...)
        write_comps_sheet(workbook, comps_data, peer_companies)
    
    Args:
        workbook: xlsxwriter Workbook object
        comps_data: Output from run_comps() containing:
            - target_metrics: Dict with revenue, ebitda, net_income
            - multiples: Dict with ev_rev, ev_ebitda, pe
            - note: str
        peer_companies: Optional list of peer company data dicts, each containing:
            - name: str
            - revenue: float
            - ebitda: float
            - net_income: float
            - market_cap: float
            - enterprise_value: float
            - multiples: Dict with ev_rev, ev_ebitda, pe
        sheet_name: Name of the Excel worksheet (default: "Comps Analysis")
        start_row: Starting row for the table (0-indexed, default: 0)
        start_col: Starting column for the table (0-indexed, default: 0)
        custom_formulas: Optional dict mapping cell addresses to formula strings.
                        If provided, these formulas will be used instead of default formulas.
                        Example: {"B10": "=AVERAGE(B2:B9)", "C10": "=B10*D5"}
    
    The sheet contains:
        - Header row with company names and metrics
        - Peer company data table
        - Target company row
        - Multiple calculations (EV/Revenue, EV/EBITDA, P/E)
        - Implied valuation calculations
        - Excel formulas for calculations (from COMPS_FORMULAS or custom_formulas)
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
    
    # Write header row
    worksheet.write(start_row, start_col, "Company", header_format)
    worksheet.write(start_row, start_col + 1, "Revenue", header_format)
    worksheet.write(start_row, start_col + 2, "EBITDA", header_format)
    worksheet.write(start_row, start_col + 3, "Net Income", header_format)
    worksheet.write(start_row, start_col + 4, "Market Cap", header_format)
    worksheet.write(start_row, start_col + 5, "Enterprise Value", header_format)
    worksheet.write(start_row, start_col + 6, "EV/Revenue", header_format)
    worksheet.write(start_row, start_col + 7, "EV/EBITDA", header_format)
    worksheet.write(start_row, start_col + 8, "P/E", header_format)
    
    current_row = start_row + 1
    
    # Write peer companies data
    if peer_companies:
        for peer in peer_companies:
            col_letter = _col_to_letter(start_col)
            cell_address = f"{col_letter}{current_row + 1}"
            
            # Company name
            worksheet.write(current_row, start_col, peer.get("name", ""), label_format)
            
            # Write data or formulas for each metric
            for col_idx, metric_key in enumerate(["revenue", "ebitda", "net_income", "market_cap", "enterprise_value"], 1):
                col_letter = _col_to_letter(start_col + col_idx)
                cell_address = f"{col_letter}{current_row + 1}"
                
                if custom_formulas and cell_address in custom_formulas:
                    worksheet.write(current_row, start_col + col_idx, custom_formulas[cell_address], formula_format)
                elif cell_address in COMPS_FORMULAS:
                    worksheet.write(current_row, start_col + col_idx, COMPS_FORMULAS[cell_address], formula_format)
                else:
                    value = peer.get(metric_key, 0.0)
                    worksheet.write(current_row, start_col + col_idx, value, currency_format)
            
            # Write multiples (formulas or calculated)
            for col_idx, multiple_key in enumerate(["ev_rev", "ev_ebitda", "pe"], 6):
                col_letter = _col_to_letter(start_col + col_idx)
                cell_address = f"{col_letter}{current_row + 1}"
                
                if custom_formulas and cell_address in custom_formulas:
                    worksheet.write(current_row, start_col + col_idx, custom_formulas[cell_address], formula_format)
                elif cell_address in COMPS_FORMULAS:
                    worksheet.write(current_row, start_col + col_idx, COMPS_FORMULAS[cell_address], formula_format)
                else:
                    multiples = peer.get("multiples", {})
                    value = multiples.get(multiple_key)
                    if value is not None:
                        worksheet.write(current_row, start_col + col_idx, value, number_format)
            
            current_row += 1
    
    # Write target company row
    worksheet.write(current_row, start_col, "Target Company", label_format)
    
    target_metrics = comps_data.get("target_metrics", {})
    multiples = comps_data.get("multiples", {})
    
    # Write target company metrics
    for col_idx, metric_key in enumerate(["revenue", "ebitda", "net_income"], 1):
        col_letter = _col_to_letter(start_col + col_idx)
        cell_address = f"{col_letter}{current_row + 1}"
        
        if custom_formulas and cell_address in custom_formulas:
            worksheet.write(current_row, start_col + col_idx, custom_formulas[cell_address], formula_format)
        elif cell_address in COMPS_FORMULAS:
            worksheet.write(current_row, start_col + col_idx, COMPS_FORMULAS[cell_address], formula_format)
        else:
            value = target_metrics.get(metric_key, 0.0)
            worksheet.write(current_row, start_col + col_idx, value, currency_format)
    
    # Market cap and EV (if available)
    for col_idx in [4, 5]:
        col_letter = _col_to_letter(start_col + col_idx)
        cell_address = f"{col_letter}{current_row + 1}"
        
        if custom_formulas and cell_address in custom_formulas:
            worksheet.write(current_row, start_col + col_idx, custom_formulas[cell_address], formula_format)
        elif cell_address in COMPS_FORMULAS:
            worksheet.write(current_row, start_col + col_idx, COMPS_FORMULAS[cell_address], formula_format)
        # Otherwise leave blank (target company may not have market data)
    
    # Write target multiples
    for col_idx, multiple_key in enumerate(["ev_rev", "ev_ebitda", "pe"], 6):
        col_letter = _col_to_letter(start_col + col_idx)
        cell_address = f"{col_letter}{current_row + 1}"
        
        if custom_formulas and cell_address in custom_formulas:
            worksheet.write(current_row, start_col + col_idx, custom_formulas[cell_address], formula_format)
        elif cell_address in COMPS_FORMULAS:
            worksheet.write(current_row, start_col + col_idx, COMPS_FORMULAS[cell_address], formula_format)
        else:
            value = multiples.get(multiple_key)
            if value is not None:
                worksheet.write(current_row, start_col + col_idx, value, number_format)
    
    current_row += 2
    
    # Write summary/average multiples
    worksheet.write(current_row, start_col, "Average Multiple", label_format)
    
    # Calculate average multiples from peers (if peers exist)
    if peer_companies and len(peer_companies) > 0:
        for col_idx, multiple_key in enumerate(["ev_rev", "ev_ebitda", "pe"], 6):
            col_letter = _col_to_letter(start_col + col_idx)
            cell_address = f"{col_letter}{current_row + 1}"
            
            if custom_formulas and cell_address in custom_formulas:
                worksheet.write(current_row, start_col + col_idx, custom_formulas[cell_address], formula_format)
            elif cell_address in COMPS_FORMULAS:
                worksheet.write(current_row, start_col + col_idx, COMPS_FORMULAS[cell_address], formula_format)
            else:
                # Default: calculate average from peer data
                # Find the column range for this multiple
                first_peer_row = start_row + 2  # After header and first peer
                last_peer_row = start_row + 1 + len(peer_companies)
                formula = f"=AVERAGE({col_letter}{first_peer_row}:{col_letter}{last_peer_row})"
                worksheet.write(current_row, start_col + col_idx, formula, formula_format)
    
    # Set column widths for readability
    worksheet.set_column(start_col, start_col, 20)  # Company name column
    for col_idx in range(1, 9):
        worksheet.set_column(start_col + col_idx, start_col + col_idx, 15)  # Data columns
