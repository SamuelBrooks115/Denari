"""
sensitivity.py — DCF Sensitivity Analysis

Purpose:
- Create sensitivity analysis table for DCF valuation
- References WACC and Terminal Growth from DCF sheet
- Creates 5x5 matrix with base case in center
- Uses Excel formulas and conditional formatting for dynamic updates

This module:
- Creates Excel formulas that reference DCF sheet cells
- Builds sensitivity table with color gradient (green=high, yellow=middle, red=low)
- Makes cell references dynamic to handle row changes in DCF sheet
"""

from typing import Dict, Any, Optional
import re

# Sensitivity table formulas template
# These formulas reference cells in the DCF sheet to calculate share prices
# The formulas will be applied to the sensitivity table data cells (5x5 grid)
# Format: {cell_address: formula_template}
# The formula_template can use {dcf_sheet_name} placeholder which will be replaced
# with the actual DCF sheet name (e.g., "DCF Base", "DCF Bear", "DCF Bull")
# Absolute references (like $G$31) will be prefixed with the DCF sheet name

SENSITIVITY_FORMULA_TEMPLATE: Dict[str, str] = {
    # Column E formulas (WACC values)
    "E53": "=K48",
    "E54": "=E55-C52",
    "E55": "=E56-C52",
    "E56": "=E14",
    "E57": "=E56+C52",
    "E58": "=E57+C52",
    
    # Column F formulas
    "F53": "=G53-C53",
    "F54": "=($G$31/(1+$E$54)^$G$34+$H$31/(1+$E$54)^$H$34+$I$31/(1+$E$54)^$I$34+$J$31/(1+$E$54)^$J$34+$K$31/(1+$E$54)^$K$34+(($K$31*(1+F$53))/($E54-F$53))/(1+$E54)^$K$34-$K$44)/$K$47",
    "F55": "=($G$31/(1+$E$55)^$G$34+$H$31/(1+$E$55)^$H$34+$I$31/(1+$E$55)^$I$34+$J$31/(1+$E$55)^$J$34+$K$31/(1+$E$55)^$K$34+(($K$31*(1+F$53))/($E55-F$53))/(1+$E$55)^$K$34-$K$44)/$K$47",
    "F56": "=($G$31/(1+$E$56)^$G$34+$H$31/(1+$E$56)^$H$34+$I$31/(1+$E$56)^$I$34+$J$31/(1+$E$56)^$J$34+$K$31/(1+$E$56)^$K$34+(($K$31*(1+F$53))/($E$56-F$53))/(1+$E$56)^$K$34-$K$44)/$K$47",
    "F57": "=($G$31/(1+$E$57)^$G$34+$H$31/(1+$E$57)^$H$34+$I$31/(1+$E$57)^$I$34+$J$31/(1+$E$57)^$J$34+$K$31/(1+$E$57)^$K$34+(($K$31*(1+F$53))/($E$57-F$53))/(1+$E$57)^$K$34-$K$44)/$K$47",
    "F58": "=($G$31/(1+$E$58)^$G$34+$H$31/(1+$E$58)^$H$34+$I$31/(1+$E$58)^$I$34+$J$31/(1+$E$58)^$J$34+$K$31/(1+$E$58)^$K$34+(($K$31*(1+F$53))/($E$58-F$53))/(1+$E$58)^$K$34-$K$44)/$K$47",
    
    # Column G formulas
    "G53": "=H53-C53",
    "G54": "=($G$31/(1+$E$54)^$G$34+$H$31/(1+$E$54)^$H$34+$I$31/(1+$E$54)^$I$34+$J$31/(1+$E$54)^$J$34+$K$31/(1+$E$54)^$K$34+(($K$31*(1+G$53))/($E54-G$53))/(1+$E54)^$K$34-$K$44)/$K$47",
    "G55": "=($G$31/(1+$E$55)^$G$34+$H$31/(1+$E$55)^$H$34+$I$31/(1+$E$55)^$I$34+$J$31/(1+$E$55)^$J$34+$K$31/(1+$E$55)^$K$34+(($K$31*(1+G$53))/($E55-G$53))/(1+$E$55)^$K$34-$K$44)/$K$47",
    "G56": "=($G$31/(1+$E$56)^$G$34+$H$31/(1+$E$56)^$H$34+$I$31/(1+$E$56)^$I$34+$J$31/(1+$E$56)^$J$34+$K$31/(1+$E$56)^$K$34+(($K$31*(1+G$53))/($E$56-G$53))/(1+$E$56)^$K$34-$K$44)/$K$47",
    "G57": "=($G$31/(1+$E$57)^$G$34+$H$31/(1+$E$57)^$H$34+$I$31/(1+$E$57)^$I$34+$J$31/(1+$E$57)^$J$34+$K$31/(1+$E$57)^$K$34+(($K$31*(1+G$53))/($E$57-G$53))/(1+$E$57)^$K$34-$K$44)/$K$47",
    "G58": "=($G$31/(1+$E$58)^$G$34+$H$31/(1+$E$58)^$H$34+$I$31/(1+$E$58)^$I$34+$J$31/(1+$E$58)^$J$34+$K$31/(1+$E$58)^$K$34+(($K$31*(1+G$53))/($E$58-G$53))/(1+$E$58)^$K$34-$K$44)/$K$47",
    
    # Column H formulas
    "H53": "=J6",
    "H54": "=($G$31/(1+$E$54)^$G$34+$H$31/(1+$E$54)^$H$34+$I$31/(1+$E$54)^$I$34+$J$31/(1+$E$54)^$J$34+$K$31/(1+$E$54)^$K$34+(($K$31*(1+H$53))/($E54-H$53))/(1+$E54)^$K$34-$K$44)/$K$47",
    "H55": "=($G$31/(1+$E$55)^$G$34+$H$31/(1+$E$55)^$H$34+$I$31/(1+$E$55)^$I$34+$J$31/(1+$E$55)^$J$34+$K$31/(1+$E$55)^$K$34+(($K$31*(1+H$53))/($E55-H$53))/(1+$E$55)^$K$34-$K$44)/$K$47",
    "H56": "=($G$31/(1+$E$56)^$G$34+$H$31/(1+$E$56)^$H$34+$I$31/(1+$E$56)^$I$34+$J$31/(1+$E$56)^$J$34+$K$31/(1+$E$56)^$K$34+(($K$31*(1+H$53))/($E$56-H$53))/(1+$E$56)^$K$34-$K$44)/$K$47",
    "H57": "=($G$31/(1+$E$57)^$G$34+$H$31/(1+$E$57)^$H$34+$I$31/(1+$E$57)^$I$34+$J$31/(1+$E$57)^$J$34+$K$31/(1+$E$57)^$K$34+(($K$31*(1+H$53))/($E$57-H$53))/(1+$E$57)^$K$34-$K$44)/$K$47",
    "H58": "=($G$31/(1+$E$58)^$G$34+$H$31/(1+$E$58)^$H$34+$I$31/(1+$E$58)^$I$34+$J$31/(1+$E$58)^$J$34+$K$31/(1+$E$58)^$K$34+(($K$31*(1+H$53))/($E$58-H$53))/(1+$E$58)^$K$34-$K$44)/$K$47",
    
    # Column I formulas
    "I53": "=H53+C53",
    "I54": "=($G$31/(1+$E$54)^$G$34+$H$31/(1+$E$54)^$H$34+$I$31/(1+$E$54)^$I$34+$J$31/(1+$E$54)^$J$34+$K$31/(1+$E$54)^$K$34+(($K$31*(1+I$53))/($E54-I$53))/(1+$E54)^$K$34-$K$44)/$K$47",
    "I55": "=($G$31/(1+$E$55)^$G$34+$H$31/(1+$E$55)^$H$34+$I$31/(1+$E$55)^$I$34+$J$31/(1+$E$55)^$J$34+$K$31/(1+$E$55)^$K$34+(($K$31*(1+I$53))/($E55-I$53))/(1+$E$55)^$K$34-$K$44)/$K$47",
    "I56": "=($G$31/(1+$E$56)^$G$34+$H$31/(1+$E$56)^$H$34+$I$31/(1+$E$56)^$I$34+$J$31/(1+$E$56)^$J$34+$K$31/(1+$E$56)^$K$34+(($K$31*(1+I$53))/($E$56-I$53))/(1+$E$56)^$K$34-$K$44)/$K$47",
    "I57": "=($G$31/(1+$E$57)^$G$34+$H$31/(1+$E$57)^$H$34+$I$31/(1+$E$57)^$I$34+$J$31/(1+$E$57)^$J$34+$K$31/(1+$E$57)^$K$34+(($K$31*(1+I$53))/($E$57-I$53))/(1+$E$57)^$K$34-$K$44)/$K$47",
    "I58": "=($G$31/(1+$E$58)^$G$34+$H$31/(1+$E$58)^$H$34+$I$31/(1+$E$58)^$I$34+$J$31/(1+$E$58)^$J$34+$K$31/(1+$E$58)^$K$34+(($K$31*(1+I$53))/($E$58-I$53))/(1+$E$58)^$K$34-$K$44)/$K$47",
    
    # Column J formulas
    "J53": "=I53+C53",
    "J54": "=($G$31/(1+$E$54)^$G$34+$H$31/(1+$E$54)^$H$34+$I$31/(1+$E$54)^$I$34+$J$31/(1+$E$54)^$J$34+$K$31/(1+$E$54)^$K$34+(($K$31*(1+J$53))/($E54-J$53))/(1+$E54)^$K$34-$K$44)/$K$47",
    "J55": "=($G$31/(1+$E$55)^$G$34+$H$31/(1+$E$55)^$H$34+$I$31/(1+$E$55)^$I$34+$J$31/(1+$E$55)^$J$34+$K$31/(1+$E$55)^$K$34+(($K$31*(1+J$53))/($E55-J$53))/(1+$E$55)^$K$34-$K$44)/$K$47",
    "J56": "=($G$31/(1+$E$56)^$G$34+$H$31/(1+$E$56)^$H$34+$I$31/(1+$E$56)^$I$34+$J$31/(1+$E$56)^$J$34+$K$31/(1+$E$56)^$K$34+(($K$31*(1+J$53))/($E$56-J$53))/(1+$E$56)^$K$34-$K$44)/$K$47",
    "J57": "=($G$31/(1+$E$57)^$G$34+$H$31/(1+$E$57)^$H$34+$I$31/(1+$E$57)^$I$34+$J$31/(1+$E$57)^$J$34+$K$31/(1+$E$57)^$K$34+(($K$31*(1+J$53))/($E$57-J$53))/(1+$E$57)^$K$34-$K$44)/$K$47",
    "J58": "=($G$31/(1+$E$58)^$G$34+$H$31/(1+$E$58)^$H$34+$I$31/(1+$E$58)^$I$34+$J$31/(1+$E$58)^$J$34+$K$31/(1+$E$58)^$K$34+(($K$31*(1+J$53))/($E$58-J$53))/(1+$E$58)^$K$34-$K$44)/$K$47",
}


def _add_dcf_sheet_to_formula(formula: str, dcf_sheet_name: str) -> str:
    """
    Add DCF sheet name prefix to cell references that should reference the DCF sheet.
    
    This function intelligently adds the DCF sheet prefix:
    - Absolute references ($G$31, $E$54) → 'DCF Base'!$G$31 (references DCF sheet)
    - Mixed references with $ ($E54, E$54, F$53) → 'DCF Base'!$E54 (references DCF sheet)
    - Relative references (E55, C52, G53) → kept as-is (references same sensitivity sheet)
    
    Args:
        formula: Excel formula string (e.g., "=E55-C52" or "=$G$31/(1+$E$54)")
        dcf_sheet_name: Name of the DCF sheet (e.g., "DCF Base")
        
    Returns:
        Formula with DCF sheet prefixes added only to absolute/mixed references
    """
    if not formula.startswith('='):
        return formula
    
    formula_body = formula[1:]
    
    # Pattern 1: Absolute references ($G$31, $E$54) - these should reference DCF sheet
    def add_sheet_to_absolute(match):
        cell_ref = match.group(0)
        # Check if already has sheet prefix
        start = max(0, match.start() - 30)
        end = min(len(formula_body), match.end() + 30)
        context = formula_body[start:end]
        if "'" in context and "!" in context:
            sheet_pattern = r"'[^']+'!" + re.escape(cell_ref)
            if re.search(sheet_pattern, context):
                return cell_ref
        return f"'{dcf_sheet_name}'!{cell_ref}"
    
    # Pattern 2: Mixed references ($E54, E$54, F$53) - these should reference DCF sheet
    def add_sheet_to_mixed(match):
        cell_ref = match.group(0)
        # Check if already has sheet prefix
        start = max(0, match.start() - 30)
        end = min(len(formula_body), match.end() + 30)
        context = formula_body[start:end]
        if "'" in context and "!" in context:
            sheet_pattern = r"'[^']+'!" + re.escape(cell_ref)
            if re.search(sheet_pattern, context):
                return cell_ref
        return f"'{dcf_sheet_name}'!{cell_ref}"
    
    # First, replace absolute references ($Column$Row)
    processed = re.sub(r'\$[A-Z]{1,3}\$\d{1,7}', add_sheet_to_absolute, formula_body)
    
    # Then, replace mixed references ($ColumnRow or Column$Row)
    processed = re.sub(r'\$[A-Z]{1,3}\d{1,7}|[A-Z]{1,3}\$\d{1,7}', add_sheet_to_mixed, processed)
    
    # Relative references (like E55, C52, G53) are left as-is - they reference the same sensitivity sheet
    
    return f"={processed}"


def write_sensitivity_sheet(
    workbook, 
    dcf_sheet_name: str = "DCF",
    wacc_cell: str = "E14",
    terminal_growth_cell: str = "J6",
    share_price_cell: Optional[str] = None,
    start_row: int = 0,
    start_col: int = 0,
    ticker: Optional[str] = None,
    wacc_step_cell: Optional[str] = None,
    terminal_growth_step_cell: Optional[str] = None,
    scenario_name: Optional[str] = None,
    data_range: Optional[str] = None,
    custom_formulas: Optional[Dict[str, str]] = None
):
    """
    Write sensitivity analysis table to Excel worksheet using dynamic cell references.
    
    This function creates a 5x5 sensitivity matrix that references the DCF sheet:
    - WACC values: base +/- 1% (5 values: base-2%, base-1%, base, base+1%, base+2%)
    - Terminal Growth values: base +/- 0.025 (5 values: base-0.05, base-0.025, base, base+0.025, base+0.05)
    - Base case is in the center (row 3, col 3)
    
    Expected usage:
        workbook = xlsxwriter.Workbook(...)
        # DCF sheet must exist with WACC in E14 and Terminal Growth in J6
        write_sensitivity_sheet(workbook, dcf_sheet_name="DCF", ticker="AAPL")
        
        # For scenario-specific tables:
        write_sensitivity_sheet(workbook, dcf_sheet_name="DCF Base", scenario_name="Base")
        write_sensitivity_sheet(workbook, dcf_sheet_name="DCF Bear", scenario_name="Bear")
        write_sensitivity_sheet(workbook, dcf_sheet_name="DCF Bull", scenario_name="Bull")
    
    Args:
        workbook: xlsxwriter Workbook object
        dcf_sheet_name: Name of the DCF sheet (default: "DCF")
        wacc_cell: Cell reference for WACC in DCF sheet (default: "E14")
        terminal_growth_cell: Cell reference for Terminal Growth in DCF sheet (default: "J6")
        share_price_cell: Optional cell reference for share price output (if None, will be calculated)
        start_row: Starting row for sensitivity table (0-indexed, default: 0)
        start_col: Starting column for sensitivity table (0-indexed, default: 0)
        ticker: Optional ticker symbol for header
        wacc_step_cell: Optional cell reference for WACC step size (if None, creates cell with default 0.01)
        terminal_growth_step_cell: Optional cell reference for Terminal Growth step size (if None, creates cell with default 0.025)
        scenario_name: Optional scenario name (e.g., "Base", "Bear", "Bull") for sheet naming
        data_range: Optional explicit cell range for conditional formatting (e.g., "F54:K58"). If None, calculated automatically.
        custom_formulas: Optional dict mapping cell addresses (e.g., "F54") to formula strings.
                         If provided, these formulas will be used instead of default formulas.
                         Example: {"F54": "='DCF Base'!$B$10", "G54": "='DCF Base'!$B$11"}
    
    The sheet contains:
        - Header with ticker (if provided)
        - 5x5 sensitivity table with formulas referencing DCF sheet
        - Color gradient formatting (soft green=high, soft yellow=middle, soft red=low)
        - Base case highlighted with border
    """
    import xlsxwriter
    
    # Create worksheet name based on scenario
    if scenario_name:
        sheet_name = f"Sensitivity Analysis - {scenario_name}"
    else:
        sheet_name = "Sensitivity Analysis"
    worksheet = workbook.add_worksheet(sheet_name)
    
    # Set column widths
    worksheet.set_column('A:A', 16)  # WACC column
    worksheet.set_column('B:F', 14)  # Data columns (5 columns)
    
    # Create formats
    header_format = workbook.add_format({
        'bold': True, 
        'bg_color': '#D3D3D3', 
        'align': 'center',
        'valign': 'vcenter',
        'border': 1
    })
    
    percent_format = workbook.add_format({'num_format': '0.00%', 'border': 1})
    currency_format = workbook.add_format({'num_format': '$#,##0.00', 'border': 1})
    
    # Color formats for gradient (green to yellow to red)
    # High values (green shades)
    format_green_dark = workbook.add_format({
        'num_format': '$#,##0.00', 
        'bg_color': '#006100',  # Dark green
        'font_color': '#FFFFFF',
        'border': 1
    })
    format_green_medium = workbook.add_format({
        'num_format': '$#,##0.00', 
        'bg_color': '#C6EFCE',  # Light green
        'border': 1
    })
    format_green_light = workbook.add_format({
        'num_format': '$#,##0.00', 
        'bg_color': '#E2EFDA',  # Very light green
        'border': 1
    })
    
    # Middle values (yellow)
    format_yellow = workbook.add_format({
        'num_format': '$#,##0.00', 
        'bg_color': '#FFEB9C',  # Yellow
        'border': 2,  # Thicker border for base case
        'bold': True
    })
    
    # Low values (red shades)
    format_red_light = workbook.add_format({
        'num_format': '$#,##0.00', 
        'bg_color': '#FFC7CE',  # Light red
        'border': 1
    })
    format_red_medium = workbook.add_format({
        'num_format': '$#,##0.00', 
        'bg_color': '#FF9999',  # Medium red
        'border': 1
    })
    format_red_dark = workbook.add_format({
        'num_format': '$#,##0.00', 
        'bg_color': '#C00000',  # Dark red
        'font_color': '#FFFFFF',
        'border': 1
    })
    
    # Build cell references with sheet name
    wacc_ref = f"'{dcf_sheet_name}'!{wacc_cell}"
    terminal_growth_ref = f"'{dcf_sheet_name}'!{terminal_growth_cell}"
    
    # Helper function to convert column index to Excel column letter
    def col_to_letter(col_idx):
        """Convert 0-based column index to Excel column letter (A, B, ..., Z, AA, AB, ...)"""
        result = ""
        col_idx += 1  # Convert to 1-based
        while col_idx > 0:
            col_idx -= 1
            result = chr(65 + (col_idx % 26)) + result
            col_idx //= 26
        return result
    
    # Set up step size cells (create them if not provided)
    # Place step size inputs in cells before the table
    step_row = start_row
    if wacc_step_cell:
        wacc_step_ref = wacc_step_cell
    else:
        # Create step size cell in column after ticker/references
        step_col = start_col + 2
        step_value_col = start_col + 3
        worksheet.write(step_row + 2, step_col, "WACC Step", header_format)
        worksheet.write(step_row + 2, step_value_col, 0.01, percent_format)  # Default 1%
        wacc_step_ref = f"{col_to_letter(step_value_col)}{step_row + 3}"  # Actual cell with value (1-indexed row)
    
    if terminal_growth_step_cell:
        tg_step_ref = terminal_growth_step_cell
    else:
        # Create step size cell
        step_col = start_col + 2
        step_value_col = start_col + 3
        worksheet.write(step_row + 3, step_col, "TG Step", header_format)
        worksheet.write(step_row + 3, step_value_col, 0.025, percent_format)  # Default 2.5%
        tg_step_ref = f"{col_to_letter(step_value_col)}{step_row + 4}"  # Actual cell with value (1-indexed row)
    
    # Write header information
    row = start_row
    if ticker:
        worksheet.write(row, start_col, "Ticker", header_format)
        worksheet.write(row, start_col + 1, ticker)
        row += 1
    
    # Write reference cells (for debugging/verification)
    worksheet.write(row, start_col, "WACC Reference", header_format)
    worksheet.write(row, start_col + 1, f"={wacc_ref}", percent_format)
    row += 1
    
    worksheet.write(row, start_col, "Terminal Growth Reference", header_format)
    worksheet.write(row, start_col + 1, f"={terminal_growth_ref}", percent_format)
    row += 2  # Skip a row
    
    # Write table header
    table_start_row = row
    # Top-left corner
    worksheet.write(row, start_col, "WACC \\ Terminal Growth", header_format)
    
    # Column headers (Terminal Growth values)
    # 5 values: base-2*step, base-step, base, base+step, base+2*step
    col = start_col + 1
    tg_multipliers = [-2, -1, 0, 1, 2]
    
    for multiplier in tg_multipliers:
        if multiplier == 0:
            formula = f"={terminal_growth_ref}"
        else:
            # Reference step size cell: base + (multiplier * step)
            formula = f"={terminal_growth_ref}+{multiplier}*{tg_step_ref}"
        header_cell_format = workbook.add_format({
            'bold': True, 
            'bg_color': '#D3D3D3', 
            'align': 'center',
            'num_format': '0.00%',
            'border': 1
        })
        worksheet.write(row, col, formula, header_cell_format)
        col += 1
    
    row += 1
    
    # Write data rows
    # 5 WACC values: base-2*step, base-step, base, base+step, base+2*step
    wacc_multipliers = [-2, -1, 0, 1, 2]
    
    # Store cell range for conditional formatting (Excel uses 1-indexed rows)
    data_range_start_row_excel = row + 2  # First data row (Excel 1-indexed: row + 1 + 1 for header)
    data_range_start_col = start_col + 1  # First data column (0-indexed)
    data_range_end_row_excel = row + 6  # Last data row (Excel 1-indexed: 5 rows of data)
    data_range_end_col = start_col + 5  # Last data column (0-indexed: 5 columns)
    
    for wacc_idx, wacc_multiplier in enumerate(wacc_multipliers):
        # Row header (WACC value)
        if wacc_multiplier == 0:
            wacc_formula = f"={wacc_ref}"
        else:
            # Reference step size cell: base + (multiplier * step)
            wacc_formula = f"={wacc_ref}+{wacc_multiplier}*{wacc_step_ref}"
        
        wacc_header_format = workbook.add_format({
            'bold': True, 
            'bg_color': '#D3D3D3', 
            'align': 'right',
            'num_format': '0.00%',
            'border': 1
        })
        worksheet.write(row, start_col, wacc_formula, wacc_header_format)
        
        # Data cells (share prices)
        # Each cell calculates share price using the WACC and TG variations
        # The formula references the DCF sheet's share price calculation
        # Note: The DCF sheet should reference input cells that can be varied
        
        for tg_idx, tg_multiplier in enumerate(tg_multipliers):
            # Calculate the WACC and TG values for this cell using step size references
            # WACC formula: base + (multiplier * step)
            if wacc_multiplier == 0:
                wacc_value_formula = wacc_ref
            else:
                wacc_value_formula = f"{wacc_ref}+{wacc_multiplier}*{wacc_step_ref}"
            
            # Terminal Growth formula: base + (multiplier * step)
            if tg_multiplier == 0:
                tg_value_formula = terminal_growth_ref
            else:
                tg_value_formula = f"{terminal_growth_ref}+{tg_multiplier}*{tg_step_ref}"
            
            # Create formula that references share price calculation
            # If custom formulas are provided, use them; otherwise use default logic
            # The formula should reference the DCF sheet's share price calculation
            # with the appropriate WACC and TG values for this cell
            
            # Calculate the cell position for this data cell (for custom formula mapping)
            # Excel row = row + 1 (convert from 0-indexed to 1-indexed)
            # Excel col = start_col + 1 + tg_idx (0-indexed column position)
            excel_row = row + 1
            excel_col_letter = col_to_letter(start_col + 1 + tg_idx)
            cell_address = f"{excel_col_letter}{excel_row}"
            
            # Determine border format based on cell position
            # Table boundaries: E53:J58 (Excel addresses)
            # Check if this cell is in the formula template (E53-J58 range)
            is_in_template = cell_address in SENSITIVITY_FORMULA_TEMPLATE
            
            # Determine specific border requirements
            is_header_row = (excel_row == 53)  # Row 53 (E53:J53)
            is_first_col = (excel_col_letter == "E")  # Column E
            is_center_cell = (cell_address == "H56")  # Center/base case cell
            
            # Create format with appropriate borders
            # Default: use currency format
            cell_format = currency_format
            
            # If cell is in our formula template (E53-J58), apply borders
            if is_in_template:
                # Build border format based on cell position
                border_options = {
                    'num_format': '$#,##0.00',
                    'border': 2  # Thick border for all table cells
                }
                
                # Add specific borders
                if is_header_row:
                    border_options['bottom'] = 1  # Single bottom border under header
                if is_first_col:
                    border_options['right'] = 1   # Single right border on first column
                if is_center_cell:
                    # Center cell gets thick outside border (already set with border: 2)
                    pass
                
                cell_format = workbook.add_format(border_options)
            
            # Check if custom formula is provided for this cell
            if custom_formulas and cell_address in custom_formulas:
                formula = custom_formulas[cell_address]
            elif cell_address in SENSITIVITY_FORMULA_TEMPLATE:
                # Use template formula
                formula = SENSITIVITY_FORMULA_TEMPLATE[cell_address]
                # Add DCF sheet name prefix to all cell references in the formula
                formula = _add_dcf_sheet_to_formula(formula, dcf_sheet_name)
            else:
                # Default formula logic
                if share_price_cell:
                    # Reference the share price output from DCF sheet
                    share_price_ref = f"'{dcf_sheet_name}'!{share_price_cell}"
                    formula = f"={share_price_ref}"
                else:
                    # Placeholder formula - user should provide actual formulas via custom_formulas
                    # This assumes the DCF sheet will recalculate based on WACC/TG input cells
                    formula = f"=IF({wacc_value_formula}>{tg_value_formula},\"See DCF Setup\",\"N/A\")"
            
            # Write formula with appropriate border format
            worksheet.write(row, start_col + 1 + tg_idx, formula, cell_format)
        
        row += 1
    
    # Apply conditional formatting with color scale (green-yellow-red)
    # Format the data range (5x5 grid of share prices)
    # Use provided data_range if specified, otherwise calculate automatically
    if data_range is None:
        data_range = f"{col_to_letter(data_range_start_col)}{data_range_start_row_excel}:{col_to_letter(data_range_end_col)}{data_range_end_row_excel}"

    # Apply 3-color scale: red (low) -> yellow (mid) -> green (high)
    # Using soft colors: soft red -> soft yellow -> soft green
    # min_color applies to minimum value (low share prices = red/bad)
    # max_color applies to maximum value (high share prices = green/good)
    worksheet.conditional_format(
        data_range,
        {
            'type': '3_color_scale',
            'min_type': 'min',  # Automatically find minimum value in range
            'min_color': '#F5B7B1',  # Soft red (for low share prices)
            'mid_type': 'percentile',
            'mid_value': 50,
            'mid_color': '#F9E79F',  # Soft yellow (middle)
            'max_type': 'max',  # Automatically find maximum value in range
            'max_color': '#ABEBC6',  # Soft green (for high share prices)
        }
    )
    
    
    # Add notes
    row += 1
    note_format = workbook.add_format({'italic': True, 'font_color': '#666666'})
    worksheet.write(row, start_col, "Note: Color scale applied (green=high, yellow=middle, red=low)", note_format)
    row += 1
    worksheet.write(row, start_col, f"WACC references: {dcf_sheet_name}!{wacc_cell}, Terminal Growth references: {dcf_sheet_name}!{terminal_growth_cell}", note_format)
    row += 1
    worksheet.write(row, start_col, f"WACC Step: {wacc_step_ref}, Terminal Growth Step: {tg_step_ref}", note_format)
    row += 1
    worksheet.write(row, start_col, "To make cell references dynamic (handle row changes), use INDIRECT() or named ranges in DCF sheet", note_format)

