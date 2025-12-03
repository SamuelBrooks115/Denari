"""
excel_export.py — Excel Workbook Export Builder

Purpose:
- Convert model outputs (projections, DCF, comps) into a structured .xlsx file.
- This is the final client-facing artifact used by analysts and investors.
- Template-driven approach to ensure readability and familiarity.

Inputs:
- company_id
- model_version (optional)
- DB session (for historicals + assumptions)
- Must call:
    run_three_statement()
    run_dcf()
    run_comps()
  to gather values prior to export.

Outputs:
- In-memory .xlsx file (returned as bytes or BytesIO stream).

This module does NOT:
- Perform valuation logic.
- Fetch filings or prices.
"""

from io import BytesIO
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

from app.services.modeling.three_statement import run_three_statement
from app.services.modeling.dcf import run_dcf
from app.services.modeling.comps import run_comps

# Recommended Excel writer: openpyxl or xlsxwriter
# We choose xlsxwriter for formatting flexibility
import xlsxwriter


# Formula template dictionary for Summary sheet Excel output
# Format: {cell_address: formula_string}
# All formulas reference other sheets in the workbook
SUMMARY_FORMULAS: Dict[str, str] = {
    "C3": "='Cover Sheet'!B3",
    "C5": "=(C9*D9)+(C10*D10)",
    "C6": "=(C4/C5-1)",
    "D9": "=(C13*D13)+(C14*D14)+(C15*D15)",
    "D10": "=(C18*D18)+(C19*D19)+(C20*D20)+(C21*D21)",
    "D13": "='DCF Base'!K48",
    "D14": "='DCF Bear'!K48",
    "D15": "='DCF Bull'!K48",
    "C18": "=RV!J5",
    "D18": "=RV!D13",
    "C19": "=RV!J6",
    "D19": "=RV!E13",
    "C20": "=RV!J7",
    "D20": "=RV!F13",
    "C21": "=RV!J8",
    "D21": "=RV!G13",
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


def write_summary_sheet(
    workbook,
    sheet_name: str = "Summary",
    cover_sheet_name: str = "Cover Sheet",
    dcf_base_sheet_name: str = "DCF Base",
    dcf_bear_sheet_name: str = "DCF Bear",
    dcf_bull_sheet_name: str = "DCF Bull",
    rv_sheet_name: str = "RV",
    start_row: int = 0,
    start_col: int = 0,
    custom_formulas: Optional[Dict[str, str]] = None,
) -> None:
    """
    Write summary/valuation summary sheet to Excel worksheet with formulas.
    
    Helper for excel_export.py to write the summary sheet that consolidates
    valuation results from DCF and Comps analyses.
    
    Expected usage:
        workbook = xlsxwriter.Workbook(...)
        write_summary_sheet(workbook)
    
    Args:
        workbook: xlsxwriter Workbook object
        sheet_name: Name of the Excel worksheet (default: "Summary")
        cover_sheet_name: Name of the cover sheet (default: "Cover Sheet")
        dcf_base_sheet_name: Name of the DCF Base sheet (default: "DCF Base")
        dcf_bear_sheet_name: Name of the DCF Bear sheet (default: "DCF Bear")
        dcf_bull_sheet_name: Name of the DCF Bull sheet (default: "DCF Bull")
        rv_sheet_name: Name of the relative valuation/comps sheet (default: "RV")
        start_row: Starting row for the table (0-indexed, default: 0)
        start_col: Starting column for the table (0-indexed, default: 0)
        custom_formulas: Optional dict mapping cell addresses to formula strings.
                        If provided, these formulas will be used instead of default formulas.
                        Example: {"C3": "='Cover Sheet'!B3", "C5": "=(C9*D9)+(C10*D10)"}
    
    The sheet contains:
        - Company name from Cover Sheet
        - Weighted average valuation calculations
        - DCF scenario valuations (Base, Bear, Bull)
        - Relative valuation multiples
        - Excel formulas for calculations (from SUMMARY_FORMULAS or custom_formulas)
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
    
    # Process formulas and replace sheet name placeholders if needed
    # For now, formulas use hardcoded sheet names, but we could make them dynamic
    
    # Write formulas from SUMMARY_FORMULAS dictionary
    # Convert formulas to use actual sheet names if they differ from defaults
    formulas_to_write = {}
    if custom_formulas:
        formulas_to_write = custom_formulas.copy()
    else:
        formulas_to_write = SUMMARY_FORMULAS.copy()
        
        # Replace sheet names in formulas if they differ from defaults
        if cover_sheet_name != "Cover Sheet":
            for cell, formula in formulas_to_write.items():
                formulas_to_write[cell] = formula.replace("'Cover Sheet'", f"'{cover_sheet_name}'")
        
        if dcf_base_sheet_name != "DCF Base":
            for cell, formula in formulas_to_write.items():
                formulas_to_write[cell] = formula.replace("'DCF Base'", f"'{dcf_base_sheet_name}'")
        
        if dcf_bear_sheet_name != "DCF Bear":
            for cell, formula in formulas_to_write.items():
                formulas_to_write[cell] = formula.replace("'DCF Bear'", f"'{dcf_bear_sheet_name}'")
        
        if dcf_bull_sheet_name != "DCF Bull":
            for cell, formula in formulas_to_write.items():
                formulas_to_write[cell] = formula.replace("'DCF Bull'", f"'{dcf_bull_sheet_name}'")
        
        if rv_sheet_name != "RV":
            for cell, formula in formulas_to_write.items():
                formulas_to_write[cell] = formula.replace("RV!", f"'{rv_sheet_name}'!")
    
    # Write formulas to their respective cells
    for cell_address, formula in formulas_to_write.items():
        # Parse cell address (e.g., "C3" -> row 2, col 2)
        col_letter = ''.join([c for c in cell_address if c.isalpha()])
        row_num = int(''.join([c for c in cell_address if c.isdigit()]))
        
        # Convert column letter to 0-indexed number
        col_num = 0
        for char in col_letter:
            col_num = col_num * 26 + (ord(char.upper()) - ord('A') + 1)
        col_num -= 1  # Convert to 0-indexed
        
        # Convert row number to 0-indexed
        row_num -= 1
        
        # Adjust for start_row and start_col
        actual_row = start_row + row_num
        actual_col = start_col + col_num
        
        # Write formula
        worksheet.write(actual_row, actual_col, formula, formula_format)
    
    # Set column widths for readability
    worksheet.set_column(start_col, start_col + 3, 20)  # Columns A-D


def build_excel_workbook(company_id: int,
                         model_version: Optional[str],
                         db: Session) -> bytes:
    """
    Generate and return an Excel workbook for download.

    Workflow:
        1. Run three-statement model → get projections.
        2. Run DCF → get valuation outputs.
        3. Run comps → get peer comparison outputs.
        4. Create workbook (memory-only).
        5. Write:
            - Historical tables
            - Projection tables
            - DCF valuation summary
            - Comps valuation summary
            - Inputs / assumptions for transparency
        6. Return workbook as bytes.

    TODO:
    - Design tab structure (MVP: 'Inputs', 'Projections', 'DCF', 'Comps')
    - Implement clean table formatting (headers bold, numbers comma-formatted)
    - Add company & model_version labeling to header

    Returns:
        bytes: Excel file content suitable for StreamingResponse
    """
    # Create an in-memory workbook buffer
    output = BytesIO()

    # Workbook object
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})

    # TODO: Create sheets and write data
    # sheet = workbook.add_worksheet("Inputs")
    # sheet.write(0, 0, "TODO: Populate with assumptions")

    workbook.close()
    output.seek(0)
    return output.read()
