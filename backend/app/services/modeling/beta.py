"""
beta.py — Beta Fetch + Excel Link Helpers

Purpose:
- Pull historical price data for a target ticker and benchmark index
- Prepare the raw data range used by Excel formulas to calculate beta
- Provide helpers so Excel export can drop the data onto a worksheet

This module does NOT calculate beta numerically; Excel handles that so
the model stays auditable for analysts.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, Optional

import pandas as pd
import yfinance as yf


# Benchmark options
BENCHMARK_OPTIONS = {
    "^GSPC": "S&P 500",
    "^IXIC": "NASDAQ",
    "^RUT": "Russell 2000",
    "^DJI": "Dow Jones Industrial Average",
}

# Year options (in days)
YEAR_OPTIONS = {
    1: 365,   # 1 year
    3: 1095,  # 3 years (365 * 3)
    5: 1825,  # 5 years (365 * 5)
}

DEFAULT_LOOKBACK_YEARS = 5
DEFAULT_LOOKBACK_DAYS = YEAR_OPTIONS[DEFAULT_LOOKBACK_YEARS]
DEFAULT_BENCHMARK = "^GSPC"  # S&P 500


def fetch_price_history(
    ticker: str,
    benchmark: str = DEFAULT_BENCHMARK,
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    lookback_years: Optional[int] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Pull adjusted close prices for ticker and benchmark over the lookback window.

    Args:
        ticker: Stock ticker symbol
        benchmark: Benchmark index symbol (e.g., "^GSPC" for S&P 500)
        lookback_days: Number of days to look back (overridden by lookback_years if provided)
        lookback_years: Number of years to look back (1, 3, or 5). If provided, overrides lookback_days.

    Returns:
        (ticker_prices, benchmark_prices) as dataframes indexed by date
    """
    # Use years if provided, otherwise use days
    if lookback_years is not None:
        if lookback_years not in YEAR_OPTIONS:
            raise ValueError(f"lookback_years must be 1, 3, or 5, got {lookback_years}")
        lookback_days = YEAR_OPTIONS[lookback_years]
    
    end = datetime.utcnow()
    start = end - timedelta(days=lookback_days)

    ticker_data = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=False)
    benchmark_data = yf.download(benchmark, start=start, end=end, progress=False, auto_adjust=False)

    if ticker_data.empty or benchmark_data.empty:
        raise ValueError("Unable to download price history for beta calc")

    # Handle MultiIndex columns (when multiple tickers) or single-level columns
    if isinstance(ticker_data.columns, pd.MultiIndex):
        ticker_adj_close = ticker_data[("Adj Close", ticker)]
    else:
        ticker_adj_close = ticker_data["Adj Close"]
    
    if isinstance(benchmark_data.columns, pd.MultiIndex):
        benchmark_adj_close = benchmark_data[("Adj Close", benchmark)]
    else:
        benchmark_adj_close = benchmark_data["Adj Close"]

    ticker_prices = (
        ticker_adj_close
        .rename("ticker_adj_close")
        .to_frame()
        .dropna()
    )
    benchmark_prices = (
        benchmark_adj_close
        .rename("benchmark_adj_close")
        .to_frame()
        .dropna()
    )

    return ticker_prices, benchmark_prices


def build_beta_export_payload(
    ticker: str,
    benchmark: str = DEFAULT_BENCHMARK,
    lookback_days: Optional[int] = None,
    lookback_years: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Convenience wrapper that returns everything Excel export needs:
        - aligned price dataframe (date | ticker | benchmark)
        - metadata for labeling
    
    Args:
        ticker: Stock ticker symbol
        benchmark: Benchmark index symbol (e.g., "^GSPC" for S&P 500)
        lookback_days: Number of days to look back (optional, overridden by lookback_years)
        lookback_years: Number of years to look back (1, 3, or 5). Preferred over lookback_days.
    
    Returns:
        Dictionary with ticker, benchmark, lookback_days, and price_table
    """
    # Use default if neither is provided
    if lookback_days is None and lookback_years is None:
        lookback_days = DEFAULT_LOOKBACK_DAYS
    
    # Validate benchmark
    if benchmark not in BENCHMARK_OPTIONS:
        raise ValueError(f"benchmark must be one of {list(BENCHMARK_OPTIONS.keys())}, got {benchmark}")
    
    ticker_prices, benchmark_prices = fetch_price_history(
        ticker=ticker,
        benchmark=benchmark,
        lookback_days=lookback_days,
        lookback_years=lookback_years,
    )

    combined = ticker_prices.join(benchmark_prices, how="inner")
    combined.reset_index(inplace=True)
    # reset_index() will create a "date" column since we named the index "date"
    # Ensure date column is named "date" (reset_index should create it from named index)
    if "Date" in combined.columns:
        combined.rename(columns={"Date": "date"}, inplace=True)

    return {
        "ticker": ticker,
        "benchmark": benchmark,
        "lookback_days": lookback_days,
        "price_table": combined,  # pandas DataFrame ready for writing to Excel
    }


def write_beta_sheet(workbook, beta_payload):
    """
    Helper for excel_export.py to drop the price table and Excel formulas.

    Expected usage:
        workbook = xlsxwriter.Workbook(...)
        beta_payload = build_beta_export_payload(...)
        write_beta_sheet(workbook, beta_payload)

    The sheet contains:
        - Header with ticker, benchmark, lookback window
        - Raw price table
        - Array formulas for returns calculation
        - Beta calculation formula
    """
    import xlsxwriter
    
    worksheet = workbook.add_worksheet("Beta")
    
    # Set column widths (xlsxwriter uses character units, not pixels)
    # Column A: 14 characters (approximately 133 pixels)
    worksheet.set_column('A:A', 14)
    
    # Create formats
    header_format = workbook.add_format({'bold': True})
    number_format = workbook.add_format({'num_format': '0.00'})
    date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})
    
    # Write headers (xlsxwriter is 0-indexed)
    worksheet.write(0, 0, "Ticker", header_format)
    worksheet.write(0, 1, beta_payload["ticker"])
    
    worksheet.write(1, 0, "Benchmark", header_format)
    # Display benchmark name nicely using BENCHMARK_OPTIONS mapping
    benchmark_display = BENCHMARK_OPTIONS.get(
        beta_payload["benchmark"], 
        beta_payload["benchmark"]
    )
    worksheet.write(1, 1, benchmark_display)
    
    worksheet.write(2, 0, "Lookback (years)", header_format)
    worksheet.write(2, 1, beta_payload["lookback_days"] / 365)  # Convert days to years
    
    worksheet.write(3, 0, "Beta", header_format)
    
    # Write column headers
    worksheet.write(4, 0, "Date", header_format)
    worksheet.write(4, 1, "Ticker Adj Close", header_format)
    worksheet.write(4, 2, "Benchmark Adj Close", header_format)
    worksheet.write(4, 4, "Ticker Returns", header_format)
    worksheet.write(4, 5, "Benchmark Returns", header_format)
    
    # Write data (xlsxwriter is 0-indexed, Excel rows start at 1)
    table = beta_payload["price_table"]
    start_row = 5  # Row 6 in Excel (0-indexed = 5)
    
    for idx, row in table.iterrows():
        excel_row = start_row + idx  # 0-indexed
        # Date (convert to datetime if needed)
        date_val = row["date"]
        if hasattr(date_val, 'to_pydatetime'):
            date_val = date_val.to_pydatetime()
        worksheet.write_datetime(excel_row, 0, date_val, date_format)
        
        # Ticker price
        worksheet.write(excel_row, 1, row["ticker_adj_close"], number_format)
        
        # Benchmark price
        worksheet.write(excel_row, 2, row["benchmark_adj_close"], number_format)
    
    # Calculate last row (0-indexed)
    last_row = start_row + len(table) - 1
    last_row_excel = last_row + 1  # Convert to Excel 1-indexed for formulas
    
    # Write array formulas for returns using write_array_formula()
    # Formula: ((new/old)-1)*100 starting at row 7 (Excel row 7 = index 6)
    # We use array formula syntax where each cell calculates its own return
    
    first_return_row = 6  # Excel row 7 (0-indexed = 6)
    last_return_row = last_row  # Last row with data
    
    if last_return_row >= first_return_row:
        # Ticker returns array formula
        # Formula calculates: (B7:B{last}/B6:B{last-1})-1)*100
        # This creates an array where each element is the return for that row
        ticker_returns_formula = f"=((B{first_return_row + 1}:B{last_return_row + 1}/B{first_return_row}:B{last_return_row})-1)*100"
        worksheet.write_array_formula(
            first_return_row, 4,  # First row (0-indexed), Column E (4)
            last_return_row, 4,    # Last row (0-indexed), Column E (4)
            ticker_returns_formula,
            number_format
        )
        
        # Benchmark returns array formula
        benchmark_returns_formula = f"=((C{first_return_row + 1}:C{last_return_row + 1}/C{first_return_row}:C{last_return_row})-1)*100"
        worksheet.write_array_formula(
            first_return_row, 5,  # First row (0-indexed), Column F (5)
            last_return_row, 5,    # Last row (0-indexed), Column F (5)
            benchmark_returns_formula,
            number_format
        )
    
    # Beta formula - use COVARIANCE.P and VAR.P (they already return single scalar values)
    # Write as string starting with = (xlsxwriter treats strings starting with = as formulas)
    covariance_part = f"SLOPE(E{first_return_row + 1}:E{last_row_excel},F{first_return_row + 1}:F{last_row_excel})"
    variance_part = f"VAR.P(F{first_return_row + 1}:F{last_row_excel})"
    beta_formula = f"=SLOPE(E{first_return_row + 1}:E{last_row_excel},F{first_return_row + 1}:F{last_row_excel})"
    worksheet.write(3, 1, beta_formula, number_format)  # Row 4 (0-indexed = 3), Column B (1)
    
    # Freeze panes (freeze row 5, which is index 4)
    worksheet.freeze_panes(5, 0)  # Freeze rows above row 5 (0-indexed: 5 means freeze first 5 rows)