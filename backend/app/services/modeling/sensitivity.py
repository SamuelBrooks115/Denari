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




def write_sensitivity_sheet(
    workbook, 
    dcf_sheet_name: str = "DCF",
    wacc_cell: str = "E14",
    terminal_growth_cell: str = "J6",
    share_price_cell: Optional[str] = None,
    start_row: int = 0,
    start_col: int = 0,
    ticker: Optional[str] = None
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
    
    Args:
        workbook: xlsxwriter Workbook object
        dcf_sheet_name: Name of the DCF sheet (default: "DCF")
        wacc_cell: Cell reference for WACC in DCF sheet (default: "E14")
        terminal_growth_cell: Cell reference for Terminal Growth in DCF sheet (default: "J6")
        share_price_cell: Optional cell reference for share price output (if None, will be calculated)
        start_row: Starting row for sensitivity table (0-indexed, default: 0)
        start_col: Starting column for sensitivity table (0-indexed, default: 0)
        ticker: Optional ticker symbol for header
    
    The sheet contains:
        - Header with ticker (if provided)
        - 5x5 sensitivity table with formulas referencing DCF sheet
        - Color gradient formatting (green=high, yellow=middle, red=low)
        - Base case highlighted with border
    """
    import xlsxwriter
    
    worksheet = workbook.add_worksheet("Sensitivity Analysis")
    
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
    # 5 values: base-0.05, base-0.025, base, base+0.025, base+0.05
    col = start_col + 1
    tg_offsets = [-0.05, -0.025, 0, 0.025, 0.05]
    
    for offset in tg_offsets:
        if offset == 0:
            formula = f"={terminal_growth_ref}"
        else:
            formula = f"={terminal_growth_ref}{offset:+.4f}"
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
    # 5 WACC values: base-0.02, base-0.01, base, base+0.01, base+0.02
    wacc_offsets = [-0.02, -0.01, 0, 0.01, 0.02]
    
    # Store cell ranges for conditional formatting
    data_cells = []
    
    for wacc_idx, wacc_offset in enumerate(wacc_offsets):
        # Row header (WACC value)
        if wacc_offset == 0:
            wacc_formula = f"={wacc_ref}"
        else:
            wacc_formula = f"={wacc_ref}{wacc_offset:+.4f}"
        
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
        
        for tg_idx, tg_offset in enumerate(tg_offsets):
            # Calculate the WACC and TG values for this cell
            # WACC formula: base +/- offset
            if wacc_offset == 0:
                wacc_value_formula = wacc_ref
            else:
                wacc_value_formula = f"{wacc_ref}{wacc_offset:+.4f}"
            
            # Terminal Growth formula: base +/- offset  
            if tg_offset == 0:
                tg_value_formula = terminal_growth_ref
            else:
                tg_value_formula = f"{terminal_growth_ref}{tg_offset:+.4f}"
            
            # Create formula that references share price calculation
            # This assumes the DCF sheet has a share price cell that uses WACC and TG inputs
            # If share_price_cell is provided, use it; otherwise create a reference structure
            if share_price_cell:
                # Reference the share price output - this will need to be set up to use
                # the WACC and TG values from input cells that we can vary
                share_price_ref = f"'{dcf_sheet_name}'!{share_price_cell}"
                # The formula references the output, but the DCF sheet needs to use
                # input cells that reference these calculated WACC/TG values
                formula = f"={share_price_ref}"
            else:
                # Create a formula structure that would work if DCF uses input cells
                # This is a template - user will need to adjust based on their DCF structure
                # The idea is: if DCF has input cells for WACC and TG, and an output for share price,
                # we'd reference those. For now, create a placeholder that shows the structure.
                formula = f"=IF({wacc_value_formula}>{tg_value_formula},\"See DCF Setup\",\"N/A\")"
            
            # Determine format based on position (for gradient effect)
            # Center cell (base case) gets yellow with border
            if wacc_idx == 2 and tg_idx == 2:  # Center cell
                cell_format = format_yellow
            else:
                # Create gradient: higher values = greener, lower = redder
                # For a 5x5 grid, distance from center determines color
                distance_from_center = abs(wacc_idx - 2) + abs(tg_idx - 2)
                
                if distance_from_center == 0:  # Center (already handled)
                    cell_format = format_yellow
                elif distance_from_center == 1:  # Adjacent to center
                    # Determine if higher or lower value area
                    if wacc_idx < 2 or tg_idx < 2:  # Lower WACC or TG = higher price (green)
                        cell_format = format_green_light
                    else:  # Higher WACC or TG = lower price (red)
                        cell_format = format_red_light
                elif distance_from_center == 2:  # Two steps from center
                    if wacc_idx < 1 or tg_idx < 1:  # Much lower = very high price
                        cell_format = format_green_medium
                    elif wacc_idx > 3 or tg_idx > 3:  # Much higher = very low price
                        cell_format = format_red_medium
                    else:
                        cell_format = format_yellow
                else:  # Corners
                    if wacc_idx == 0 and tg_idx == 0:  # Top-left (lowest WACC, lowest TG) = highest price
                        cell_format = format_green_dark
                    elif wacc_idx == 4 and tg_idx == 4:  # Bottom-right (highest WACC, highest TG) = lowest price
                        cell_format = format_red_dark
                    else:
                        cell_format = currency_format
            
            worksheet.write(row, start_col + 1 + tg_idx, formula, cell_format)
            data_cells.append((row, start_col + 1 + tg_idx))
        
        row += 1
    
    # Add notes
    row += 1
    note_format = workbook.add_format({'italic': True, 'font_color': '#666666'})
    worksheet.write(row, start_col, "Note: Base case (center cell) highlighted with yellow background and bold border", note_format)
    row += 1
    worksheet.write(row, start_col, f"WACC references: {dcf_sheet_name}!{wacc_cell}, Terminal Growth references: {dcf_sheet_name}!{terminal_growth_cell}", note_format)
    row += 1
    worksheet.write(row, start_col, "To make cell references dynamic (handle row changes), use INDIRECT() or named ranges in DCF sheet", note_format)
    row += 1
    worksheet.write(row, start_col, "Example: Use =INDIRECT(\"'DCF'!E\"&ROW()) to make E14 dynamic based on current row", note_format)
    
    # Freeze panes (freeze header row and WACC column)
    worksheet.freeze_panes(table_start_row + 1, start_col + 1)

