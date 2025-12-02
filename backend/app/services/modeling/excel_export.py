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
    Return historical columns D, E, F (columns 4, 5, 6).
    Years are written to row 16 in these columns.
    
    Args:
        worksheet: openpyxl Worksheet object (unused but kept for API consistency)
        
    Returns:
        List of column indices (1-indexed): [4, 5, 6] for columns D, E, F
    """
    # Historical columns are hardcoded to D, E, F (columns 4, 5, 6)
    return [4, 5, 6]


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


def populate_template_from_json(
    json_path: str,
    template_path: str,
    output_path: str,
    target_sheets: Optional[List[str]] = None
) -> None:
    """
    Main orchestration function to populate Excel template with historical data from JSON.
    
    Args:
        json_path: Path to structured JSON file
        template_path: Path to Excel template file
        output_path: Path where populated template will be saved
        target_sheets: List of sheet names to populate (default: ["DCF A", "3-STMT A"])
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
        
        # Write year headers to row 16
        write_year_headers(worksheet, year_column_map, header_row=16)
        logger.info(f"Wrote year headers to row 16")
        
        # Populate historicals
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