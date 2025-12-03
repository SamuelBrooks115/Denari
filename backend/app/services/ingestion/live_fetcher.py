"""
live_fetcher.py — On-the-fly EDGAR and FMP data fetching and parsing (no database)

Purpose:
- Fetch company data from EDGAR or FMP in real-time
- Parse XBRL (EDGAR) or normalize financial statements (FMP)
- Return in-memory data structures (no persistence)
- Used by MVP live workflow endpoints

This module orchestrates:
For EDGAR:
1. Ticker → CIK lookup
2. EDGAR submissions fetch
3. Company facts fetch
4. XBRL parsing
5. Normalization to canonical financial statements

For FMP:
1. Fetch income statement, balance sheet, and cash flow from FMP API
2. Normalize FMP field names to internal tags
3. Organize by period and statement type
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime

from app.core.logging import get_logger
from app.services.ingestion.clients import EdgarClient
from app.services.ingestion.xbrl.companyfacts_parser import (
    PeriodStatements,
    build_period_statements,
    detect_primary_taxonomy,
    extract_annual_report_dates,
)
from app.services.ingestion.xbrl.normalizer import CompanyFactsNormalizer
from app.services.ingestion.sp500_tickers import SP500_TICKERS
from app.data.fmp_client import (
    fetch_income_statement,
    fetch_balance_sheet,
    fetch_cash_flow,
    fetch_quote,
)

logger = get_logger(__name__)


def fetch_company_live(
    ticker: str,
    years: int = 5,
    edgar_client: Optional[EdgarClient] = None,
) -> Dict[str, Any]:
    """
    Fetch and parse company financial data from EDGAR on-the-fly.

    Args:
        ticker: Company ticker symbol (e.g., "AAPL")
        years: Number of years of historical data to fetch
        edgar_client: Optional EdgarClient instance (creates new if not provided)

    Returns:
        Dictionary containing:
        - ticker: str
        - cik: int
        - name: str (from submissions)
        - taxonomy: str (e.g., "us-gaap")
        - financials: Dict[str, List[Dict]] - normalized facts by period_end
        - periods: List[str] - list of period_end dates
        - raw_submissions: Dict - raw submissions data
        - raw_facts: Dict - raw company facts data

    Raises:
        RuntimeError if ticker not found, CIK lookup fails, or parsing fails
    """
    client = edgar_client or EdgarClient()

    # Step 1: Get CIK from ticker
    logger.info("Looking up CIK for ticker: %s", ticker)
    cik_map = client.get_cik_map()
    cik = cik_map.get(ticker.upper())
    if not cik:
        raise RuntimeError(f"CIK not found for ticker: {ticker}")

    # Step 2: Fetch submissions (for company name and report dates)
    logger.info("Fetching submissions for CIK: %s", cik)
    submissions = client.get_submissions(cik)
    company_name = submissions.get("name", ticker)
    report_dates = extract_annual_report_dates(submissions, years=years)
    
    if not report_dates:
        logger.warning("No annual filings found for %s (CIK: %s)", ticker, cik)
        return {
            "ticker": ticker,
            "cik": cik,
            "name": company_name,
            "taxonomy": None,
            "financials": {},
            "periods": [],
            "raw_submissions": submissions,
            "raw_facts": {},
        }

    # Step 3: Fetch company facts (XBRL data)
    logger.info("Fetching company facts for CIK: %s", cik)
    facts_payload = client.get_company_facts(cik)
    
    # Step 4: Detect taxonomy
    taxonomy = detect_primary_taxonomy(facts_payload)
    if not taxonomy:
        raise RuntimeError(f"No supported taxonomy found for CIK {cik}")

    taxonomy_facts = facts_payload["facts"][taxonomy]

    # Step 5: Build period statements
    logger.info("Parsing XBRL for %d periods", len(report_dates))
    statements_by_period: Dict[str, PeriodStatements] = {}
    for report_date in report_dates:
        statements_by_period[report_date] = build_period_statements(taxonomy_facts, report_date)

    # Step 6: Normalize to canonical financial statements
    logger.info("Normalizing financial statements")
    normalizer = CompanyFactsNormalizer()
    company_meta = {
        "company_id": None,  # No DB in MVP
        "ticker": ticker,
        "cik": cik,
    }
    
    normalized = normalizer.normalize_companyfacts(company_meta, taxonomy, statements_by_period)

    # Convert to more usable format - organize by statement type and period
    financials_by_statement: Dict[str, Dict[str, Dict[str, float]]] = {
        "IS": {},  # Income Statement
        "BS": {},  # Balance Sheet
        "CF": {},  # Cash Flow
        "SHARES": {},  # Share data
    }

    for period_end, facts_list in normalized.items():
        for fact in facts_list:
            stmt_type = fact.get("statement_type", "IS")
            tag = fact.get("tag")
            value = fact.get("value")
            
            if stmt_type not in financials_by_statement:
                continue
            if period_end not in financials_by_statement[stmt_type]:
                financials_by_statement[stmt_type][period_end] = {}
            
            if tag and value is not None:
                financials_by_statement[stmt_type][period_end][tag] = value

    return {
        "ticker": ticker,
        "cik": cik,
        "name": company_name,
        "taxonomy": taxonomy,
        "financials": financials_by_statement,
        "periods": report_dates,
        "raw_submissions": submissions,
        "raw_facts": facts_payload,
    }


def _get_sp500_tickers() -> set:
    """Get set of S&P 500 tickers from hard-coded list."""
    return SP500_TICKERS


def search_company_by_ticker(ticker: str, edgar_client: Optional[EdgarClient] = None) -> Dict[str, Any]:
    """
    Quick search to get basic company info by ticker.
    MVP: Only searches S&P 500 companies.

    Args:
        ticker: Company ticker symbol
        edgar_client: Optional EdgarClient instance

    Returns:
        Dictionary with:
        - ticker: str
        - cik: int
        - name: str
        - found: bool
        - in_sp500: bool (whether ticker is in S&P 500)
    """
    client = edgar_client or EdgarClient()
    ticker_upper = ticker.upper()
    
    try:
        # Check if ticker is in S&P 500
        sp500_tickers = _get_sp500_tickers()
        if ticker_upper not in sp500_tickers:
            return {
                "ticker": ticker,
                "cik": None,
                "name": None,
                "found": False,
                "in_sp500": False,
                "error": f"Ticker {ticker} is not in S&P 500. Only S&P 500 companies are supported in MVP.",
            }
        
        cik_map = client.get_cik_map()
        cik = cik_map.get(ticker_upper)
        
        if not cik:
            return {
                "ticker": ticker,
                "cik": None,
                "name": None,
                "found": False,
                "in_sp500": ticker_upper in sp500_tickers,
            }
        
        # Get company name from submissions
        submissions = client.get_submissions(cik)
        company_name = submissions.get("name", ticker)
        
        return {
            "ticker": ticker,
            "cik": cik,
            "name": company_name,
            "found": True,
            "in_sp500": True,
        }
    except Exception as exc:
        logger.exception("Error searching for ticker %s: %s", ticker, exc)
        return {
            "ticker": ticker,
            "cik": None,
            "name": None,
            "found": False,
            "in_sp500": False,
            "error": str(exc),
        }


def fetch_company_live_fmp(
    ticker: str,
    years: int = 5,
) -> Dict[str, Any]:
    """
    Fetch and parse company financial data from FMP (Financial Modeling Prep) API on-the-fly.

    Args:
        ticker: Company ticker symbol (e.g., "AAPL")
        years: Number of years of historical data to fetch

    Returns:
        Dictionary containing:
        - ticker: str
        - cik: Optional[int] (not available from FMP, set to None)
        - name: str (from quote data)
        - taxonomy: str (set to "fmp" to indicate FMP source)
        - financials: Dict[str, Dict[str, Dict[str, float]]] - normalized facts by period_end
        - periods: List[str] - list of period_end dates (YYYY-MM-DD format)
        - raw_submissions: Dict (empty, kept for compatibility)
        - raw_facts: Dict (contains raw FMP data)

    Raises:
        RuntimeError if ticker not found or API call fails
    """
    ticker_upper = ticker.upper()
    quote = None
    
    # Step 1: Fetch company quote for name
    logger.info("Fetching company quote for ticker: %s", ticker_upper)
    try:
        quote = fetch_quote(ticker_upper)
        company_name = quote.get("name", ticker_upper) if quote else ticker_upper
    except Exception as e:
        logger.warning("Could not fetch quote for %s: %s. Using ticker as name.", ticker_upper, e)
        company_name = ticker_upper
    
    # Step 2: Fetch all three financial statements
    logger.info("Fetching financial statements for %s (limit=%d)", ticker_upper, years)
    try:
        income_statements = fetch_income_statement(ticker_upper, limit=years)
        balance_sheets = fetch_balance_sheet(ticker_upper, limit=years)
        cash_flows = fetch_cash_flow(ticker_upper, limit=years)
    except Exception as e:
        raise RuntimeError(f"Failed to fetch financial data from FMP for {ticker_upper}: {e}") from e
    
    if not income_statements and not balance_sheets and not cash_flows:
        logger.warning("No financial data found for %s", ticker_upper)
        return {
            "ticker": ticker_upper,
            "cik": None,
            "name": company_name,
            "taxonomy": "fmp",
            "financials": {},
            "periods": [],
            "raw_submissions": {},
            "raw_facts": {
                "income_statements": [],
                "balance_sheets": [],
                "cash_flows": [],
            },
        }
    
    # Step 3: Extract periods from income statements (most reliable)
    periods_set = set()
    for stmt in income_statements:
        date_str = stmt.get("date") or stmt.get("calendarYear")
        if date_str:
            # Convert to YYYY-MM-DD format if needed
            if isinstance(date_str, str) and len(date_str) == 4:
                # Just a year, use year-end date
                date_str = f"{date_str}-12-31"
            periods_set.add(str(date_str))
    
    # If no periods from income statements, try balance sheets
    if not periods_set:
        for stmt in balance_sheets:
            date_str = stmt.get("date") or stmt.get("calendarYear")
            if date_str:
                if isinstance(date_str, str) and len(date_str) == 4:
                    date_str = f"{date_str}-12-31"
                periods_set.add(str(date_str))
    
    # If still no periods, try cash flows
    if not periods_set:
        for stmt in cash_flows:
            date_str = stmt.get("date") or stmt.get("calendarYear")
            if date_str:
                if isinstance(date_str, str) and len(date_str) == 4:
                    date_str = f"{date_str}-12-31"
                periods_set.add(str(date_str))
    
    periods = sorted(list(periods_set), reverse=True)[:years]  # Most recent first, limit to years
    
    if not periods:
        logger.warning("No valid periods found in FMP data for %s", ticker_upper)
        return {
            "ticker": ticker_upper,
            "cik": None,
            "name": company_name,
            "taxonomy": "fmp",
            "financials": {},
            "periods": [],
            "raw_submissions": {},
            "raw_facts": {
                "income_statements": income_statements,
                "balance_sheets": balance_sheets,
                "cash_flows": cash_flows,
            },
        }
    
    # Step 4: Map FMP field names to normalized tags
    # This mapping converts FMP's camelCase field names to our internal tag format
    FMP_TO_TAG_MAPPING: Dict[str, Dict[str, str]] = {
        "IS": {
            "revenue": "revenue",
            "costOfRevenue": "cost_of_revenue",
            "grossProfit": "gross_profit",
            "researchAndDevelopmentExpenses": "research_and_development",
            "generalAndAdministrativeExpenses": "general_and_administrative",
            "sellingAndMarketingExpenses": "selling_and_marketing",
            "sellingGeneralAndAdministrativeExpenses": "selling_general_and_administrative",
            "operatingExpenses": "operating_expenses",
            "operatingIncome": "operating_income",
            "interestExpense": "interest_expense",
            "interestIncome": "interest_income",
            "incomeBeforeTax": "income_before_tax",
            "incomeTaxExpense": "income_tax_expense",
            "netIncome": "net_income",
            "ebitda": "ebitda",
            "depreciationAndAmortization": "depreciation_and_amortization",
            "weightedAverageShsOut": "weighted_average_shares_outstanding",
            "weightedAverageShsOutDil": "weighted_average_shares_outstanding_diluted",
            "eps": "eps",
            "epsDiluted": "eps_diluted",
        },
        "BS": {
            "totalAssets": "total_assets",
            "totalLiabilities": "total_liabilities",
            "totalStockholdersEquity": "total_stockholders_equity",
            "cashAndCashEquivalents": "cash_and_cash_equivalents",
            "cashAndShortTermInvestments": "cash_and_short_term_investments",
            "inventory": "inventory",
            "accountsReceivables": "accounts_receivable",
            "netReceivables": "accounts_receivable",
            "accountPayables": "accounts_payable",
            "accountsPayables": "accounts_payable",
            "shortTermDebt": "short_term_debt",
            "longTermDebt": "longTermDebt",
            "longTermDebtNoncurrent": "long_term_debt_noncurrent",
            "totalDebt": "total_debt",
            "propertyPlantEquipmentNet": "property_plant_equipment_net",
            "netPPE": "property_plant_equipment_net",
            "goodwill": "goodwill",
            "intangibleAssets": "intangible_assets",
        },
        "CF": {
            "operatingCashFlow": "operating_cash_flow",
            "capitalExpenditure": "capital_expenditure",
            "freeCashFlow": "free_cash_flow",
            "dividendsPaid": "dividends_paid",
            "stockRepurchases": "stock_repurchases",
            "repurchaseOfCommonStock": "stock_repurchases",
            "commonStockRepurchased": "stock_repurchases",
            "depreciationAndAmortization": "depreciation_and_amortization",
            "netCashFlowFromInvestingActivities": "investing_cash_flow",
            "netCashFlowFromFinancingActivities": "financing_cash_flow",
        },
    }
    
    # Step 5: Build financials_by_statement structure
    financials_by_statement: Dict[str, Dict[str, Dict[str, float]]] = {
        "IS": {},
        "BS": {},
        "CF": {},
        "SHARES": {},
    }
    
    # Helper function to get period_end from statement
    def get_period_end(stmt: Dict[str, Any]) -> Optional[str]:
        date_str = stmt.get("date") or stmt.get("calendarYear")
        if date_str:
            if isinstance(date_str, str) and len(date_str) == 4:
                return f"{date_str}-12-31"
            return str(date_str)
        return None
    
    # Process income statements
    for stmt in income_statements:
        period_end = get_period_end(stmt)
        if not period_end or period_end not in periods:
            continue
        
        if period_end not in financials_by_statement["IS"]:
            financials_by_statement["IS"][period_end] = {}
        
        for fmp_field, tag in FMP_TO_TAG_MAPPING["IS"].items():
            value = stmt.get(fmp_field)
            if value is not None:
                try:
                    financials_by_statement["IS"][period_end][tag] = float(value)
                except (ValueError, TypeError):
                    pass
    
    # Process balance sheets
    for stmt in balance_sheets:
        period_end = get_period_end(stmt)
        if not period_end or period_end not in periods:
            continue
        
        if period_end not in financials_by_statement["BS"]:
            financials_by_statement["BS"][period_end] = {}
        
        for fmp_field, tag in FMP_TO_TAG_MAPPING["BS"].items():
            value = stmt.get(fmp_field)
            if value is not None:
                try:
                    financials_by_statement["BS"][period_end][tag] = float(value)
                except (ValueError, TypeError):
                    pass
    
    # Process cash flows
    for stmt in cash_flows:
        period_end = get_period_end(stmt)
        if not period_end or period_end not in periods:
            continue
        
        if period_end not in financials_by_statement["CF"]:
            financials_by_statement["CF"][period_end] = {}
        
        for fmp_field, tag in FMP_TO_TAG_MAPPING["CF"].items():
            value = stmt.get(fmp_field)
            if value is not None:
                try:
                    financials_by_statement["CF"][period_end][tag] = float(value)
                except (ValueError, TypeError):
                    pass
    
    # Extract share data if available
    for stmt in income_statements:
        period_end = get_period_end(stmt)
        if not period_end or period_end not in periods:
            continue
        
        if period_end not in financials_by_statement["SHARES"]:
            financials_by_statement["SHARES"][period_end] = {}
        
        shares = stmt.get("weightedAverageShsOutDil") or stmt.get("weightedAverageShsOut")
        if shares is not None:
            try:
                financials_by_statement["SHARES"][period_end]["diluted_shares_outstanding"] = float(shares)
            except (ValueError, TypeError):
                pass
    
    logger.info("Successfully fetched and normalized FMP data for %s: %d periods", ticker_upper, len(periods))
    
    return {
        "ticker": ticker_upper,
        "cik": None,  # FMP doesn't provide CIK
        "name": company_name,
        "taxonomy": "fmp",
        "financials": financials_by_statement,
        "periods": periods,
        "raw_submissions": {},  # Empty for FMP
        "raw_facts": {
            "income_statements": income_statements,
            "balance_sheets": balance_sheets,
            "cash_flows": cash_flows,
            "quote": quote if quote else {},
        },
    }

