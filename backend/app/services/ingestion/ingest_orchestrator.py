"""
ingest_orchestrator.py — Data Readiness Workflow Orchestrator.

Provides high-level orchestration for:
    * Full S&P 500 historical ingestion
    * Single-company refreshes (e.g., `/companies/{id}/prepare`)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.data.fmp_client import (
    fetch_balance_sheet,
    fetch_cash_flow,
    fetch_income_statement,
    fetch_quote,
)
from app.models.company import Company
from app.services.ingestion.pipelines import SP500IngestionPipeline
from app.services.ingestion.repositories import XbrlRepository


logger = get_logger(__name__)


class IngestOrchestrator:
    """
    Coordinates ingestion workflows using the configured pipeline components.
    """

    def __init__(self, db: Session) -> None:
        self._db = db
        repository = XbrlRepository()  # Uses default db_client from get_db_client()
        self._pipeline = SP500IngestionPipeline(repository=repository)

    # ------------------------------------------------------------------ #
    def run_sp500_backfill(self, years: int = 5) -> Dict[str, Any]:
        logger.info("Starting S&P 500 backfill for %s years.", years)
        result = self._pipeline.ingest_all(years=years)
        logger.info("S&P 500 backfill complete: %s successes, %s errors.", result.get("succeeded", 0), len(result.get("errors", [])))
        return result

    def prepare_company(self, company_id: int, years: int = 5) -> Dict[str, Any]:
        try:
            company = self._db.query(Company).filter(Company.id == company_id).first()
            if not company:
                logger.warning("Company not found: %s", company_id)
                return {"error": "company_not_found"}

            if not company.cik:
                logger.warning("Company missing CIK: %s", company.ticker)
                return {"error": "cik_missing"}

            try:
                cik_int = int(company.cik)
            except ValueError as exc:
                logger.error("Invalid CIK stored for company %s: %s", company.ticker, company.cik)
                raise RuntimeError("Invalid company CIK") from exc

            logger.info("Preparing data for company %s (CIK %s)", company.ticker, company.cik)

            ingestion_result = self._pipeline.ingest_single(
                ticker=company.ticker,
                cik=cik_int,
                years=years,
                company_id=company.id,
            )

            return {
                "company": company.ticker,
                "status": "success",
                "ingestion": ingestion_result,
            }

        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Error in prepare_company: %s", exc)
            raise

    def fetch_fmp_stable_raw(
        self,
        ticker: str,
        limit: int = 3,
        output_dir: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Fetch FMP stable raw data for all three financial statements and save to JSON files.
        
        This method fetches income statement, balance sheet, and cash flow data
        from the FMP /stable API and saves them to JSON files in the output directory.
        
        Args:
            ticker: Company ticker symbol (e.g., "MSFT")
            limit: Number of periods to fetch (default: 3)
            output_dir: Directory to save JSON files (default: backend/downloads)
            
        Returns:
            Dictionary containing:
            - ticker: str
            - status: str ("success" or "error")
            - files: Dict with paths to saved files
            - summary: Dict with counts and most recent period info
            - error: Optional[str] if an error occurred
        """
        ticker_upper = ticker.upper()
        
        # Default output directory
        if output_dir is None:
            # Default to backend/downloads relative to this file
            backend_dir = Path(__file__).parent.parent.parent.parent
            output_dir = backend_dir / "downloads"
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            logger.info(f"=== Fetching FMP Stable Raw Data for {ticker_upper} ===\n")
            
            # Fetch income statement
            logger.info(f"Fetching income statement for {ticker_upper}...")
            income_data = fetch_income_statement(ticker_upper, limit=limit)
            income_file = output_dir / f"{ticker_upper}_income_statement_stable_raw.json"
            with income_file.open("w", encoding="utf-8") as f:
                json.dump(income_data, f, indent=2, ensure_ascii=False)
            logger.info(f"✓ Wrote {len(income_data)} income statement(s) to {income_file.name}")
            
            # Fetch balance sheet
            logger.info(f"Fetching balance sheet for {ticker_upper}...")
            balance_data = fetch_balance_sheet(ticker_upper, limit=limit)
            balance_file = output_dir / f"{ticker_upper}_balance_sheet_stable_raw.json"
            with balance_file.open("w", encoding="utf-8") as f:
                json.dump(balance_data, f, indent=2, ensure_ascii=False)
            logger.info(f"✓ Wrote {len(balance_data)} balance sheet(s) to {balance_file.name}")
            
            # Fetch cash flow
            logger.info(f"Fetching cash flow for {ticker_upper}...")
            cash_flow_data = fetch_cash_flow(ticker_upper, limit=limit)
            cash_flow_file = output_dir / f"{ticker_upper}_cash_flow_stable_raw.json"
            with cash_flow_file.open("w", encoding="utf-8") as f:
                json.dump(cash_flow_data, f, indent=2, ensure_ascii=False)
            logger.info(f"✓ Wrote {len(cash_flow_data)} cash flow statement(s) to {cash_flow_file.name}")
            
            # Fetch quote/price data
            quote_data = None
            quote_file = None
            try:
                logger.info(f"Fetching quote/price data for {ticker_upper}...")
                quote_data = fetch_quote(ticker_upper)
                quote_file = output_dir / f"{ticker_upper}_quote_stable_raw.json"
                with quote_file.open("w", encoding="utf-8") as f:
                    json.dump(quote_data, f, indent=2, ensure_ascii=False)
                logger.info(f"✓ Wrote quote data to {quote_file.name}")
                if quote_data.get("price"):
                    logger.info(f"  Current Price: ${quote_data.get('price', 0):.2f}")
            except Exception as quote_error:
                logger.warning(f"Failed to fetch quote data for {ticker_upper}: {quote_error}")
                quote_data = None
            
            # Build summary
            summary = {
                "income_statements": len(income_data),
                "balance_sheets": len(balance_data),
                "cash_flows": len(cash_flow_data),
            }
            
            # Add quote data to summary if available
            if quote_data:
                summary["quote"] = {
                    "price": quote_data.get("price"),
                    "market_cap": quote_data.get("marketCap"),
                    "volume": quote_data.get("volume"),
                    "change": quote_data.get("change"),
                    "change_percent": quote_data.get("changesPercentage"),
                }
            
            # Add most recent period info if available
            if income_data:
                latest = income_data[0]
                summary["most_recent_period"] = {
                    "date": latest.get("date", "N/A"),
                    "fiscal_year": latest.get("fiscalYear", "N/A"),
                    "period": latest.get("period", "N/A"),
                }
                if latest.get("revenue"):
                    summary["most_recent_period"]["revenue"] = latest.get("revenue")
                if latest.get("netIncome"):
                    summary["most_recent_period"]["net_income"] = latest.get("netIncome")
            
            logger.info("\n=== Fetch Complete ===")
            logger.info(f"✓ Successfully fetched and cached FMP /stable data for {ticker_upper}")
            
            files_dict = {
                "income_statement": str(income_file),
                "balance_sheet": str(balance_file),
                "cash_flow": str(cash_flow_file),
            }
            
            if quote_file:
                files_dict["quote"] = str(quote_file)
            
            return {
                "ticker": ticker_upper,
                "status": "success",
                "files": files_dict,
                "summary": summary,
            }
            
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception(f"Error fetching FMP stable raw data for {ticker_upper}: {exc}")
            return {
                "ticker": ticker_upper,
                "status": "error",
                "error": str(exc),
            }


# Backwards-compatible function -------------------------------------------------------------- #
def prepare_company_data(company_id: int, db: Session, years: int = 5) -> Dict[str, Any]:
    orchestrator = IngestOrchestrator(db)
    return orchestrator.prepare_company(company_id, years=years)


def fetch_fmp_stable_raw_data(
    ticker: str,
    limit: int = 3,
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Standalone function to fetch FMP stable raw data.
    
    This function can be called without creating an IngestOrchestrator instance.
    It directly fetches and saves FMP stable raw data to JSON files.
    
    Args:
        ticker: Company ticker symbol (e.g., "MSFT")
        limit: Number of periods to fetch (default: 3)
        output_dir: Directory to save JSON files (default: backend/downloads)
        
    Returns:
        Dictionary with fetch results (see fetch_fmp_stable_raw for details)
    """
    ticker_upper = ticker.upper()
    
    # Default output directory
    if output_dir is None:
        # Default to backend/downloads relative to this file
        backend_dir = Path(__file__).parent.parent.parent.parent
        output_dir = backend_dir / "downloads"
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        logger.info(f"=== Fetching FMP Stable Raw Data for {ticker_upper} ===\n")
        
        # Fetch income statement
        logger.info(f"Fetching income statement for {ticker_upper}...")
        income_data = fetch_income_statement(ticker_upper, limit=limit)
        income_file = output_dir / f"{ticker_upper}_income_statement_stable_raw.json"
        with income_file.open("w", encoding="utf-8") as f:
            json.dump(income_data, f, indent=2, ensure_ascii=False)
        logger.info(f"✓ Wrote {len(income_data)} income statement(s) to {income_file.name}")
        
        # Fetch balance sheet
        logger.info(f"Fetching balance sheet for {ticker_upper}...")
        balance_data = fetch_balance_sheet(ticker_upper, limit=limit)
        balance_file = output_dir / f"{ticker_upper}_balance_sheet_stable_raw.json"
        with balance_file.open("w", encoding="utf-8") as f:
            json.dump(balance_data, f, indent=2, ensure_ascii=False)
        logger.info(f"✓ Wrote {len(balance_data)} balance sheet(s) to {balance_file.name}")
        
        # Fetch cash flow
        logger.info(f"Fetching cash flow for {ticker_upper}...")
        cash_flow_data = fetch_cash_flow(ticker_upper, limit=limit)
        cash_flow_file = output_dir / f"{ticker_upper}_cash_flow_stable_raw.json"
        with cash_flow_file.open("w", encoding="utf-8") as f:
            json.dump(cash_flow_data, f, indent=2, ensure_ascii=False)
        logger.info(f"✓ Wrote {len(cash_flow_data)} cash flow statement(s) to {cash_flow_file.name}")
        
        # Fetch quote/price data
        quote_data = None
        quote_file = None
        try:
            logger.info(f"Fetching quote/price data for {ticker_upper}...")
            quote_data = fetch_quote(ticker_upper)
            quote_file = output_dir / f"{ticker_upper}_quote_stable_raw.json"
            with quote_file.open("w", encoding="utf-8") as f:
                json.dump(quote_data, f, indent=2, ensure_ascii=False)
            logger.info(f"✓ Wrote quote data to {quote_file.name}")
            if quote_data.get("price"):
                logger.info(f"  Current Price: ${quote_data.get('price', 0):.2f}")
        except Exception as quote_error:
            logger.warning(f"Failed to fetch quote data for {ticker_upper}: {quote_error}")
            quote_data = None
        
        # Build summary
        summary = {
            "income_statements": len(income_data),
            "balance_sheets": len(balance_data),
            "cash_flows": len(cash_flow_data),
        }
        
        # Add quote data to summary if available
        if quote_data:
            summary["quote"] = {
                "price": quote_data.get("price"),
                "market_cap": quote_data.get("marketCap"),
                "volume": quote_data.get("volume"),
                "change": quote_data.get("change"),
                "change_percent": quote_data.get("changesPercentage"),
            }
        
        # Add most recent period info if available
        if income_data:
            latest = income_data[0]
            summary["most_recent_period"] = {
                "date": latest.get("date", "N/A"),
                "fiscal_year": latest.get("fiscalYear", "N/A"),
                "period": latest.get("period", "N/A"),
            }
            if latest.get("revenue"):
                summary["most_recent_period"]["revenue"] = latest.get("revenue")
            if latest.get("netIncome"):
                summary["most_recent_period"]["net_income"] = latest.get("netIncome")
        
        logger.info("\n=== Fetch Complete ===")
        logger.info(f"✓ Successfully fetched and cached FMP /stable data for {ticker_upper}")
        
        files_dict = {
            "income_statement": str(income_file),
            "balance_sheet": str(balance_file),
            "cash_flow": str(cash_flow_file),
        }
        
        if quote_file:
            files_dict["quote"] = str(quote_file)
        
        return {
            "ticker": ticker_upper,
            "status": "success",
            "files": files_dict,
            "summary": summary,
        }
        
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception(f"Error fetching FMP stable raw data for {ticker_upper}: {exc}")
        return {
            "ticker": ticker_upper,
            "status": "error",
            "error": str(exc),
        }
