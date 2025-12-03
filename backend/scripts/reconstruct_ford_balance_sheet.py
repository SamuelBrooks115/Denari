"""
reconstruct_ford_balance_sheet.py — Standalone script to reconstruct Ford's 2024 Balance Sheet from XBRL

This script:
1. Fetches Ford's XBRL data from EDGAR
2. Extracts all balance sheet items for FY 2024
3. Organizes them into Assets, Liabilities, and Equity
4. Exports to a structured JSON file

Usage:
    python scripts/reconstruct_ford_balance_sheet.py --output outputs/ford_2024_balance_sheet.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

# Import necessary modules
import sys
from pathlib import Path as PathLib

# Add parent directory to path to import app modules
sys.path.insert(0, str(PathLib(__file__).parent.parent))

from app.services.ingestion.clients import EdgarClient
from app.services.ingestion.xbrl.utils import flatten_units, parse_date
from app.core.logging import get_logger

logger = get_logger(__name__)

# Ford Motor Company constants
FORD_CIK = 37996
FORD_TICKER = "F"
FORD_2024_REPORT_DATE = "2024-12-31"

# Balance Sheet tag keywords (from structured_output.py)
BS_KEYWORDS = [
    "asset",
    "liabilit",
    "equity",
    "shareholder",
    "stockholder",
    "capital",
    "debt",
    "borrow",
    "notes payable",
    "loan",
    "credit facility",
    "unsecured",
    "secured",
    "receivable",
    "payable",
    "inventory",
    "property, plant and equipment",
    "propertyplantandequipment",
    "ppe",
    "goodwill",
    "intangible",
    "deferred tax",
    "retained earnings",
    "accumulated other comprehensive",
    "cash",
    "marketable",
    "investment",
]

# Standard balance sheet tag allowlist
BS_ALLOWLIST = {
    # Assets
    "Assets",
    "AssetsCurrent",
    "AssetsNoncurrent",
    "CashAndCashEquivalentsAtCarryingValue",
    "CashCashEquivalentsAndShortTermInvestments",
    "ShortTermInvestments",
    "MarketableSecuritiesCurrent",
    "AccountsReceivableNetCurrent",
    "ReceivablesNetCurrent",
    "Inventories",
    "InventoryNet",
    "PrepaidExpensesAndOtherCurrentAssets",
    "OtherAssetsCurrent",
    "PropertyPlantAndEquipmentNet",
    "Goodwill",
    "IntangibleAssetsNetExcludingGoodwill",
    "FiniteLivedIntangibleAssetsNet",
    "OtherAssetsNoncurrent",
    
    # Liabilities
    "Liabilities",
    "LiabilitiesCurrent",
    "LiabilitiesNoncurrent",
    "AccountsPayableCurrent",
    "AccruedLiabilitiesCurrent",
    "OtherLiabilitiesCurrent",
    "ShortTermBorrowings",
    "ShortTermDebt",
    "CommercialPaper",
    "DebtCurrent",
    "DebtNoncurrent",
    "LongTermDebtCurrent",
    "LongTermDebtNoncurrent",
    "LongTermDebt",
    "LongTermDebtAndCapitalLeaseObligationsCurrent",
    "LongTermDebtAndCapitalLeaseObligationsNoncurrent",
    "LongTermDebtAndFinanceLeaseObligationsCurrent",
    "LongTermDebtAndFinanceLeaseObligationsNoncurrent",
    "NotesPayableCurrent",
    "NotesPayableNoncurrent",
    "UnsecuredDebtCurrent",
    "UnsecuredLongTermDebt",
    "SecuredDebtCurrent",
    "SecuredLongTermDebt",
    "CurrentPortionOfLongTermDebt",
    "DeferredTaxLiabilitiesNoncurrent",
    "OtherLiabilitiesNoncurrent",
    
    # Equity
    "StockholdersEquity",
    "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    "Equity",
    "RetainedEarningsAccumulatedDeficit",
    "RetainedEarningsAccumulated",
    "AccumulatedOtherComprehensiveIncomeLossNetOfTax",
    "CommonStockValue",
    "AdditionalPaidInCapital",
    "TreasuryStockValue",
}


def is_balance_sheet_tag(tag: str, label: str) -> bool:
    """Check if a tag/label represents a balance sheet item."""
    tag_lower = tag.lower()
    label_lower = label.lower()
    
    # Check allowlist first
    if tag in BS_ALLOWLIST:
        return True
    
    # Check keywords
    for keyword in BS_KEYWORDS:
        if keyword in tag_lower or keyword in label_lower:
            return True
    
    return False


def is_instant_record(record: Dict[str, Any]) -> bool:
    """Check if a record is an instant (balance sheet) record."""
    return record.get("start") is None or record.get("start") == record.get("end")


def select_consolidated_fact(records: List[Dict[str, Any]], report_date: str) -> Optional[Dict[str, Any]]:
    """
    Select the best consolidated fact from multiple records.
    Prefers dimensionless (consolidated) facts over dimensional ones.
    """
    # Filter to records matching the report date
    matching = [r for r in records if r.get("end") == report_date and is_instant_record(r)]
    
    if not matching:
        return None
    
    # Prefer records without dimensions (consolidated)
    dimensionless = [r for r in matching if not r.get("dimensions")]
    
    if dimensionless:
        # If multiple dimensionless, pick the one with largest magnitude
        return max(dimensionless, key=lambda r: abs(float(r.get("val", 0))))
    
    # If no dimensionless, pick largest magnitude from dimensional
    return max(matching, key=lambda r: abs(float(r.get("val", 0))))


def extract_balance_sheet_items(
    us_gaap: Dict[str, Any],
    report_date: str,
) -> List[Dict[str, Any]]:
    """
    Extract all balance sheet items from XBRL data for a given report date.
    
    Returns list of balance sheet line items with:
    - tag: XBRL tag name
    - label: Human-readable label
    - value: Numeric value
    - unit: Unit (typically USD)
    - context: Context information (consolidated vs segment)
    """
    balance_sheet_items: List[Dict[str, Any]] = []
    
    for tag, tag_data in us_gaap.items():
        label = tag_data.get("label") or tag_data.get("description") or tag
        
        # Check if this is a balance sheet tag
        if not is_balance_sheet_tag(tag, label):
            continue
        
        # Get units (prefer USD)
        units = tag_data.get("units", {})
        if not isinstance(units, dict):
            continue
        
        # Flatten units to get all records
        flattened = flatten_units(units)
        
        # Select best consolidated fact for this report date
        selected = select_consolidated_fact(flattened, report_date)
        
        if not selected:
            continue
        
        # Extract value
        val = selected.get("val")
        if val is None:
            continue
        
        try:
            value = float(val)
        except (ValueError, TypeError):
            continue
        
        # Determine context
        dimensions = selected.get("dimensions", {})
        if dimensions:
            # Check for segment information
            segment_dim = dimensions.get("us-gaap:ConsolidationItemsAxis", {})
            if segment_dim:
                segment_value = segment_dim.get("value", "")
                context = f"Segment: {segment_value}"
            else:
                context = "Dimensional (may include segments)"
        else:
            context = "Consolidated"
        
        # Get unit
        unit = selected.get("_unit") or "USD"
        
        balance_sheet_items.append({
            "tag": tag,
            "label": label,
            "value": value,
            "unit": unit,
            "context": context,
            "report_date": report_date,
        })
    
    return balance_sheet_items


def is_subtotal_or_total(tag: str, label: str) -> bool:
    """Check if a tag/label represents a subtotal or total (should not be summed)."""
    tag_lower = tag.lower()
    label_lower = label.lower()
    
    # Exact total tags (these are the main totals)
    exact_totals = ["assets", "liabilities", "equity", "stockholdersequity"]
    if tag_lower in exact_totals:
        return True
    
    # Subtotal tags (these are subtotals that sum other items)
    subtotal_tags = [
        "assetscurrent",
        "assetsnoncurrent",
        "noncurrentassets",
        "liabilitiescurrent",
        "liabilitiesnoncurrent",
        "noncurrentliabilities",
    ]
    if tag_lower in subtotal_tags:
        return True
    
    # Check for "Total" prefix/suffix (but allow specific line items)
    if "total" in tag_lower or "total" in label_lower:
        # Allow specific line items that happen to have "total" in name
        if any(specific in tag_lower for specific in [
            "totaldebt", "totalassets", "totalliabilities",
            "totalrevenue", "totalcost",  # IS items, shouldn't appear in BS
        ]):
            # Check if it's actually a total tag
            if tag_lower in exact_totals:
                return True
            # Otherwise, it's likely a line item
            return False
        # If it has "total" and matches a subtotal pattern, exclude it
        if any(st in tag_lower for st in subtotal_tags):
            return True
        # Generic "total" in name likely means it's a total
        return True
    
    return False


def categorize_balance_sheet_items(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Categorize balance sheet items into Assets, Liabilities, and Equity.
    Excludes subtotals/totals to avoid double-counting.
    
    Returns structured dictionary with sections and totals.
    """
    assets: List[Dict[str, Any]] = []
    liabilities: List[Dict[str, Any]] = []
    equity: List[Dict[str, Any]] = []
    
    # Track totals separately
    assets_total: Optional[float] = None
    liabilities_total: Optional[float] = None
    equity_total: Optional[float] = None
    
    for item in items:
        tag = item["tag"]
        label = item["label"]
        tag_lower = tag.lower()
        label_lower = label.lower()
        
        # Check if this is a total/subtotal
        if is_subtotal_or_total(tag, label):
            # Store totals but don't include in line items
            if tag_lower == "assets":
                assets_total = item["value"]
            elif tag_lower == "liabilities":
                liabilities_total = item["value"]
            elif tag_lower in ["equity", "stockholdersequity"]:
                equity_total = item["value"]
            continue  # Skip totals in line items
        
        # Categorize line items
        if any(kw in tag_lower or kw in label_lower for kw in ["asset", "cash", "receivable", "inventory", "ppe", "goodwill", "intangible", "investment"]):
            if "liabilit" not in tag_lower and "liabilit" not in label_lower:
                assets.append(item)
        elif any(kw in tag_lower or kw in label_lower for kw in ["liabilit", "debt", "payable", "accrued", "borrowing", "lease"]):
            if "equity" not in tag_lower and "equity" not in label_lower:
                liabilities.append(item)
        elif any(kw in tag_lower or kw in label_lower for kw in ["equity", "stockholder", "retained", "capital", "treasury"]):
            equity.append(item)
        else:
            # Default categorization based on common patterns
            if "asset" in tag_lower or "asset" in label_lower:
                assets.append(item)
            elif "liabilit" in tag_lower or "liabilit" in label_lower:
                liabilities.append(item)
            elif "equity" in tag_lower or "equity" in label_lower:
                equity.append(item)
    
    # Sort by absolute value (largest first)
    assets.sort(key=lambda x: abs(x["value"]), reverse=True)
    liabilities.sort(key=lambda x: abs(x["value"]), reverse=True)
    equity.sort(key=lambda x: abs(x["value"]), reverse=True)
    
    return {
        "assets": assets,
        "liabilities": liabilities,
        "equity": equity,
        "assets_total": assets_total,
        "liabilities_total": liabilities_total,
        "equity_total": equity_total,
    }


def calculate_totals(categorized: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate totals for each section.
    Uses reported totals if available, otherwise sums line items.
    """
    def sum_items(items: List[Dict[str, Any]]) -> float:
        return sum(item["value"] for item in items)
    
    # Use reported totals if available, otherwise sum line items
    assets_total = categorized.get("assets_total")
    if assets_total is None:
        assets_total = sum_items(categorized["assets"])
    
    liabilities_total = categorized.get("liabilities_total")
    if liabilities_total is None:
        liabilities_total = sum_items(categorized["liabilities"])
    
    equity_total = categorized.get("equity_total")
    if equity_total is None:
        equity_total = sum_items(categorized["equity"])
    
    # Calculate check: Assets should equal Liabilities + Equity
    calculated_equity = assets_total - liabilities_total
    reconciliation_diff = equity_total - calculated_equity
    
    # Also calculate sum of line items for comparison
    assets_sum = sum_items(categorized["assets"])
    liabilities_sum = sum_items(categorized["liabilities"])
    equity_sum = sum_items(categorized["equity"])
    
    return {
        "assets_total": assets_total,
        "liabilities_total": liabilities_total,
        "equity_total": equity_total,
        "assets_sum_of_items": assets_sum,
        "liabilities_sum_of_items": liabilities_sum,
        "equity_sum_of_items": equity_sum,
        "calculated_equity": calculated_equity,
        "reconciliation_difference": reconciliation_diff,
        "balances": abs(reconciliation_diff) < (abs(assets_total) * 0.01),  # Within 1%
        "uses_reported_totals": (
            categorized.get("assets_total") is not None or
            categorized.get("liabilities_total") is not None or
            categorized.get("equity_total") is not None
        ),
    }


def reconstruct_ford_balance_sheet_2024(
    output_path: Optional[Path] = None,
    use_cached: bool = False,
) -> Dict[str, Any]:
    """
    Main function to reconstruct Ford's 2024 balance sheet from XBRL.
    
    Args:
        output_path: Path to save JSON output (optional)
        use_cached: If True, try to use cached XBRL data from outputs/ford_all_tags_with_amounts.json
    
    Returns:
        Dictionary with complete balance sheet structure
    """
    logger.info(f"Reconstructing Ford's 2024 Balance Sheet (Report Date: {FORD_2024_REPORT_DATE})")
    
    # Try to use cached data first
    us_gaap: Optional[Dict[str, Any]] = None
    
    if use_cached:
        cached_file = Path("outputs/ford_all_tags_with_amounts.json")
        if cached_file.exists():
            logger.info(f"Loading cached XBRL data from {cached_file}")
            try:
                with cached_file.open('r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                    # Try different structures
                    if "facts" in cached_data:
                        facts = cached_data.get("facts", {})
                        us_gaap = facts.get("us-gaap", {})
                    elif "us-gaap" in cached_data:
                        us_gaap = cached_data.get("us-gaap", {})
                    else:
                        # Try tagsByTaxonomy structure
                        tags_by_taxonomy = cached_data.get("tagsByTaxonomy", {})
                        us_gaap = tags_by_taxonomy.get("us-gaap", {})
                    
                    if us_gaap and len(us_gaap) > 0:
                        logger.info(f"Loaded {len(us_gaap)} tags from cache")
                    else:
                        raise ValueError("Could not find us-gaap section in cached data or it is empty")
            except Exception as e:
                logger.warning(f"Failed to load cached data: {e}, fetching from EDGAR")
                us_gaap = None
    
    # Fetch from EDGAR if not using cache or cache failed
    if us_gaap is None:
        logger.info("Fetching XBRL data from EDGAR...")
        client = EdgarClient()
        facts_payload = client.get_company_facts(FORD_CIK)
        facts = facts_payload.get("facts", {})
        us_gaap = facts.get("us-gaap", {})
        
        if not us_gaap:
            raise RuntimeError(f"No 'us-gaap' section found in company facts for CIK {FORD_CIK}")
        
        logger.info(f"Fetched {len(us_gaap)} XBRL tags from EDGAR")
    
    # Extract balance sheet items
    logger.info(f"Extracting balance sheet items for {FORD_2024_REPORT_DATE}...")
    balance_sheet_items = extract_balance_sheet_items(us_gaap, FORD_2024_REPORT_DATE)
    logger.info(f"Found {len(balance_sheet_items)} balance sheet items")
    
    # Categorize items
    logger.info("Categorizing items into Assets, Liabilities, and Equity...")
    categorized = categorize_balance_sheet_items(balance_sheet_items)
    
    # Calculate totals
    totals = calculate_totals(categorized)
    
    # Build final structure
    result = {
        "company": "Ford Motor Company",
        "ticker": FORD_TICKER,
        "cik": FORD_CIK,
        "report_date": FORD_2024_REPORT_DATE,
        "fiscal_year": 2024,
        "currency": "USD",
        "extraction_timestamp": datetime.now(timezone.utc).isoformat(),
        "balance_sheet": {
            "assets": {
                "items": categorized["assets"],
                "total": totals["assets_total"],
                "sum_of_items": totals["assets_sum_of_items"],
                "item_count": len(categorized["assets"]),
            },
            "liabilities": {
                "items": categorized["liabilities"],
                "total": totals["liabilities_total"],
                "sum_of_items": totals["liabilities_sum_of_items"],
                "item_count": len(categorized["liabilities"]),
            },
            "equity": {
                "items": categorized["equity"],
                "total": totals["equity_total"],
                "sum_of_items": totals["equity_sum_of_items"],
                "item_count": len(categorized["equity"]),
            },
        },
        "totals": totals,
        "metadata": {
            "total_items_extracted": len(balance_sheet_items),
            "assets_line_items": len(categorized["assets"]),
            "liabilities_line_items": len(categorized["liabilities"]),
            "equity_line_items": len(categorized["equity"]),
            "reconciliation_passes": totals["balances"],
            "uses_reported_totals": totals["uses_reported_totals"],
        },
    }
    
    # Save to file if output path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Saving balance sheet to {output_path}")
        with output_path.open('w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"[OK] Balance sheet saved to {output_path}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("Ford Motor Company - Balance Sheet (FY 2024)")
    print("=" * 80)
    print(f"Report Date: {FORD_2024_REPORT_DATE}")
    print(f"\nAssets: ${totals['assets_total']:,.0f} ({len(categorized['assets'])} items)")
    print(f"Liabilities: ${totals['liabilities_total']:,.0f} ({len(categorized['liabilities'])} items)")
    print(f"Equity: ${totals['equity_total']:,.0f} ({len(categorized['equity'])} items)")
    print(f"\nReconciliation: Assets = Liabilities + Equity")
    print(f"  ${totals['assets_total']:,.0f} = ${totals['liabilities_total']:,.0f} + ${totals['equity_total']:,.0f}")
    print(f"  Difference: ${totals['reconciliation_difference']:,.0f}")
    
    if totals["balances"]:
        print("  [OK] Balance sheet reconciles (within 1% tolerance)")
    else:
        print(f"  [WARNING] Balance sheet does not reconcile (difference: ${totals['reconciliation_difference']:,.0f})")
    
    print("=" * 80)
    
    return result


def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(
        description="Reconstruct Ford's 2024 Balance Sheet from XBRL data"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="outputs/ford_2024_balance_sheet.json",
        help="Output JSON file path (default: outputs/ford_2024_balance_sheet.json)",
    )
    parser.add_argument(
        "--use-cached",
        action="store_true",
        help="Use cached XBRL data from outputs/ford_all_tags_with_amounts.json if available",
    )
    
    args = parser.parse_args()
    
    try:
        result = reconstruct_ford_balance_sheet_2024(
            output_path=Path(args.output),
            use_cached=args.use_cached,
        )
        print(f"\n[OK] Successfully reconstructed balance sheet with {result['metadata']['total_items_extracted']} items")
    except Exception as e:
        logger.error(f"Error reconstructing balance sheet: {e}", exc_info=True)
        print(f"\n[ERROR] Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

