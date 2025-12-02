"""
excel_export.py — Excel Workbook Export Builder

Purpose:
- Convert model outputs (projections, DCF, comps) into a structured .xlsx file.
- Populate Excel template with historical financial data from structured JSON.
- This is the final client-facing artifact used by analysts and investors.
- Template-driven approach to ensure readability and familiarity.

Inputs:
- company_id
- model_version (optional)
- DB session (for historicals + assumptions)
- Structured JSON files (for template population)
- Must call:
    run_three_statement()
    run_dcf()
    run_comps()
  to gather values prior to export.

Outputs:
- In-memory .xlsx file (returned as bytes or BytesIO stream).
- Populated Excel template with historical data.

This module does NOT:
- Perform valuation logic.
- Fetch filings or prices.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from io import BytesIO
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.services.modeling.three_statement import run_three_statement
from app.services.modeling.dcf import run_dcf
from app.services.modeling.comps import run_comps
from app.services.modeling.types import (
    CompanyModelInput,
    build_company_model_input,
    HistoricalSeries,
    DcfOutput,
)

# Use openpyxl for reading/modifying existing Excel files
# Use xlsxwriter for creating new workbooks
try:
    import openpyxl
    from openpyxl import Workbook, load_workbook
    from openpyxl.utils import get_column_letter, column_index_from_string
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

import xlsxwriter

logger = get_logger(__name__)

# Model role to row label mappings for Excel template
# Maps row labels (from column B) to model_role values
# Order matters: more specific patterns should come first
ROW_LABEL_TO_MODEL_ROLE: Dict[str, str] = {
    # Revenue
    "revenue": "IS_REVENUE",
    "sales": "IS_REVENUE",
    "net sales": "IS_REVENUE",
    "total revenue": "IS_REVENUE",
    
    # COGS - match patterns with parentheses and dashes first
    "(-) cogs": "IS_COGS",
    "cogs": "IS_COGS",
    "cost of goods sold": "IS_COGS",
    "cost of goods": "IS_COGS",
    "cost of sales": "IS_COGS",
    
    # Operating Expenses
    "(-) op ex": "IS_OPERATING_EXPENSE",
    "(-) operating expenses": "IS_OPERATING_EXPENSE",
    "(-) opex": "IS_OPERATING_EXPENSE",
    "op ex": "IS_OPERATING_EXPENSE",
    "operating expenses": "IS_OPERATING_EXPENSE",
    "opex": "IS_OPERATING_EXPENSE",
    "operating expense": "IS_OPERATING_EXPENSE",
    "sg&a": "IS_OPERATING_EXPENSE",
    "selling, general and administrative": "IS_OPERATING_EXPENSE",
    
    # Depreciation & Amortization
    "(+) d&a": "CF_DEPRECIATION",
    "(+) depreciation": "CF_DEPRECIATION",
    "(+) depreciation & amortization": "CF_DEPRECIATION",
    "d&a": "CF_DEPRECIATION",
    "depreciation & amortization": "CF_DEPRECIATION",
    "depreciation and amortization": "CF_DEPRECIATION",
    
    # Capital Expenditures
    "(-) capex": "CF_CAPEX",
    "(-) capital expenditures": "CF_CAPEX",
    "capex": "CF_CAPEX",
    "capital expenditures": "CF_CAPEX",
    "capital expense": "CF_CAPEX",
    
    # Changes in Working Capital
    "(-) changes in wc": "CF_CHANGE_IN_WORKING_CAPITAL",
    "(-) change in wc": "CF_CHANGE_IN_WORKING_CAPITAL",
    "(-) changes in working capital": "CF_CHANGE_IN_WORKING_CAPITAL",
    "(-) change in working capital": "CF_CHANGE_IN_WORKING_CAPITAL",
    "changes in wc": "CF_CHANGE_IN_WORKING_CAPITAL",
    "change in wc": "CF_CHANGE_IN_WORKING_CAPITAL",
    "changes in working capital": "CF_CHANGE_IN_WORKING_CAPITAL",
    "change in working capital": "CF_CHANGE_IN_WORKING_CAPITAL",
    
    # Income Statement items
    "net income": "IS_NET_INCOME",
    "ebit": "IS_EBIT",
    "ebitda": "IS_EBITDA",
    "nopat": "IS_NOPAT",
    
    # Balance Sheet items
    "cash": "BS_CASH",
    "cash & equivalents": "BS_CASH",
    "cash and equivalents": "BS_CASH",
    "pp&e": "BS_PP_AND_E",
    "property, plant and equipment": "BS_PP_AND_E",
    "ppe": "BS_PP_AND_E",
    "inventory": "BS_INVENTORY",
    "accounts receivable": "BS_ACCOUNTS_RECEIVABLE",
    "ar": "BS_ACCOUNTS_RECEIVABLE",
    "accounts payable": "BS_ACCOUNTS_PAYABLE",
    "ap": "BS_ACCOUNTS_PAYABLE",
    "accrued expenses": "BS_ACCRUED_LIABILITIES",
    "accrued liabilities": "BS_ACCRUED_LIABILITIES",
    "total debt": "BS_DEBT_CURRENT",
    "debt": "BS_DEBT_CURRENT",
    
    # Cash Flow items
    "share repurchases": "CF_SHARE_REPURCHASES",
    "share buybacks": "CF_SHARE_REPURCHASES",
    "dividends paid": "CF_DIVIDENDS_PAID",
    "dividends": "CF_DIVIDENDS_PAID",
    "debt issued": "CF_DEBT_ISSUANCE",
    "debt repaid": "CF_DEBT_REPAYMENT",
}


def load_structured_json(path: str) -> Dict[str, Any]:
    """
    Load structured JSON file containing financial data.
    
    Args:
        path: Path to JSON file
        
    Returns:
        Dictionary containing structured financial data
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_line_items_from_json(json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract all line_items from all filings and all statements.
    
    Handles both single-year and multi-year JSON formats:
    - Multi-year: {"filings": [{"statements": {...}}]}
    - Single-year: {"statements": {...}}
    
    Args:
        json_data: Loaded JSON data
        
    Returns:
        Flattened list of all line items from all statements
    """
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
    
    return line_items


def build_role_year_matrix(line_items: List[Dict[str, Any]]) -> Dict[str, Dict[int, float]]:
    """
    Build a matrix aggregating values by model_role and year.
    
    Multiple items with the same model_role for a given year are summed.
    
    Args:
        line_items: List of line item dictionaries from JSON
        
    Returns:
        Dictionary mapping model_role -> year -> aggregated_value
        Example: {"IS_REVENUE": {2022: 100.0, 2023: 110.0}}
    """
    matrix: Dict[str, Dict[int, float]] = defaultdict(lambda: defaultdict(float))
    
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
                matrix[role][year] += val
            except (ValueError, IndexError, TypeError) as e:
                logger.warning(f"Failed to parse period '{period_str}' or value '{raw_val}': {e}")
                continue
    
    return dict(matrix)


def load_excel_template(template_path: str) -> Workbook:
    """
    Load existing Excel template file.
    
    Args:
        template_path: Path to .xlsx template file
        
    Returns:
        openpyxl Workbook object
    """
    if not OPENPYXL_AVAILABLE:
        raise ImportError("openpyxl is required for reading Excel templates. Install with: pip install openpyxl")
    
    return load_workbook(template_path)


def find_revenue_row(worksheet) -> Optional[int]:
    """
    Find the row containing "Revenue" label in column B.
    Searches for various revenue-related terms.
    
    Args:
        worksheet: openpyxl Worksheet object
        
    Returns:
        Row number (1-indexed) if found, None otherwise
    """
    # Search column B (index 2) for revenue label
    revenue_keywords = ["revenue", "sales", "net sales", "total revenue", "total sales"]
    
    for row_idx, row in enumerate(worksheet.iter_rows(min_col=2, max_col=2, values_only=False), start=1):
        cell = row[0]
        if cell.value:
            cell_value = str(cell.value).strip().lower()
            # Check for any revenue keyword
            for keyword in revenue_keywords:
                if keyword in cell_value:
                    return row_idx
    return None


def detect_historical_columns(worksheet) -> List[int]:
    """
    Detect historical columns by searching for "Year" headers in row 16.
    Looks for patterns like "Year 'A'", "Year 'E'", "Year A", etc.
    These headers will be overwritten with actual years later.
    
    Args:
        worksheet: openpyxl Worksheet object
        
    Returns:
        List of column indices (1-indexed) containing "Year" headers, sorted left to right
    """
    hist_columns: List[int] = []
    header_row = 16
    
    # Search row 16 for "Year" headers (case-insensitive)
    # Look in columns D through K (4-11) for historical columns
    for col_idx in range(4, 12):  # Columns D through K
        cell = worksheet.cell(row=header_row, column=col_idx)
        cell_value = str(cell.value or "").strip()
        cell_lower = cell_value.lower()
        
        # Check if cell contains "year" - be flexible with patterns
        # Matches: "Year 'A'", "Year 'E'", "Year A", "Year E", "Year\"A\"", etc.
        if "year" in cell_lower:
            # Check for various patterns: Year 'A', Year 'E', Year A, Year E, Year"A", etc.
            if any(pattern in cell_lower for pattern in ["'a'", "'e'", " a", " e", "\"a\"", "\"e\""]) or len(cell_lower) < 10:
                hist_columns.append(col_idx)
    
    # If no "Year" headers found, fallback to hardcoded D, E, F
    if not hist_columns:
        logger.warning("No 'Year' headers found in row 16, using default columns D, E, F")
        return [4, 5, 6]
    
    # Sort columns left to right
    hist_columns.sort()
    logger.debug(f"Detected historical columns: {hist_columns}")
    return hist_columns


def map_years_to_columns(years: List[int], hist_columns: List[int]) -> Dict[int, int]:
    """
    Map sorted years to historical columns from left to right.
    Hardcapped at 3 most recent years.
    
    Args:
        years: List of years from JSON data
        hist_columns: List of column indices containing "Year"A" headers (sorted left to right)
        
    Returns:
        Dictionary mapping year -> column_index
    """
    sorted_years = sorted(years)
    
    # Hardcap at 3 most recent years
    recent_years = sorted_years[-3:] if len(sorted_years) > 3 else sorted_years
    
    year_column_map: Dict[int, int] = {}
    
    # Map oldest year to leftmost column, newest to rightmost
    # Only use up to 3 columns (hardcap)
    max_columns = min(3, len(hist_columns))
    for idx, year in enumerate(recent_years):
        if idx < max_columns:
            year_column_map[year] = hist_columns[idx]
    
    return year_column_map


def write_year_headers(worksheet, year_column_map: Dict[int, int], header_row: int = 16) -> None:
    """
    Write actual year values to header row (row 16 by default).
    
    Args:
        worksheet: openpyxl Worksheet object
        year_column_map: Dictionary mapping year -> column_index
        header_row: Row number where years should be written (default 16)
    """
    # Sort years to write them in order (oldest to newest)
    sorted_years = sorted(year_column_map.keys())
    
    for year in sorted_years:
        column_idx = year_column_map[year]
        cell = worksheet.cell(row=header_row, column=column_idx)
        cell.value = year


def overwrite_year_headers_in_statement_section(
    worksheet,
    statement_name: str,
    year_column_map: Dict[int, int],
    section_start_row: Optional[int] = None
) -> None:
    """
    Find and overwrite "Year 'A'" headers in a statement section header row.
    Works for Income Statement, Balance Sheet, and Cash Flow Statement.
    
    This function:
    1. Finds the statement section start row (if not provided)
    2. Searches for "Year" headers in the header row(s) of that section
    3. Overwrites them with actual years from year_column_map
    
    Args:
        worksheet: openpyxl Worksheet object
        statement_name: Name of the statement ("Income Statement", "Balance Sheet", or "Cash Flow Statement")
        year_column_map: Dictionary mapping year -> column_index
        section_start_row: Optional starting row of the statement section (if None, will search for it)
    """
    # Find section start if not provided
    if section_start_row is None:
        section_start_row = find_statement_section_start(worksheet, statement_name)
    
    if not section_start_row:
        logger.warning(f"Could not find '{statement_name}' section start, skipping year header overwrite")
        return
    
    # Search for "Year" headers in rows near the section start (typically 0-3 rows after section start)
    # This covers the header row that contains "Year 'A'" placeholders
    for row_offset in range(0, 4):
        check_row = section_start_row + row_offset
        if check_row > worksheet.max_row:
            break
        
        # Check columns D-F (4-6) for "Year" headers
        year_header_found = False
        for col_idx in range(4, 7):  # Columns D, E, F
            cell = worksheet.cell(row=check_row, column=col_idx)
            cell_value = str(cell.value or "").strip()
            
            if "year" in cell_value.lower():
                year_header_found = True
                # Overwrite with actual year if this column is mapped
                if col_idx in year_column_map.values():
                    # Find which year maps to this column
                    for year, mapped_col in year_column_map.items():
                        if mapped_col == col_idx:
                            cell.value = year
                            logger.info(f"Overwrote '{cell_value}' with {year} in {statement_name} row {check_row}, column {col_idx}")
                            break
        
        # If we found year headers in this row, we're done (don't need to check further rows)
        if year_header_found:
            break


def add_model_role_column(worksheet, role_column: str = "ZZ") -> None:
    """
    Add hidden model_role column to worksheet.
    
    Maps row labels to model_role values and writes them in the specified column.
    Hides the column for clean appearance.
    
    Args:
        worksheet: openpyxl Worksheet object
        role_column: Column letter (default "ZZ") where model_role will be stored
    """
    col_idx = column_index_from_string(role_column)
    
    # Write header
    header_cell = worksheet.cell(row=1, column=col_idx)
    header_cell.value = "model_role"
    
    # Find rows with known labels and map to model roles
    # Search column B (index 2) for row labels
    for row_idx, row in enumerate(worksheet.iter_rows(min_col=2, max_col=2, values_only=False), start=1):
        cell = row[0]
        if cell.value:
            cell_value = str(cell.value).strip().lower()
            
            # Check if this label maps to a model role
            for label_pattern, model_role in ROW_LABEL_TO_MODEL_ROLE.items():
                if label_pattern in cell_value:
                    role_cell = worksheet.cell(row=row_idx, column=col_idx)
                    role_cell.value = model_role
                    break
    
    # Hide the column
    worksheet.column_dimensions[role_column].hidden = True


def populate_historicals(
    worksheet,
    role_column: str,
    matrix: Dict[str, Dict[int, float]],
    year_column_map: Dict[int, int]
) -> None:
    """
    Populate historical data in worksheet using model_role column for row matching.
    Skips rows with "%" in the label (these are calculated, not filled).
    
    Args:
        worksheet: openpyxl Worksheet object
        role_column: Column letter containing model_role values
        matrix: Role/year matrix from build_role_year_matrix()
        year_column_map: Dictionary mapping year -> column_index
    """
    col_idx = column_index_from_string(role_column)
    
    # Iterate through all rows
    for row_idx, row in enumerate(worksheet.iter_rows(min_col=col_idx, max_col=col_idx, values_only=False), start=1):
        role_cell = row[0]
        model_role = (role_cell.value or "").strip()
        
        if not model_role:
            continue
        
        # Skip rows with "%" in the label (these are calculated, not filled)
        # Check the row label in column B
        label_cell = worksheet.cell(row=row_idx, column=2)
        label_value = str(label_cell.value or "").strip()
        if "%" in label_value:
            continue
        
        # Look up values for this model_role
        role_values = matrix.get(model_role, {})
        
        if not role_values:
            continue
        
        # Write values to historical columns
        for year, column_idx in year_column_map.items():
            if year in role_values:
                value = role_values[year]
                target_cell = worksheet.cell(row=row_idx, column=column_idx)
                target_cell.value = value


def populate_cover_sheet(
    workbook,
    company_name: str,
    ticker: str,
    date: Optional[str] = None
) -> None:
    """
    Populate cover sheet with company information.
    
    Writes:
    - Company name to B3
    - Ticker to B4
    - Date to B5 (defaults to current date if not provided)
    
    Args:
        workbook: openpyxl Workbook object
        company_name: Company name to write
        ticker: Ticker symbol to write
        date: Optional date string (defaults to current date in MM/DD/YYYY format)
    """
    # Find cover sheet - common names: "Cover", "Cover Sheet", "Summary", or first sheet
    cover_sheet = None
    cover_sheet_names = ["Cover", "Cover Sheet", "Summary", "Cover Page"]
    
    for sheet_name in cover_sheet_names:
        if sheet_name in workbook.sheetnames:
            cover_sheet = workbook[sheet_name]
            break
    
    # If no cover sheet found, try the first sheet
    if cover_sheet is None and workbook.sheetnames:
        cover_sheet = workbook[workbook.sheetnames[0]]
        logger.warning(f"No cover sheet found with standard names, using first sheet: {workbook.sheetnames[0]}")
    
    if cover_sheet is None:
        logger.warning("No sheets found in workbook, skipping cover sheet population")
        return
    
    # Write company name to B3 (row 3, column 2)
    cover_sheet.cell(row=3, column=2).value = company_name
    
    # Write ticker to B4 (row 4, column 2)
    cover_sheet.cell(row=4, column=2).value = ticker
    
    # Write date to B5 (row 5, column 2)
    if date is None:
        date = datetime.now().strftime("%m/%d/%Y")
    cover_sheet.cell(row=5, column=2).value = date
    
    logger.info(f"Populated cover sheet: Company={company_name}, Ticker={ticker}, Date={date}")


def populate_three_statement_assumptions(
    worksheet,
    assumptions: Dict[str, Any],
    forecast_periods: int = 5
) -> None:
    """
    Populate 3-statement model assumptions in Excel worksheet.
    
    Supports three forecast methods:
    - "step": Step increase/decrease per period (value written to O column)
    - "constant": Constant value for all periods (value written to O, P, Q, R, S)
    - "custom": Custom values for each period (5 values written to O, P, Q, R, S)
    
    Args:
        worksheet: openpyxl Worksheet object for "3-STMT A" sheet
        assumptions: Dictionary with structure:
            {
                "income_statement": {
                    "revenue": {"type": "step", "value": 0.08},
                    ...
                },
                "balance_sheet": {...},
                "cash_flow": {...}
            }
        forecast_periods: Number of forecast periods (default 5)
    """
    # Find assumption section headers dynamically
    # Search for headers in column L (12) containing "Assumptions"
    is_assumptions_row = None
    bs_assumptions_row = None
    cf_assumptions_row = None
    
    for row in range(1, 200):
        cell_value = worksheet.cell(row=row, column=12).value  # Column L
        if cell_value:
            cell_str = str(cell_value).lower().strip()
            if "is assumptions" in cell_str or (is_assumptions_row is None and "assumptions" in cell_str and "income" in cell_str):
                is_assumptions_row = row
            elif "bs assumptions" in cell_str or (bs_assumptions_row is None and "assumptions" in cell_str and "balance" in cell_str):
                bs_assumptions_row = row
            elif "cf assumptions" in cell_str or (cf_assumptions_row is None and "assumptions" in cell_str and "cash" in cell_str):
                cf_assumptions_row = row
    
    # Fallback to hardcoded rows if headers not found
    if is_assumptions_row is None:
        is_assumptions_row = 4
        logger.warning("Could not find IS Assumptions header, using row 4")
    if bs_assumptions_row is None:
        bs_assumptions_row = 21
        logger.warning("Could not find BS Assumptions header, using row 21")
    if cf_assumptions_row is None:
        cf_assumptions_row = 51
        logger.warning("Could not find CF Assumptions header, using row 51")
    
    # Mapping of assumption names to their row offsets from section headers
    # Column N = 14 (Type), Column O = 15 (Value start), P=16, Q=17, R=18, S=19
    assumption_mapping = {
        "income_statement": {
            "revenue": {"row_offset": 1},  # IS header + 1 = row 5
            "gross_margin": {"row_offset": 2},  # IS header + 2 = row 6
            "operating_cost": {"row_offset": 3},  # IS header + 3 = row 7
            "ebitda_margin": {"row_offset": 4},  # IS header + 4 = row 8
            "tax_rate": {"row_offset": 5},  # IS header + 5 = row 9
            "interest_rate_on_debt": {"row_offset": 6},  # IS header + 6 = row 10
        },
        "balance_sheet": {
            "depreciation_pct_of_ppe": {"row_offset": 1},  # BS header + 1 = row 22
            "inventory": {"row_offset": 2},  # BS header + 2 = row 23
            "total_debt_amount": {"row_offset": 3},  # BS header + 3 = row 24
        },
        "cash_flow": {
            "share_repurchase": {"row_offset": 1},  # CF header + 1 = row 52
            "dividend_pct_of_net_income": {"row_offset": 2},  # CF header + 2 = row 53
            "capex": {"row_offset": 3},  # CF header + 3 = row 54
        },
    }
    
    # Column indices: N=14 (Type), O=15, P=16, Q=17, R=18, S=19
    TYPE_COLUMN = 14
    VALUE_START_COLUMN = 15
    
    # Process each statement type
    for statement_type, statement_assumptions in assumptions.items():
        if statement_type not in assumption_mapping:
            logger.warning(f"Unknown statement type: {statement_type}")
            continue
        
        # Get the section header row for this statement type
        if statement_type == "income_statement":
            section_header_row = is_assumptions_row
        elif statement_type == "balance_sheet":
            section_header_row = bs_assumptions_row
        elif statement_type == "cash_flow":
            section_header_row = cf_assumptions_row
        else:
            logger.warning(f"Unknown statement type: {statement_type}")
            continue
        
        mapping = assumption_mapping[statement_type]
        
        # Process each assumption
        for assumption_name, assumption_data in statement_assumptions.items():
            if assumption_name not in mapping:
                logger.warning(f"Unknown assumption '{assumption_name}' for {statement_type}")
                continue
            
            # Calculate absolute row from section header + offset
            row_offset = mapping[assumption_name]["row_offset"]
            row = section_header_row + row_offset
            assumption_type = assumption_data.get("type", "").lower()
            value = assumption_data.get("value")
            
            if not assumption_type:
                logger.warning(f"Missing type for assumption '{assumption_name}'")
                continue
            
            # Write type to column N
            type_cell = worksheet.cell(row=row, column=TYPE_COLUMN)
            type_cell.value = assumption_type
            
            # Handle different types
            if assumption_type == "step":
                # Step type: write value to O column only
                if value is not None:
                    value_cell = worksheet.cell(row=row, column=VALUE_START_COLUMN)
                    value_cell.value = value
                    # Set number format to prevent date interpretation
                    # Use General format for numbers, or percentage format if value is < 1
                    if isinstance(value, (int, float)):
                        if abs(value) < 1 and value != 0:
                            value_cell.number_format = "0.00%"
                        else:
                            value_cell.number_format = "General"
                    logger.debug(f"Wrote step assumption '{assumption_name}': {value} to row {row}, column {VALUE_START_COLUMN}")
            
            elif assumption_type == "constant":
                # Constant type: write value to all period columns (O, P, Q, R, S)
                if value is not None:
                    for period_idx in range(forecast_periods):
                        col = VALUE_START_COLUMN + period_idx
                        value_cell = worksheet.cell(row=row, column=col)
                        value_cell.value = value
                        # Set number format to prevent date interpretation
                        if isinstance(value, (int, float)):
                            if abs(value) < 1 and value != 0:
                                value_cell.number_format = "0.00%"
                            else:
                                value_cell.number_format = "General"
                    logger.debug(f"Wrote constant assumption '{assumption_name}': {value} to row {row}, columns {VALUE_START_COLUMN}-{VALUE_START_COLUMN + forecast_periods - 1}")
            
            elif assumption_type == "custom":
                # Custom type: write array of values to O, P, Q, R, S
                if isinstance(value, list) and len(value) == forecast_periods:
                    for period_idx, period_value in enumerate(value):
                        col = VALUE_START_COLUMN + period_idx
                        value_cell = worksheet.cell(row=row, column=col)
                        value_cell.value = period_value
                        # Set number format to prevent date interpretation
                        if isinstance(period_value, (int, float)):
                            if abs(period_value) < 1 and period_value != 0:
                                value_cell.number_format = "0.00%"
                            else:
                                value_cell.number_format = "General"
                    logger.debug(f"Wrote custom assumption '{assumption_name}': {value} to row {row}, columns {VALUE_START_COLUMN}-{VALUE_START_COLUMN + forecast_periods - 1}")
                else:
                    logger.warning(f"Custom assumption '{assumption_name}' must have {forecast_periods} values, got {len(value) if isinstance(value, list) else 'non-list'}")
            
            else:
                logger.warning(f"Unknown assumption type '{assumption_type}' for '{assumption_name}'")
    
    logger.info("Populated 3-statement assumptions")


# Statement structure definitions for dynamic line item insertion
STATEMENT_STRUCTURE = {
    "income_statement": {
        "section_name": "Income Statement",
        "anchors": [
            "gross income",
            "gross margin %",
            "operating income",
            "operating margin %",
            "income before taxes",
            "income tax expense",
            "net income",
            "net income margin %",
            "eps",
        ],
        "placeholder_text": "line item",
    },
    "balance_sheet": {
        "section_name": "Balance Sheet",
        "subsections": {
            "assets": {
                "header": "assets",
                "anchors": [
                    "total current assets",
                    "total assets",
                ],
                "placeholder_text": "line item",
            },
            "liabilities": {
                "header": "liabilities",
                "anchors": [
                    "total current liabilities",
                    "total liabilities",
                ],
                "placeholder_text": "line item",
            },
            "equity": {
                "header": "equity",
                "anchors": [
                    "total equity",
                    "total liabilities and equity",
                ],
                "placeholder_text": "line item",
            },
        },
    },
    "cash_flow": {
        "section_name": "Cash Flow Statement",
        "subsections": {
            "operating": {
                "header": "cash flows from operating activities",
                "anchors": [
                    "net cash provided by/(used in) operating activities",
                ],
                "placeholder_text": "line item",
            },
            "investing": {
                "header": "cash flows from investing activities",
                "anchors": [
                    "net cash provided by/(used in) investing activities",
                ],
                "placeholder_text": "line item",
            },
            "financing": {
                "header": "cash flows from financing activities",
                "anchors": [
                    "net cash provided by/(used in) financing activities",
                ],
                "placeholder_text": "line item",
            },
        },
        "final_items": [
            "effects of exchange rate",
            "net increase/(decrease) in cash, cash equivalents, and restricted cash",
            "cash, cash equivalents, and restricted cash at beginning of period",
            "net increase/(decrease) in cash, cash equivalents, and restricted cash",
            "cash, cash equivalents, and restricted cash at end of period",
        ],
    },
}


# Helper functions for dynamic line item insertion
def find_statement_section_start(worksheet, section_name: str, start_row: int = 1, max_row: int = 200) -> Optional[int]:
    """
    Find the starting row of a statement section by searching for the section name in column B.
    
    Args:
        worksheet: openpyxl Worksheet object
        section_name: Name of the section to find (e.g., "Income Statement")
        start_row: Row to start searching from
        max_row: Maximum row to search to
        
    Returns:
        Row number if found, None otherwise
    """
    section_name_lower = section_name.lower()
    for row_idx in range(start_row, min(max_row + 1, worksheet.max_row + 1)):
        cell = worksheet.cell(row=row_idx, column=2)  # Column B
        cell_value = str(cell.value or "").strip().lower()
        if section_name_lower in cell_value:
            return row_idx
    return None


def find_anchor_rows(worksheet, anchors: List[str], start_row: int, end_row: int) -> Dict[str, int]:
    """
    Find anchor rows within a specified range.
    
    Args:
        worksheet: openpyxl Worksheet object
        anchors: List of anchor text to search for (case-insensitive)
        start_row: Starting row to search
        end_row: Ending row to search
        
    Returns:
        Dictionary mapping anchor text (lowercase) to row number
    """
    anchor_map: Dict[str, int] = {}
    anchors_lower = [anchor.lower() for anchor in anchors]
    
    for row_idx in range(start_row, min(end_row + 1, worksheet.max_row + 1)):
        cell = worksheet.cell(row=row_idx, column=2)  # Column B
        cell_value = str(cell.value or "").strip().lower()
        
        for anchor in anchors_lower:
            if anchor in cell_value and anchor not in anchor_map:
                anchor_map[anchor] = row_idx
    
    return anchor_map


def find_line_item_placeholders(worksheet, placeholder_text: str, start_row: int, end_row: int, exclude_anchors: Optional[List[str]] = None) -> List[int]:
    """
    Find rows containing placeholder text in column B.
    Excludes anchor rows (like "Total Current Assets", "Total Current Liabilities", etc.)
    
    Args:
        worksheet: openpyxl Worksheet object
        placeholder_text: Text to search for (e.g., "Line Item")
        start_row: Starting row to search
        end_row: Ending row to search
        exclude_anchors: Optional list of anchor text to exclude from results
        
    Returns:
        List of row numbers containing the placeholder (excluding anchor rows)
    """
    placeholder_lower = placeholder_text.lower()
    placeholder_rows: List[int] = []
    
    # Common anchor patterns to exclude (Balance Sheet terms that shouldn't appear in Cash Flow)
    default_exclude = [
        "total current assets",
        "total assets",
        "total current liabilities",
        "total liabilities",
        "total equity",
        "total liabilities and equity"
    ]
    
    exclude_patterns = (exclude_anchors or []) + default_exclude
    exclude_lower = [pattern.lower() for pattern in exclude_patterns]
    
    for row_idx in range(start_row, min(end_row + 1, worksheet.max_row + 1)):
        cell = worksheet.cell(row=row_idx, column=2)  # Column B
        cell_value = str(cell.value or "").strip().lower()
        
        # Skip if this is an anchor row
        is_anchor = False
        for exclude_pattern in exclude_lower:
            if exclude_pattern in cell_value:
                is_anchor = True
                break
        
        if not is_anchor and placeholder_lower in cell_value:
            placeholder_rows.append(row_idx)
    
    return placeholder_rows


def preserve_assumptions_on_row_insert(worksheet, insert_row: int, num_rows: int = 1) -> None:
    """
    When inserting rows, preserve assumptions columns (L-O) by copying from row above.
    
    Args:
        worksheet: openpyxl Worksheet object
        insert_row: Row number where rows will be inserted
        num_rows: Number of rows to insert
    """
    # Assumptions columns: L=12, M=13, N=14, O=15
    assumptions_columns = [12, 13, 14, 15]
    
    # Copy assumptions from the row above the insertion point
    source_row = insert_row - 1
    
    if source_row < 1:
        return  # No row above to copy from
    
    # Copy to each inserted row
    for row_offset in range(num_rows):
        target_row = insert_row + row_offset
        for col in assumptions_columns:
            source_cell = worksheet.cell(row=source_row, column=col)
            target_cell = worksheet.cell(row=target_row, column=col)
            
            # Copy value
            target_cell.value = source_cell.value
            
            # Copy number format (this is safe and important)
            if source_cell.has_style:
                target_cell.number_format = source_cell.number_format
                
            # Note: We don't copy font, fill, border, alignment directly as StyleProxy objects
            # are not hashable. The template formatting should handle visual styling.
            # If specific formatting is needed, it can be applied via template or
            # by copying the style ID: target_cell._style = source_cell._style.copy()


def group_line_items_by_statement(line_items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group line items by statement type based on model_role prefix.
    
    Args:
        line_items: List of line item dictionaries from JSON
        
    Returns:
        Dictionary with keys: "income_statement", "balance_sheet", "cash_flow"
        Each value is a list of line items for that statement type
    """
    grouped: Dict[str, List[Dict[str, Any]]] = {
        "income_statement": [],
        "balance_sheet": [],
        "cash_flow": [],
    }
    
    for item in line_items:
        model_role = (item.get("model_role") or "").strip()
        
        if model_role.startswith("IS_"):
            grouped["income_statement"].append(item)
        elif model_role.startswith("BS_"):
            grouped["balance_sheet"].append(item)
        elif model_role.startswith("CF_"):
            grouped["cash_flow"].append(item)
    
    return grouped


def replace_line_item_placeholders(
    worksheet,
    placeholder_rows: List[int],
    line_items: List[Dict[str, Any]],
    matrix: Dict[str, Dict[int, float]],
    year_column_map: Dict[int, int]
) -> None:
    """
    Replace "Line Item" placeholders with actual line item data.
    Overwrites existing placeholder rows instead of inserting new ones.
    Only inserts additional rows if there are more line items than placeholders.
    
    IMPORTANT: Never writes to row 16 (year headers) or assumptions rows.
    
    Args:
        worksheet: openpyxl Worksheet object
        placeholder_rows: List of row numbers containing "Line Item" placeholders
        line_items: List of line items to populate
        matrix: Role/year matrix from build_role_year_matrix()
        year_column_map: Dictionary mapping year -> column_index
    """
    # Filter out row 16 (year headers) - never overwrite year headers
    placeholder_rows = [row for row in placeholder_rows if row != 16]
    
    if not placeholder_rows:
        logger.warning("No valid placeholder rows found (excluding row 16)")
        return
    
    # Replace placeholders one-to-one with line items
    num_replacements = min(len(placeholder_rows), len(line_items))
    
    for idx in range(num_replacements):
        row = placeholder_rows[idx]
        item = line_items[idx]
        model_role = (item.get("model_role") or "").strip()
        label = item.get("label", "").strip()
        
        # Overwrite placeholder text with actual label
        label_cell = worksheet.cell(row=row, column=2)
        label_cell.value = label
        
        # Write model_role to role column (ZZ) for later reference
        role_cell = worksheet.cell(row=row, column=column_index_from_string("ZZ"))
        role_cell.value = model_role
        
        # Write historical values (only to data columns D, E, F - not year header row)
        role_values = matrix.get(model_role, {})
        for year, column_idx in year_column_map.items():
            if year in role_values:
                value = role_values[year]
                target_cell = worksheet.cell(row=row, column=column_idx)
                target_cell.value = value
                target_cell.number_format = "General"
    
    # If there are more line items than placeholders, insert rows ONLY in data columns (A-K)
    # This prevents assumptions columns (L-O) from being shifted
    if len(line_items) > len(placeholder_rows):
        extra_items = line_items[num_replacements:]
        insert_after_row = placeholder_rows[-1] if placeholder_rows else None
        
        if insert_after_row:
            # Insert rows only affecting columns A-K (data columns)
            # We'll manually copy cells to avoid shifting assumptions
            num_extra = len(extra_items)
            
            # Insert rows (this will shift everything, but we'll fix assumptions)
            worksheet.insert_rows(insert_after_row + 1, num_extra)
            
            # Restore assumptions columns from their original positions
            # Assumptions should NOT move - they're anchored to their section headers
            # So we need to copy assumptions back from where they should be
            # For now, copy from the row above the insertion point
            preserve_assumptions_on_row_insert(worksheet, insert_after_row + 1, num_extra)
            
            # Populate the extra inserted rows
            for idx, item in enumerate(extra_items):
                row = insert_after_row + 1 + idx
                model_role = (item.get("model_role") or "").strip()
                label = item.get("label", "").strip()
                
                # Write label to column B
                label_cell = worksheet.cell(row=row, column=2)
                label_cell.value = label
                
                # Write model_role to role column (ZZ)
                role_cell = worksheet.cell(row=row, column=column_index_from_string("ZZ"))
                role_cell.value = model_role
                
                # Write historical values
                role_values = matrix.get(model_role, {})
                for year, column_idx in year_column_map.items():
                    if year in role_values:
                        value = role_values[year]
                        target_cell = worksheet.cell(row=row, column=column_idx)
                        target_cell.value = value
                        target_cell.number_format = "General"


def populate_income_statement_line_items(
    worksheet,
    line_items: List[Dict[str, Any]],
    matrix: Dict[str, Dict[int, float]],
    year_column_map: Dict[int, int],
    section_start_row: int
) -> None:
    """
    Populate Income Statement with dynamic line items by replacing placeholders.
    
    Groups line items by their position relative to anchors:
    - Before Gross Income: Revenue items
    - Between Gross Income and Operating Income: COGS and other items
    - Between Operating Income and Income before Taxes: Operating expenses
    - Between Income before Taxes and Net Income: Tax-related items
    
    Args:
        worksheet: openpyxl Worksheet object
        line_items: List of Income Statement line items
        matrix: Role/year matrix
        year_column_map: Dictionary mapping year -> column_index
        section_start_row: Starting row of Income Statement section
    """
    structure = STATEMENT_STRUCTURE["income_statement"]
    anchors = structure["anchors"]
    placeholder_text = structure["placeholder_text"]
    
    # Find anchor rows
    anchor_map = find_anchor_rows(worksheet, anchors, section_start_row, section_start_row + 100)
    
    # Group line items by position relative to anchors
    gross_income_row = anchor_map.get("gross income")
    operating_income_row = anchor_map.get("operating income")
    income_before_taxes_row = anchor_map.get("income before taxes")
    net_income_row = anchor_map.get("net income")
    
    if not gross_income_row:
        logger.warning("Could not find 'Gross Income' anchor in Income Statement")
        return
    
    # Find placeholders before Gross Income (Revenue items)
    if gross_income_row:
        placeholder_rows_before_gross = find_line_item_placeholders(
            worksheet, placeholder_text, section_start_row + 1, gross_income_row - 1
        )
        revenue_items = [item for item in line_items if item.get("model_role") == "IS_REVENUE"]
        if revenue_items and placeholder_rows_before_gross:
            # Deduplicate: only keep one Revenue item (the first one)
            unique_revenue_items = [revenue_items[0]] if revenue_items else []
            replace_line_item_placeholders(
                worksheet, placeholder_rows_before_gross[:len(unique_revenue_items)], 
                unique_revenue_items, matrix, year_column_map
            )
            logger.debug(f"Replaced {len(unique_revenue_items)} Revenue items before Gross Income")
    
    # Find placeholders between Gross Income and Operating Income (COGS, etc.)
    if gross_income_row and operating_income_row:
        placeholder_rows_before_operating = find_line_item_placeholders(
            worksheet, placeholder_text, gross_income_row + 1, operating_income_row - 1
        )
        cogs_items = [item for item in line_items if item.get("model_role") == "IS_COGS"]
        if cogs_items and placeholder_rows_before_operating:
            unique_cogs_items = [cogs_items[0]] if cogs_items else []
            replace_line_item_placeholders(
                worksheet, placeholder_rows_before_operating[:len(unique_cogs_items)],
                unique_cogs_items, matrix, year_column_map
            )
    
    # Find placeholders between Operating Income and Income before Taxes (Operating expenses)
    if operating_income_row and income_before_taxes_row:
        placeholder_rows_before_taxes = find_line_item_placeholders(
            worksheet, placeholder_text, operating_income_row + 1, income_before_taxes_row - 1
        )
        opex_items = [item for item in line_items if item.get("model_role") == "IS_OPERATING_EXPENSE"]
        if opex_items and placeholder_rows_before_taxes:
            unique_opex_items = [opex_items[0]] if opex_items else []
            replace_line_item_placeholders(
                worksheet, placeholder_rows_before_taxes[:len(unique_opex_items)],
                unique_opex_items, matrix, year_column_map
            )


def populate_balance_sheet_line_items(
    worksheet,
    line_items: List[Dict[str, Any]],
    matrix: Dict[str, Dict[int, float]],
    year_column_map: Dict[int, int],
    section_start_row: int
) -> None:
    """
    Populate Balance Sheet with dynamic line items for Assets, Liabilities, and Equity sections.
    
    Args:
        worksheet: openpyxl Worksheet object
        line_items: List of Balance Sheet line items
        matrix: Role/year matrix
        year_column_map: Dictionary mapping year -> column_index
        section_start_row: Starting row of Balance Sheet section
    """
    structure = STATEMENT_STRUCTURE["balance_sheet"]
    subsections = structure["subsections"]
    
    # Map model roles to subsections
    assets_roles = {"BS_CASH", "BS_INVENTORY", "BS_ACCOUNTS_RECEIVABLE", "BS_PP_AND_E"}
    liabilities_roles = {"BS_ACCOUNTS_PAYABLE", "BS_ACCRUED_LIABILITIES", "BS_DEBT_CURRENT", "BS_DEBT_NON_CURRENT"}
    equity_roles = set()  # Add equity roles if needed
    
    # Helper function to deduplicate items by model_role (keep first occurrence)
    def deduplicate_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen_roles = set()
        unique_items = []
        for item in items:
            role = item.get("model_role")
            if role and role not in seen_roles:
                seen_roles.add(role)
                unique_items.append(item)
        return unique_items
    
    # Process Assets section
    assets_header_row = find_statement_section_start(worksheet, subsections["assets"]["header"], section_start_row)
    if assets_header_row:
        assets_items_raw = [item for item in line_items if item.get("model_role") in assets_roles]
        assets_items = deduplicate_items(assets_items_raw)
        anchor_map = find_anchor_rows(worksheet, subsections["assets"]["anchors"], assets_header_row, assets_header_row + 50)
        first_anchor = anchor_map.get("total current assets")
        if first_anchor:
            placeholder_rows = find_line_item_placeholders(worksheet, subsections["assets"]["placeholder_text"], assets_header_row + 1, first_anchor - 1)
            if assets_items and placeholder_rows:
                replace_line_item_placeholders(
                    worksheet, placeholder_rows, assets_items, matrix, year_column_map
                )
                logger.debug(f"Replaced {len(assets_items)} Balance Sheet Assets items")
    
    # Process Liabilities section
    liabilities_header_row = find_statement_section_start(worksheet, subsections["liabilities"]["header"], section_start_row)
    if liabilities_header_row:
        liabilities_items_raw = [item for item in line_items if item.get("model_role") in liabilities_roles]
        liabilities_items = deduplicate_items(liabilities_items_raw)
        anchor_map = find_anchor_rows(worksheet, subsections["liabilities"]["anchors"], liabilities_header_row, liabilities_header_row + 50)
        first_anchor = anchor_map.get("total current liabilities")
        if first_anchor:
            placeholder_rows = find_line_item_placeholders(worksheet, subsections["liabilities"]["placeholder_text"], liabilities_header_row + 1, first_anchor - 1)
            if liabilities_items and placeholder_rows:
                replace_line_item_placeholders(
                    worksheet, placeholder_rows, liabilities_items, matrix, year_column_map
                )
                logger.debug(f"Replaced {len(liabilities_items)} Balance Sheet Liabilities items")
    
    # Process Equity section
    equity_header_row = find_statement_section_start(worksheet, subsections["equity"]["header"], section_start_row)
    if equity_header_row:
        equity_items_raw = [item for item in line_items if item.get("model_role") in equity_roles]
        equity_items = deduplicate_items(equity_items_raw)
        anchor_map = find_anchor_rows(worksheet, subsections["equity"]["anchors"], equity_header_row, equity_header_row + 50)
        first_anchor = anchor_map.get("total equity")
        if first_anchor:
            placeholder_rows = find_line_item_placeholders(worksheet, subsections["equity"]["placeholder_text"], equity_header_row + 1, first_anchor - 1)
            if equity_items and placeholder_rows:
                replace_line_item_placeholders(
                    worksheet, placeholder_rows, equity_items, matrix, year_column_map
                )
                logger.debug(f"Replaced {len(equity_items)} Balance Sheet Equity items")


def populate_cash_flow_line_items(
    worksheet,
    line_items: List[Dict[str, Any]],
    matrix: Dict[str, Dict[int, float]],
    year_column_map: Dict[int, int],
    section_start_row: int
) -> None:
    """
    Populate Cash Flow Statement with dynamic line items for Operating, Investing, and Financing sections.
    
    Args:
        worksheet: openpyxl Worksheet object
        line_items: List of Cash Flow line items
        matrix: Role/year matrix
        year_column_map: Dictionary mapping year -> column_index
        section_start_row: Starting row of Cash Flow Statement section
    """
    structure = STATEMENT_STRUCTURE["cash_flow"]
    subsections = structure["subsections"]
    
    # Map model roles to subsections
    operating_roles = {"CF_DEPRECIATION", "CF_CHANGE_IN_WORKING_CAPITAL"}
    investing_roles = {"CF_CAPEX"}
    financing_roles = {"CF_SHARE_REPURCHASES", "CF_DIVIDENDS_PAID", "CF_DEBT_ISSUANCE", "CF_DEBT_REPAYMENT"}
    
    # Helper function to deduplicate items by model_role (keep first occurrence)
    def deduplicate_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen_roles = set()
        unique_items = []
        for item in items:
            role = item.get("model_role")
            if role and role not in seen_roles:
                seen_roles.add(role)
                unique_items.append(item)
        return unique_items
    
    # Process Operating Activities
    operating_header_row = find_statement_section_start(worksheet, subsections["operating"]["header"], section_start_row)
    if operating_header_row:
        operating_items_raw = [item for item in line_items if item.get("model_role") in operating_roles]
        operating_items = deduplicate_items(operating_items_raw)
        logger.debug(f"Found {len(operating_items)} Operating Activities items: {[item.get('label') for item in operating_items]}")
        anchor_map = find_anchor_rows(worksheet, subsections["operating"]["anchors"], operating_header_row, operating_header_row + 50)
        first_anchor = anchor_map.get("net cash provided by/(used in) operating activities")
        if first_anchor:
            placeholder_rows = find_line_item_placeholders(worksheet, subsections["operating"]["placeholder_text"], operating_header_row + 1, first_anchor - 1)
            logger.debug(f"Found {len(placeholder_rows)} placeholder rows for Operating Activities: {placeholder_rows}")
            if operating_items and placeholder_rows:
                replace_line_item_placeholders(
                    worksheet, placeholder_rows, operating_items, matrix, year_column_map
                )
                logger.info(f"Replaced {len(operating_items)} Cash Flow Operating items")
            elif operating_items and not placeholder_rows:
                logger.warning(f"Found {len(operating_items)} Operating Activities items but no placeholder rows to replace")
            elif not operating_items and placeholder_rows:
                logger.warning(f"Found {len(placeholder_rows)} placeholder rows but no Operating Activities items to populate")
    
    # Process Investing Activities
    investing_header_row = find_statement_section_start(worksheet, subsections["investing"]["header"], section_start_row)
    if investing_header_row:
        investing_items_raw = [item for item in line_items if item.get("model_role") in investing_roles]
        investing_items = deduplicate_items(investing_items_raw)
        logger.debug(f"Found {len(investing_items)} Investing Activities items: {[item.get('label') for item in investing_items]}")
        anchor_map = find_anchor_rows(worksheet, subsections["investing"]["anchors"], investing_header_row, investing_header_row + 50)
        first_anchor = anchor_map.get("net cash provided by/(used in) investing activities")
        if first_anchor:
            placeholder_rows = find_line_item_placeholders(worksheet, subsections["investing"]["placeholder_text"], investing_header_row + 1, first_anchor - 1)
            logger.debug(f"Found {len(placeholder_rows)} placeholder rows for Investing Activities: {placeholder_rows}")
            if investing_items and placeholder_rows:
                replace_line_item_placeholders(
                    worksheet, placeholder_rows, investing_items, matrix, year_column_map
                )
                logger.info(f"Replaced {len(investing_items)} Cash Flow Investing items")
            elif investing_items and not placeholder_rows:
                logger.warning(f"Found {len(investing_items)} Investing Activities items but no placeholder rows to replace")
            elif not investing_items and placeholder_rows:
                logger.warning(f"Found {len(placeholder_rows)} placeholder rows but no Investing Activities items to populate")
    
    # Process Financing Activities
    financing_header_row = find_statement_section_start(worksheet, subsections["financing"]["header"], section_start_row)
    if financing_header_row:
        financing_items_raw = [item for item in line_items if item.get("model_role") in financing_roles]
        financing_items = deduplicate_items(financing_items_raw)
        logger.debug(f"Found {len(financing_items)} Financing Activities items: {[item.get('label') for item in financing_items]}")
        anchor_map = find_anchor_rows(worksheet, subsections["financing"]["anchors"], financing_header_row, financing_header_row + 50)
        first_anchor = anchor_map.get("net cash provided by/(used in) financing activities")
        if first_anchor:
            placeholder_rows = find_line_item_placeholders(worksheet, subsections["financing"]["placeholder_text"], financing_header_row + 1, first_anchor - 1)
            logger.debug(f"Found {len(placeholder_rows)} placeholder rows for Financing Activities: {placeholder_rows}")
            if financing_items and placeholder_rows:
                replace_line_item_placeholders(
                    worksheet, placeholder_rows, financing_items, matrix, year_column_map
                )
                logger.info(f"Replaced {len(financing_items)} Cash Flow Financing items")
            elif financing_items and not placeholder_rows:
                logger.warning(f"Found {len(financing_items)} Financing Activities items but no placeholder rows to replace")
            elif not financing_items and placeholder_rows:
                logger.warning(f"Found {len(placeholder_rows)} placeholder rows but no Financing Activities items to populate")


def populate_three_statement_historicals(
    worksheet,
    role_column: str,
    matrix: Dict[str, Dict[int, float]],
    year_column_map: Dict[int, int],
    line_items: Optional[List[Dict[str, Any]]] = None
) -> None:
    """
    Populate historical data specifically for 3-statement model worksheet.
    
    This function is tailored for the "3-STMT A" sheet and handles:
    - Income Statement items (Revenue, COGS, Operating Expenses, etc.)
    - Balance Sheet items (Cash, PPE, Inventory, Debt, etc.)
    - Cash Flow items (Capex, Depreciation, Working Capital, etc.)
    
    First inserts dynamic line items to replace "Line Item" placeholders,
    then populates historical data for all items.
    
    Skips rows with "%" in the label (these are calculated, not filled).
    Ensures proper number formatting to prevent date interpretation.
    
    Args:
        worksheet: openpyxl Worksheet object for "3-STMT A" sheet
        role_column: Column letter containing model_role values (typically "ZZ")
        matrix: Role/year matrix from build_role_year_matrix()
        year_column_map: Dictionary mapping year -> column_index
        line_items: Optional list of line items from JSON for dynamic insertion
    """
    col_idx = column_index_from_string(role_column)
    
    # Step 1: Insert dynamic line items if provided
    if line_items:
        logger.info("Inserting dynamic line items for 3-statement model")
        grouped_items = group_line_items_by_statement(line_items)
        
        # Find statement section starts
        income_start = find_statement_section_start(worksheet, "Income Statement")
        balance_start = find_statement_section_start(worksheet, "Balance Sheet")
        cash_flow_start = find_statement_section_start(worksheet, "Cash Flow Statement")
        
        # Populate Income Statement line items
        if income_start and grouped_items["income_statement"]:
            populate_income_statement_line_items(
                worksheet, grouped_items["income_statement"], matrix, year_column_map, income_start
            )
        
        # Populate Balance Sheet line items
        if balance_start and grouped_items["balance_sheet"]:
            populate_balance_sheet_line_items(
                worksheet, grouped_items["balance_sheet"], matrix, year_column_map, balance_start
            )
        
        # Populate Cash Flow line items
        if cash_flow_start and grouped_items["cash_flow"]:
            populate_cash_flow_line_items(
                worksheet, grouped_items["cash_flow"], matrix, year_column_map, cash_flow_start
            )
        
        # Re-add model_role column after row insertions
        add_model_role_column(worksheet, role_column=role_column)
    
    # Step 2: Populate historical data for all items (including inserted ones)
    # Key model roles for 3-statement model organized by statement type
    income_statement_roles = {
        "IS_REVENUE",
        "IS_COGS",
        "IS_OPERATING_EXPENSE",
        "IS_OPERATING_INCOME",
        "IS_EBIT",
        "IS_EBITDA",
        "IS_NET_INCOME",
        "IS_NOPAT",
    }
    
    balance_sheet_roles = {
        "BS_CASH",
        "BS_PP_AND_E",
        "BS_INVENTORY",
        "BS_ACCOUNTS_RECEIVABLE",
        "BS_ACCOUNTS_PAYABLE",
        "BS_ACCRUED_LIABILITIES",
        "BS_DEBT_CURRENT",
        "BS_DEBT_NON_CURRENT",
    }
    
    cash_flow_roles = {
        "CF_CAPEX",
        "CF_DEPRECIATION",
        "CF_CHANGE_IN_WORKING_CAPITAL",
        "CF_SHARE_REPURCHASES",
        "CF_DIVIDENDS_PAID",
        "CF_DEBT_ISSUANCE",
        "CF_DEBT_REPAYMENT",
    }
    
    # Track which roles we've populated for logging
    populated_roles = {
        "income_statement": [],
        "balance_sheet": [],
        "cash_flow": [],
    }
    
    # Iterate through all rows
    for row_idx, row in enumerate(worksheet.iter_rows(min_col=col_idx, max_col=col_idx, values_only=False), start=1):
        role_cell = row[0]
        model_role = (role_cell.value or "").strip()
        
        if not model_role:
            continue
        
        # Skip rows with "%" in the label (these are calculated, not filled)
        # Check the row label in column B
        label_cell = worksheet.cell(row=row_idx, column=2)
        label_value = str(label_cell.value or "").strip()
        if "%" in label_value:
            continue
        
        # Determine which statement type this role belongs to
        statement_type = None
        if model_role in income_statement_roles:
            statement_type = "income_statement"
        elif model_role in balance_sheet_roles:
            statement_type = "balance_sheet"
        elif model_role in cash_flow_roles:
            statement_type = "cash_flow"
        else:
            # Unknown role, skip it (or could log a warning)
            continue
        
        # Look up values for this model_role
        role_values = matrix.get(model_role, {})
        
        if not role_values:
            continue
        
        # Write values to historical columns with proper formatting
        for year, column_idx in year_column_map.items():
            if year in role_values:
                value = role_values[year]
                target_cell = worksheet.cell(row=row_idx, column=column_idx)
                target_cell.value = value
                
                # Set number format to prevent date interpretation
                # Use General format for all numeric values
                if isinstance(value, (int, float)):
                    target_cell.number_format = "General"
        
        # Track populated role
        if model_role not in populated_roles[statement_type]:
            populated_roles[statement_type].append(model_role)
    
    # Log summary
    total_populated = sum(len(roles) for roles in populated_roles.values())
    logger.info(f"Populated 3-statement historicals: {total_populated} roles")
    logger.debug(f"  Income Statement: {len(populated_roles['income_statement'])} roles")
    logger.debug(f"  Balance Sheet: {len(populated_roles['balance_sheet'])} roles")
    logger.debug(f"  Cash Flow: {len(populated_roles['cash_flow'])} roles")


def populate_template_from_json(
    json_path: str,
    template_path: str,
    output_path: str,
    target_sheets: Optional[List[str]] = None,
    assumptions_path: Optional[str] = None
) -> None:
    """
    Main orchestration function to populate Excel template with historical data from JSON.
    
    Args:
        json_path: Path to structured JSON file
        template_path: Path to Excel template file
        output_path: Path where populated template will be saved
        target_sheets: List of sheet names to populate (default: ["DCF A", "3-STMT A"])
        assumptions_path: Optional path to assumptions JSON file for 3-statement model
    """
    if target_sheets is None:
        target_sheets = ["DCF A"]
    
    if not OPENPYXL_AVAILABLE:
        raise ImportError("openpyxl is required for reading Excel templates. Install with: pip install openpyxl")
    
    # Step 1: Load JSON and build matrix
    logger.info(f"Loading JSON from {json_path}")
    json_data = load_structured_json(json_path)
    
    logger.info("Extracting line items from JSON")
    line_items = extract_line_items_from_json(json_data)
    logger.info(f"Extracted {len(line_items)} line items")
    
    logger.info("Building role/year matrix")
    matrix = build_role_year_matrix(line_items)
    logger.info(f"Built matrix with {len(matrix)} model roles")
    
    # Get all years from matrix
    all_years = set()
    for role_values in matrix.values():
        all_years.update(role_values.keys())
    years_list = sorted(all_years)
    logger.info(f"Found years: {years_list}")
    
    # Step 2: Copy template to output path first (preserves original template as source of truth)
    # This also avoids permission errors if the template is open in Excel
    if template_path != output_path:
        logger.info(f"Copying template from {template_path} to {output_path}")
        shutil.copy2(template_path, output_path)
        template_path = output_path  # Work on the copy
    
    # Step 3: Load Excel template (now working on copy)
    logger.info(f"Loading Excel template from {template_path}")
    workbook = load_excel_template(template_path)
    
    # Step 3.5: Populate cover sheet
    company_info = json_data.get("company", {})
    company_name = company_info.get("company_name", "").strip()
    ticker = company_info.get("ticker", "").strip()
    
    if company_name and ticker:
        logger.info("Populating cover sheet")
        populate_cover_sheet(workbook, company_name, ticker)
    else:
        logger.warning(f"Missing company info (name={company_name}, ticker={ticker}), skipping cover sheet")
    
    # Step 3.6: Load assumptions if provided
    assumptions_data = None
    if assumptions_path:
        logger.info(f"Loading assumptions from {assumptions_path}")
        try:
            assumptions_data = load_structured_json(assumptions_path)
            logger.info("Assumptions loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load assumptions: {e}")
    
    # Step 4: Process each target sheet
    for sheet_name in target_sheets:
        if sheet_name not in workbook.sheetnames:
            logger.warning(f"Sheet '{sheet_name}' not found in template. Skipping.")
            continue
        
        logger.info(f"Processing sheet: {sheet_name}")
        worksheet = workbook[sheet_name]
        
        # Add model_role column
        add_model_role_column(worksheet, role_column="ZZ")
        
        # Detect historical columns (looks for "Year"A" headers)
        hist_columns = detect_historical_columns(worksheet)
        if not hist_columns:
            logger.warning(f"No 'Year\"A\"' columns found in sheet '{sheet_name}'. Skipping.")
            continue
        
        logger.info(f"Found {len(hist_columns)} historical columns: {hist_columns}")
        
        # Map years to columns
        year_column_map = map_years_to_columns(years_list, hist_columns)
        logger.info(f"Mapped years to columns: {year_column_map}")
        
        # Write year headers to row 16 BEFORE any line item operations
        # This ensures years are written to the header row and won't be overwritten
        # Also search for and overwrite any "Year 'A'" headers in each statement section
        write_year_headers(worksheet, year_column_map, header_row=16)
        logger.info(f"Wrote year headers to row 16: {sorted(year_column_map.keys())}")
        
        # For 3-STMT A sheet, overwrite "Year 'A'" headers in each statement section header row
        # Use the unified function for all three statements (Income Statement, Balance Sheet, Cash Flow Statement)
        if sheet_name == "3-STMT A":
            overwrite_year_headers_in_statement_section(worksheet, "Income Statement", year_column_map)
            overwrite_year_headers_in_statement_section(worksheet, "Balance Sheet", year_column_map)
            overwrite_year_headers_in_statement_section(worksheet, "Cash Flow Statement", year_column_map)
        
        # Populate historicals - use dedicated function for 3-STMT A sheet
        if sheet_name == "3-STMT A":
            # Ensure line item replacement doesn't affect row 16 (year headers)
            populate_three_statement_historicals(
                worksheet, 
                role_column="ZZ", 
                matrix=matrix, 
                year_column_map=year_column_map,
                line_items=line_items
            )
            logger.info(f"Populated 3-statement historicals for sheet '{sheet_name}'")
            
            # Populate assumptions for 3-STMT A sheet if assumptions provided
            # This happens AFTER line items to ensure assumptions are anchored correctly
            if assumptions_data:
                logger.info("Populating 3-statement assumptions")
                populate_three_statement_assumptions(worksheet, assumptions_data, forecast_periods=5)
        else:
            # Use generic historical population for other sheets (e.g., DCF A)
            populate_historicals(worksheet, role_column="ZZ", matrix=matrix, year_column_map=year_column_map)
            logger.info(f"Populated historicals for sheet '{sheet_name}'")
    
    # Step 5: Save workbook
    logger.info(f"Saving populated template to {output_path}")
    workbook.save(output_path)
    logger.info("Template population complete")


def export_full_model_to_excel(
    json_path: str,
    template_path: str,
    output_path: str,
    comps_input: Optional[List[Dict[str, Any]]] = None,
) -> None:
    """
    Main orchestration function to populate Excel template with historical data from JSON.
    
    Loads structured JSON, extracts historical financial data, and writes to Excel template.
    Excel formulas handle all forecasting/calculations - this function only provides historical inputs.
    
    Args:
        json_path: Path to structured JSON file
        template_path: Path to Excel template file
        output_path: Path where populated template will be saved
        comps_input: Optional list of comparable company data for RV sheet
            Each dict should have: name, ev_ebitda, pe, ev_sales (or None)
    """
    if not OPENPYXL_AVAILABLE:
        raise ImportError("openpyxl is required for reading Excel templates. Install with: pip install openpyxl")
    
    # Step 1: Load JSON and build CompanyModelInput
    logger.info(f"Loading JSON from {json_path}")
    json_data = load_structured_json(json_path)
    
    logger.info("Building CompanyModelInput")
    model_input = build_company_model_input(json_data)
    logger.info(f"Built model input for {model_input.ticker} ({model_input.name})")
    
    # Step 1.5: Run modeling modules (for programmatic access, but Excel handles forecasting)
    # Default assumptions - can be made configurable later
    default_assumptions = {
        "revenue_growth": 0.05,
        "operating_margin_target": 0.15,
        "tax_rate": 0.21,
        "capex_as_pct_revenue": 0.05,
        "depreciation_as_pct_revenue": 0.03,
        "wacc": 0.10,
        "terminal_growth_rate": 0.025,
        # WACC components
        "beta": 1.2,
        "market_risk_premium": 0.06,
        "risk_free_rate": 0.04,
        "cost_of_debt": 0.05,
        # Other assumptions
        "shares_outstanding": None,  # Can be calculated or provided
        "debt": None,  # Can be extracted from historicals or provided
        "current_price": None,  # Market data, optional
    }
    
    logger.info("Running 3-statement model")
    three_stmt_output = run_three_statement(
        model_input=model_input,
        assumptions=default_assumptions,
        forecast_periods=5,
    )
    
    logger.info("Running DCF model")
    dcf_output = run_dcf(
        projections=three_stmt_output,
        assumptions=default_assumptions,
    )
    
    logger.info("Running comps analysis")
    comps_output = run_comps(
        model_input=model_input,
        comparables=comps_input,
    )
    
    logger.info(f"DCF Enterprise Value: ${dcf_output.enterprise_value:,.0f}")
    logger.info(f"Comps implied values: {comps_output.implied_values}")
    
    # Step 2: Build role/year matrix from historicals
    logger.info("Building role/year matrix")
    matrix = model_input.historicals.by_role
    logger.info(f"Built matrix with {len(matrix)} model roles")
    
    # Get all years from matrix
    all_years = set()
    for role_values in matrix.values():
        all_years.update(role_values.keys())
    years_list = sorted(all_years)
    logger.info(f"Found years: {years_list}")
    
    # Step 3: Copy template to output path first (preserves original template as source of truth)
    # This also avoids permission errors if the template is open in Excel
    if template_path != output_path:
        logger.info(f"Copying template from {template_path} to {output_path}")
        shutil.copy2(template_path, output_path)
        template_path = output_path  # Work on the copy
    
    # Step 4: Load Excel template (now working on copy)
    logger.info(f"Loading Excel template from {template_path}")
    workbook = load_excel_template(template_path)
    
    # Step 4.5: Populate cover sheet
    logger.info("Populating cover sheet")
    populate_cover_sheet(workbook, model_input.name, model_input.ticker)
    
    # Step 5: Process DCF A and 3-STMT A sheets
    target_sheets = ["DCF A", "3-STMT A"]
    for sheet_name in target_sheets:
        if sheet_name not in workbook.sheetnames:
            logger.warning(f"Sheet '{sheet_name}' not found in template. Skipping.")
            continue
        
        logger.info(f"Processing sheet: {sheet_name}")
        worksheet = workbook[sheet_name]
        
        # Add model_role column
        add_model_role_column(worksheet, role_column="ZZ")
        
        # Detect historical columns (looks for "Year"A" headers)
        hist_columns = detect_historical_columns(worksheet)
        if not hist_columns:
            logger.warning(f"No 'Year\"A\"' columns found in sheet '{sheet_name}'. Skipping.")
            continue
        
        logger.info(f"Found {len(hist_columns)} historical columns: {hist_columns}")
        
        # Map years to columns
        year_column_map = map_years_to_columns(years_list, hist_columns)
        logger.info(f"Mapped years to columns: {year_column_map}")
        
        # Write year headers to row 16
        write_year_headers(worksheet, year_column_map, header_row=16)
        logger.info(f"Wrote year headers to row 16")
        
        # Populate historicals
        populate_historicals(worksheet, role_column="ZZ", matrix=matrix, year_column_map=year_column_map)
        logger.info(f"Populated historicals for sheet '{sheet_name}'")
        
        # Populate WACC and Other Assumptions if this is the DCF A sheet
        if sheet_name == "DCF A":
            logger.info("Populating WACC and Other Assumptions for DCF A sheet")
            populate_wacc_and_assumptions(worksheet, model_input, dcf_output, default_assumptions)
    
    # Step 6: Process RV sheet if comps_input provided
    if comps_input and "RV" in workbook.sheetnames:
        logger.info("Processing RV sheet")
        worksheet = workbook["RV"]
        _write_rv_sheet(worksheet, model_input, comps_input)
        logger.info("Populated RV sheet")
    elif comps_input:
        logger.warning("RV sheet not found in template, skipping comps data")
    
    # Step 7: Save workbook
    logger.info(f"Saving populated template to {output_path}")
    workbook.save(output_path)
    logger.info("Template population complete")


def populate_wacc_and_assumptions(
    worksheet,
    model_input: CompanyModelInput,
    dcf_output: DcfOutput,
    assumptions: Dict[str, Any]
) -> None:
    """
    Populate WACC calculation inputs and Other Assumptions in DCF A sheet.
    
    Searches for labels in column B (WACC section) and column G (Other Assumptions),
    then writes values to columns D/E and I/J respectively.
    
    Args:
        worksheet: openpyxl Worksheet object for DCF A sheet
        model_input: CompanyModelInput with historical data
        dcf_output: DcfOutput from run_dcf()
        assumptions: Dict with assumptions (wacc, tax_rate, terminal_growth_rate, etc.)
    """
    # WACC section labels (column B) -> values go in column E
    wacc_labels = {
        "beta": ("Beta", assumptions.get("beta", 1.2)),
        "market risk premium": ("Market Risk Premium", assumptions.get("market_risk_premium", 0.06)),
        "risk free rate": ("Risk Free Rate", assumptions.get("risk_free_rate", 0.04)),
        "cost of equity": ("Cost of Equity", None),  # Calculated, skip
        "weight of equity": ("Weight of Equity", None),  # Calculated, skip
        "cost of debt": ("Cost of Debt", assumptions.get("cost_of_debt", 0.05)),
        "after tax cod": ("After Tax CoD", None),  # Calculated, skip
        "weight of debt": ("Weight of Debt", None),  # Calculated, skip
        "tax rate": ("Tax Rate", assumptions.get("tax_rate", 0.21)),
        "wacc": ("WACC", assumptions.get("wacc", 0.10)),
    }
    
    # Other Assumptions labels (column G) -> values go in column J
    other_assumptions_labels = {
        "fiscal year end": ("Fiscal Year End", "12/31/2025"),
        "ltgr": ("LTGR", f"{assumptions.get('terminal_growth_rate', 0.025) * 100:.2f}%"),
        "cash & equivalents": ("Cash & Equivalents", None),  # From historicals
        "cash and equivalents": ("Cash & Equivalents", None),  # Alternative label
        "diluted s/o": ("Diluted S/O", None),  # Will write to row 8 explicitly
        "diluted shares": ("Diluted S/O", None),  # Will write to row 8 explicitly
        "current price": ("Current Price", None),  # Will write to row 9 explicitly
        "mkt cap": ("Mkt Cap", None),  # Calculated, skip
        "market cap": ("Mkt Cap", None),  # Alternative label
        "bv debt": ("BV debt", assumptions.get("debt", None)),
        "book value debt": ("BV debt", assumptions.get("debt", None)),
        "financial units": ("Financial Units", "USD"),
    }
    
    # Search for WACC labels in column B (rows 1-50)
    for row_idx in range(1, min(51, worksheet.max_row + 1)):
        label_cell = worksheet.cell(row=row_idx, column=2)  # Column B
        label_value = str(label_cell.value or "").strip().lower()
        
        # Check if this matches any WACC label
        for key, (display_name, value) in wacc_labels.items():
            if key in label_value and value is not None:
                # Write to column E
                value_cell = worksheet.cell(row=row_idx, column=5)  # Column E
                if value_cell.value is None or str(value_cell.value).strip() == "#":
                    value_cell.value = value
                    logger.debug(f"Wrote {display_name} = {value} to row {row_idx}, column E")
                break
    
    # Get latest cash and debt from historicals
    historicals = model_input.historicals.by_role
    all_years = set()
    for role_values in historicals.values():
        all_years.update(role_values.keys())
    latest_year = max(all_years) if all_years else None
    latest_cash = None
    latest_debt = None
    if latest_year:
        latest_cash = historicals.get("BS_CASH", {}).get(latest_year)
        # Try to get debt from various possible model roles
        latest_debt = (
            historicals.get("BS_DEBT_CURRENT", {}).get(latest_year) or
            historicals.get("BS_DEBT_NON_CURRENT", {}).get(latest_year) or
            assumptions.get("debt")
        )
    
    # Search for Other Assumptions labels in column G (rows 1-50)
    for row_idx in range(1, min(51, worksheet.max_row + 1)):
        label_cell = worksheet.cell(row=row_idx, column=7)  # Column G
        label_value = str(label_cell.value or "").strip().lower()
        
        # Check if this matches any Other Assumptions label
        for key, (display_name, value) in other_assumptions_labels.items():
            if key in label_value:
                # Special handling for Cash & Equivalents and BV debt
                if "cash" in key and latest_cash is not None:
                    value = latest_cash
                elif "bv debt" in key or "book value debt" in key:
                    if latest_debt is not None:
                        value = latest_debt
                    elif value is None:
                        continue  # Skip if no debt value available
                # Skip Diluted S/O and Current Price here - will write to specific rows below
                elif "diluted" in key or "current price" in key:
                    continue
                
                if value is not None:
                    # Write to column J
                    value_cell = worksheet.cell(row=row_idx, column=10)  # Column J
                    if value_cell.value is None or str(value_cell.value).strip() == "#":
                        value_cell.value = value
                        logger.debug(f"Wrote {display_name} = {value} to row {row_idx}, column J")
                break
    
    # Explicitly write to rows 8 and 9 for Diluted S/O and Current Price
    shares_outstanding = assumptions.get("shares_outstanding")
    if shares_outstanding is not None:
        cell_j8 = worksheet.cell(row=8, column=10)  # Column J, Row 8
        if cell_j8.value is None or str(cell_j8.value).strip() == "#":
            cell_j8.value = shares_outstanding
            logger.debug(f"Wrote Diluted S/O = {shares_outstanding} to row 8, column J")
    
    current_price = assumptions.get("current_price")
    if current_price is not None:
        cell_j9 = worksheet.cell(row=9, column=10)  # Column J, Row 9
        if cell_j9.value is None or str(cell_j9.value).strip() == "#":
            cell_j9.value = current_price
            logger.debug(f"Wrote Current Price = {current_price} to row 9, column J")


def _write_rv_sheet(
    worksheet,
    model_input: CompanyModelInput,
    comps_input: List[Dict[str, Any]]
) -> None:
    """
    Write relative valuation data to RV sheet.
    
    Args:
        worksheet: openpyxl Worksheet object for RV sheet
        model_input: CompanyModelInput with historical data
        comps_input: List of comparable company dictionaries
    """
    # Get latest year's data for subject company
    historicals = model_input.historicals.by_role
    latest_year = max(
        (year for role_data in historicals.values() for year in role_data.keys()),
        default=None
    )
    
    if not latest_year:
        logger.warning("No historical data found for RV sheet")
        return
    
    # Extract subject company metrics
    revenue = historicals.get("IS_REVENUE", {}).get(latest_year, 0.0)
    net_income = historicals.get("IS_NET_INCOME", {}).get(latest_year, 0.0)
    
    # Calculate EBITDA if possible (EBIT + D&A)
    ebit = historicals.get("IS_EBIT", {}).get(latest_year)
    da = historicals.get("CF_DEPRECIATION", {}).get(latest_year, 0.0)
    if ebit is not None:
        ebitda = ebit + da
    else:
        ebitda = None
    
    # Write comps table (assuming a standard layout)
    # This is a simplified implementation - adjust based on actual RV sheet structure
    # Typically comps are in rows starting around row 5-10, with columns for Name, EV/EBITDA, P/E, EV/Sales
    
    # Find where to write comps (look for header row)
    comps_start_row = None
    for row_idx in range(1, min(20, worksheet.max_row + 1)):
        row = worksheet[row_idx]
        for cell in row:
            if cell.value and "comparable" in str(cell.value).lower():
                comps_start_row = row_idx + 1
                break
        if comps_start_row:
            break
    
    if not comps_start_row:
        logger.warning("Could not find comps table location in RV sheet")
        return
    
    # Write comps data
    for idx, comp in enumerate(comps_input):
        row_num = comps_start_row + idx
        # Column B: Name
        worksheet.cell(row=row_num, column=2).value = comp.get("name", "")
        # Column C: EV/EBITDA
        if comp.get("ev_ebitda") is not None:
            worksheet.cell(row=row_num, column=3).value = comp["ev_ebitda"]
        # Column D: P/E
        if comp.get("pe") is not None:
            worksheet.cell(row=row_num, column=4).value = comp["pe"]
        # Column E: EV/Sales
        if comp.get("ev_sales") is not None:
            worksheet.cell(row=row_num, column=5).value = comp["ev_sales"]
    
    # Write subject company metrics (typically in a separate section)
    # Look for "Subject" or company name row
    subject_row = None
    for row_idx in range(1, min(30, worksheet.max_row + 1)):
        row = worksheet[row_idx]
        for cell in row:
            if cell.value and ("subject" in str(cell.value).lower() or model_input.ticker.lower() in str(cell.value).lower()):
                subject_row = row_idx
                break
        if subject_row:
            break
    
    if subject_row:
        # Write subject metrics (adjust columns based on actual layout)
        # Revenue
        worksheet.cell(row=subject_row, column=6).value = revenue
        # EBITDA
        if ebitda is not None:
            worksheet.cell(row=subject_row, column=7).value = ebitda
        # Net Income
        worksheet.cell(row=subject_row, column=8).value = net_income


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