"""
Canonical mappings for XBRL normalization.

These mappings are derived from the standalone research script and adapted for
re-use within the ingestion service. They should be expanded over time as more
coverage is required.
"""

from __future__ import annotations

from typing import Dict, List, Mapping

# Canonical tags representing Denari's internal schema --------------------- #

CANON_US_GAAP: Dict[str, str] = {
    # Income Statement
    "RevenueFromContractWithCustomerExcludingAssessedTax": "Revenue",
    "SalesRevenueNet": "Revenue",
    "Revenues": "Revenue",
    "CostOfGoodsAndServicesSold": "COGS",
    "CostOfRevenue": "COGS",
    "GrossProfit": "GrossProfit",
    "ResearchAndDevelopmentExpense": "R&D",
    "SellingGeneralAndAdministrativeExpense": "SG&A",
    "OperatingIncomeLoss": "OperatingIncome",
    "IncomeTaxExpenseBenefit": "TaxExpense",
    "NetIncomeLoss": "NetIncome",
    "ProfitLoss": "NetIncome",
    # Cash Flow
    "NetCashProvidedByUsedInOperatingActivities": "CFO",
    "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations": "CFO",
    "PaymentsToAcquirePropertyPlantAndEquipment": "CapEx",
    "PurchasesOfPropertyAndEquipment": "CapEx",
    "CapitalExpenditures": "CapEx",
    "NetCashProvidedByUsedInInvestingActivities": "CFI",
    "NetCashProvidedByUsedInFinancingActivities": "CFF",
    # Balance Sheet
    "Assets": "Assets",
    "AssetsCurrent": "AssetsCurrent",
    "CashAndCashEquivalentsAtCarryingValue": "CashAndCashEquivalents",
    "CashCashEquivalentsAndShortTermInvestments": "CashAndShortTermInvestments",
    "ShortTermInvestments": "ShortTermInvestments",
    "AccountsReceivableNetCurrent": "AR",
    "ReceivablesNetCurrent": "AR",
    "InventoryNet": "Inventory",
    "PropertyPlantAndEquipmentNet": "PPENet",
    "Goodwill": "Goodwill",
    "IntangibleAssetsNetExcludingGoodwill": "IntangiblesNet",
    "FiniteLivedIntangibleAssetsNet": "IntangiblesNet",
    "Liabilities": "Liabilities",
    "LiabilitiesCurrent": "LiabilitiesCurrent",
    "AccountsPayableCurrent": "AP",
    "LongTermDebtNoncurrent": "LongTermDebt",
    "StockholdersEquity": "Equity",
    "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest": "Equity",
    "RetainedEarningsAccumulatedDeficit": "RetainedEarnings",
    "RetainedEarningsAccumulated": "RetainedEarnings",
}

CANON_IFRS: Dict[str, str] = {
    # Income Statement
    "Revenue": "Revenue",
    "CostOfSales": "COGS",
    "GrossProfit": "GrossProfit",
    "ResearchAndDevelopmentExpense": "R&D",
    "AdministrativeExpense": "SG&A",
    "SellingExpense": "SG&A",
    "OperatingProfitLoss": "OperatingIncome",
    "IncomeTaxExpense": "TaxExpense",
    "ProfitLoss": "NetIncome",
    # Cash Flow
    "NetCashFlowsFromUsedInOperatingActivities": "CFO",
    "NetCashFlowsFromUsedInInvestingActivities": "CFI",
    "NetCashFlowsFromUsedInFinancingActivities": "CFF",
    "PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities": "CapEx",
    # Balance Sheet
    "Assets": "Assets",
    "CurrentAssets": "AssetsCurrent",
    "CashAndCashEquivalents": "CashAndCashEquivalents",
    "ShorttermInvestments": "ShortTermInvestments",
    "TradeAndOtherReceivablesCurrent": "AR",
    "Inventories": "Inventory",
    "PropertyPlantAndEquipment": "PPENet",
    "Goodwill": "Goodwill",
    "OtherIntangibleAssets": "IntangiblesNet",
    "Liabilities": "Liabilities",
    "CurrentLiabilities": "LiabilitiesCurrent",
    "TradeAndOtherPayablesCurrent": "AP",
    "NoncurrentBorrowings": "LongTermDebt",
    "Equity": "Equity",
    "RetainedEarnings": "RetainedEarnings",
}


# Alias tables used when extracting raw values from company facts ----------- #
BS_ALIASES: Mapping[str, List[str]] = {
    "Assets": ["Assets"],
    "AssetsCurrent": ["AssetsCurrent", "CurrentAssets"],
    "CashAndCashEquivalents": [
        "CashAndCashEquivalentsAtCarryingValue",
        "CashAndCashEquivalents",
        "CashCashEquivalentsAndShortTermInvestments",
    ],
    "ShortTermInvestments": ["ShortTermInvestments", "ShorttermInvestments"],
    "AccountsReceivableNetCurrent": [
        "AccountsReceivableNetCurrent",
        "ReceivablesNetCurrent",
        "TradeAndOtherReceivablesCurrent",
    ],
    "InventoryNet": ["InventoryNet", "Inventories"],
    "PropertyPlantAndEquipmentNet": ["PropertyPlantAndEquipmentNet", "PropertyPlantAndEquipment"],
    "Goodwill": ["Goodwill"],
    "IntangibleAssetsNet": [
        "IntangibleAssetsNetExcludingGoodwill",
        "FiniteLivedIntangibleAssetsNet",
        "OtherIntangibleAssets",
    ],
    "Liabilities": ["Liabilities"],
    "LiabilitiesCurrent": ["LiabilitiesCurrent", "CurrentLiabilities"],
    "AccountsPayableCurrent": ["AccountsPayableCurrent", "TradeAndOtherPayablesCurrent"],
    "LongTermDebtNoncurrent": ["LongTermDebtNoncurrent", "NoncurrentBorrowings"],
    "StockholdersEquity": [
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
        "Equity",
    ],
}

IS_ALIASES: Mapping[str, List[str]] = {
    "Revenues": [
        "Revenues",
        "SalesRevenueNet",
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenue",
    ],
    "CostOfRevenue": ["CostOfGoodsAndServicesSold", "CostOfRevenue", "CostOfSales"],
    "GrossProfit": ["GrossProfit"],
    "ResearchAndDevelopmentExpense": ["ResearchAndDevelopmentExpense"],
    "SellingGeneralAndAdministrativeExpense": [
        "SellingGeneralAndAdministrativeExpense",
        "AdministrativeExpense",
        "SellingExpense",
    ],
    "OperatingIncomeLoss": ["OperatingIncomeLoss", "OperatingProfitLoss"],
    "IncomeTaxExpenseBenefit": ["IncomeTaxExpenseBenefit", "IncomeTaxExpense"],
    "NetIncomeLoss": ["NetIncomeLoss", "ProfitLoss"],
}

CF_ALIASES: Mapping[str, List[str]] = {
    "NetCashFromOperatingActivities": [
        "NetCashProvidedByUsedInOperatingActivities",
        "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
        "NetCashFlowsFromUsedInOperatingActivities",
    ],
    "PaymentsToAcquirePropertyPlantAndEquipment": [
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PurchasesOfPropertyAndEquipment",
        "CapitalExpenditures",
        "PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities",
    ],
    "NetCashFromInvestingActivities": [
        "NetCashProvidedByUsedInInvestingActivities",
        "NetCashFlowsFromUsedInInvestingActivities",
    ],
    "NetCashFromFinancingActivities": [
        "NetCashProvidedByUsedInFinancingActivities",
        "NetCashFlowsFromUsedInFinancingActivities",
    ],
}


DERIVED_SECTION = {
    "GrossProfit": ("Revenue", "COGS"),
    "FCF": ("CFO", "CapEx"),
}


def get_canonical_map(taxonomy: str) -> Dict[str, str]:
    """Return canonical mapping for the provided taxonomy."""
    taxonomy_lower = (taxonomy or "").lower()
    if taxonomy_lower == "us-gaap":
        return CANON_US_GAAP
    if taxonomy_lower == "ifrs-full":
        return CANON_IFRS
    raise ValueError(f"Unsupported taxonomy '{taxonomy}'.")





