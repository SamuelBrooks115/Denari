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
    "RevenueFromContractWithCustomerExcludingAssessedTax": "revenue",
    "SalesRevenueNet": "revenue",
    "Revenues": "revenue",
    "Revenue": "revenue",
    "CostOfGoodsAndServicesSold": "cogs",
    "CostOfRevenue": "cogs",
    "CostOfSales": "cogs",
    "CostOfGoodsSold": "cogs",
    "GrossProfit": "gross_profit",
    "OperatingExpenses": "operating_expense",
    "TotalOperatingExpenses": "operating_expense",
    "OperatingCosts": "operating_expense",
    "ResearchAndDevelopmentExpense": "research_and_development",
    "ResearchAndDevelopmentCosts": "research_and_development",
    "SellingGeneralAndAdministrativeExpense": "selling_general_administrative",
    "OperatingIncomeLoss": "operating_income",
    "OperatingProfit": "operating_income",
    "OperatingProfitLoss": "operating_income",
    "OperatingIncome": "operating_income",
    "InterestExpense": "interest_expense",
    "InterestExpenseDebt": "interest_expense",
    "InterestAndDebtExpense": "interest_expense",
    "DepreciationDepletionAndAmortization": "depreciation_amortization",
    "DepreciationAndAmortization": "depreciation_amortization",
    "Depreciation": "depreciation_amortization",
    "AmortizationOfIntangibleAssets": "depreciation_amortization",
    "NonoperatingIncomeExpense": "nonoperating_income",
    "OtherIncomeExpense": "nonoperating_income",
    "OtherNonoperatingIncomeExpense": "nonoperating_income",
    "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest": "pretax_income",
    "IncomeBeforeTax": "pretax_income",
    "IncomeTaxExpenseBenefit": "income_tax",
    "IncomeTaxExpense": "income_tax",
    "ProvisionForIncomeTaxes": "income_tax",
    "NetIncomeLoss": "net_income",
    "ProfitLoss": "net_income",
    "NetIncome": "net_income",
    "NetEarnings": "net_income",
    # Cash Flow
    "NetCashProvidedByUsedInOperatingActivities": "cfo",
    "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations": "cfo",
    "NetCashFlowsFromUsedInOperatingActivities": "cfo",
    "NetCashProvidedByUsedInInvestingActivities": "cfi",
    "NetCashFlowsFromUsedInInvestingActivities": "cfi",
    "NetCashProvidedByUsedInFinancingActivities": "cff",
    "NetCashFlowsFromUsedInFinancingActivities": "cff",
    "PaymentsToAcquirePropertyPlantAndEquipment": "capex",
    "PurchasesOfPropertyAndEquipment": "capex",
    "CapitalExpenditures": "capex",
    "PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities": "capex",
    "StockBasedCompensation": "stock_based_compensation",
    "ShareBasedCompensation": "stock_based_compensation",
    "StockBasedCompensationAndBenefits": "stock_based_compensation",
    "ChangesInOperatingAssetsAndLiabilitiesNet": "working_capital_changes",
    "ChangesInWorkingCapital": "working_capital_changes",
    "IncreaseDecreaseInOperatingCapital": "working_capital_changes",
    "PaymentsOfDividends": "dividends_paid",
    "CashDividendsPaid": "dividends_paid",
    "DividendsPaid": "dividends_paid",
    "ProceedsFromIssuanceOfLongTermDebt": "debt_issued",
    "ProceedsFromDebt": "debt_issued",
    "IssuanceOfDebtSecurities": "debt_issued",
    "RepaymentsOfLongTermDebt": "debt_repaid",
    "RepaymentsOfDebt": "debt_repaid",
    "PaymentsOfDebtPrincipal": "debt_repaid",
    "PaymentsForRepurchaseOfCommonStock": "share_repurchases",
    "PurchaseOfTreasuryStock": "share_repurchases",
    "StockRepurchased": "share_repurchases",
    # Balance Sheet
    "Assets": "total_assets",
    "TotalAssets": "total_assets",
    "AssetsCurrent": "current_assets",
    "CurrentAssets": "current_assets",
    "CashAndCashEquivalentsAtCarryingValue": "cash_and_equivalents",
    "CashAndCashEquivalents": "cash_and_equivalents",
    "CashCashEquivalentsAndShortTermInvestments": "cash_and_equivalents",
    "ShortTermInvestments": "ShortTermInvestments",
    "AccountsReceivableNetCurrent": "accounts_receivable",
    "ReceivablesNetCurrent": "accounts_receivable",
    "AccountsReceivableNet": "accounts_receivable",
    "TradeAndOtherReceivablesCurrent": "accounts_receivable",
    "InventoryNet": "inventory",
    "Inventories": "inventory",
    "Inventory": "inventory",
    "PropertyPlantAndEquipmentNet": "ppe_net",
    "PropertyPlantAndEquipment": "ppe_net",
    "Goodwill": "goodwill",
    "IntangibleAssetsNetExcludingGoodwill": "intangible_assets",
    "FiniteLivedIntangibleAssetsNet": "intangible_assets",
    "OtherIntangibleAssets": "intangible_assets",
    "IntangibleAssetsNet": "intangible_assets",
    "Liabilities": "total_liabilities",
    "TotalLiabilities": "total_liabilities",
    "LiabilitiesCurrent": "current_liabilities",
    "CurrentLiabilities": "current_liabilities",
    "AccountsPayableCurrent": "accounts_payable",
    "AccountsPayable": "accounts_payable",
    "TradeAndOtherPayablesCurrent": "accounts_payable",
    "LongTermDebtNoncurrent": "long_term_debt",
    "LongTermDebt": "long_term_debt",
    "DebtLongtermAndShorttermCombinedAmount": "long_term_debt",
    "NoncurrentBorrowings": "long_term_debt",
    "StockholdersEquity": "shareholders_equity",
    "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest": "shareholders_equity",
    "Equity": "shareholders_equity",
    "ShareholdersEquity": "shareholders_equity",
    "RetainedEarningsAccumulatedDeficit": "RetainedEarnings",
    "RetainedEarningsAccumulated": "RetainedEarnings",
    # Share Data
    "WeightedAverageNumberOfSharesOutstandingBasic": "shares_basic",
    "SharesOutstandingBasic": "shares_basic",
    "CommonStockSharesOutstanding": "shares_basic",
    "WeightedAverageNumberOfDilutedSharesOutstanding": "shares_diluted",
    "SharesOutstandingDiluted": "shares_diluted",
    "CommonStockSharesOutstandingDiluted": "shares_diluted",
    "EarningsPerShareBasic": "eps_basic",
    "EPSBasic": "eps_basic",
    "EarningsPerShareDiluted": "eps_diluted",
    "EPSDiluted": "eps_diluted",
    "CommonStockIssued": "shares_outstanding",
}

CANON_IFRS: Dict[str, str] = {
    # Income Statement
    "Revenue": "revenue",
    "SalesRevenueNet": "revenue",
    "Revenues": "revenue",
    "CostOfSales": "cogs",
    "CostOfGoodsAndServicesSold": "cogs",
    "CostOfRevenue": "cogs",
    "GrossProfit": "gross_profit",
    "OperatingExpenses": "operating_expense",
    "TotalOperatingExpenses": "operating_expense",
    "ResearchAndDevelopmentExpense": "research_and_development",
    "AdministrativeExpense": "selling_general_administrative",
    "SellingExpense": "selling_general_administrative",
    "OperatingProfitLoss": "operating_income",
    "OperatingIncomeLoss": "operating_income",
    "InterestExpense": "interest_expense",
    "DepreciationDepletionAndAmortization": "depreciation_amortization",
    "DepreciationAndAmortization": "depreciation_amortization",
    "NonoperatingIncomeExpense": "nonoperating_income",
    "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest": "pretax_income",
    "IncomeBeforeTax": "pretax_income",
    "IncomeTaxExpense": "income_tax",
    "ProfitLoss": "net_income",
    "NetIncomeLoss": "net_income",
    # Cash Flow
    "NetCashFlowsFromUsedInOperatingActivities": "cfo",
    "NetCashFlowsFromUsedInInvestingActivities": "cfi",
    "NetCashFlowsFromUsedInFinancingActivities": "cff",
    "PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities": "capex",
    "PaymentsToAcquirePropertyPlantAndEquipment": "capex",
    # Balance Sheet
    "Assets": "total_assets",
    "CurrentAssets": "current_assets",
    "CashAndCashEquivalents": "cash_and_equivalents",
    "ShorttermInvestments": "ShortTermInvestments",
    "TradeAndOtherReceivablesCurrent": "accounts_receivable",
    "Inventories": "inventory",
    "PropertyPlantAndEquipment": "ppe_net",
    "Goodwill": "goodwill",
    "OtherIntangibleAssets": "intangible_assets",
    "Liabilities": "total_liabilities",
    "CurrentLiabilities": "current_liabilities",
    "TradeAndOtherPayablesCurrent": "accounts_payable",
    "NoncurrentBorrowings": "long_term_debt",
    "Equity": "shareholders_equity",
    "RetainedEarnings": "RetainedEarnings",
}


# Alias tables used when extracting raw values from company facts ----------- #

BS_ALIASES: Mapping[str, List[str]] = {
    "total_assets": ["Assets", "TotalAssets"],
    "current_assets": ["AssetsCurrent", "CurrentAssets"],
    "cash_and_equivalents": [
        "CashAndCashEquivalentsAtCarryingValue",
        "CashAndCashEquivalents",
        "CashCashEquivalentsAndShortTermInvestments",
    ],
    "accounts_receivable": [
        "AccountsReceivableNetCurrent",
        "ReceivablesNetCurrent",
        "AccountsReceivableNet",
        "TradeAndOtherReceivablesCurrent",
    ],
    "inventory": ["InventoryNet", "Inventories", "Inventory"],
    "ppe_net": ["PropertyPlantAndEquipmentNet", "PropertyPlantAndEquipment"],
    "goodwill": ["Goodwill"],
    "intangible_assets": [
        "IntangibleAssetsNetExcludingGoodwill",
        "FiniteLivedIntangibleAssetsNet",
        "OtherIntangibleAssets",
        "IntangibleAssetsNet",
    ],
    "total_liabilities": ["Liabilities", "TotalLiabilities"],
    "current_liabilities": ["LiabilitiesCurrent", "CurrentLiabilities"],
    "accounts_payable": [
        "AccountsPayableCurrent",
        "AccountsPayable",
        "TradeAndOtherPayablesCurrent",
    ],
    "long_term_debt": [
        "LongTermDebtNoncurrent",
        "LongTermDebt",
        "DebtLongtermAndShorttermCombinedAmount",
        "NoncurrentBorrowings",
    ],
    "shareholders_equity": [
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
        "Equity",
        "ShareholdersEquity",
    ],
}

IS_ALIASES: Mapping[str, List[str]] = {
    "revenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "SalesRevenueNet",
        "Revenues",
        "Revenue",
    ],
    "cogs": [
        "CostOfGoodsAndServicesSold",
        "CostOfRevenue",
        "CostOfSales",
        "CostOfGoodsSold",
    ],
    "gross_profit": ["GrossProfit"],
    "operating_expense": [
        "OperatingExpenses",
        "TotalOperatingExpenses",
        "OperatingCosts",
    ],
    "research_and_development": [
        "ResearchAndDevelopmentExpense",
        "ResearchAndDevelopmentCosts",
    ],
    "selling_general_administrative": [
        "SellingGeneralAndAdministrativeExpense",
        "AdministrativeExpense",
        "SellingExpense",
    ],
    "operating_income": [
        "OperatingIncomeLoss",
        "OperatingProfit",
        "OperatingProfitLoss",
        "OperatingIncome",
    ],
    "interest_expense": [
        "InterestExpense",
        "InterestExpenseDebt",
        "InterestAndDebtExpense",
    ],
    "depreciation_amortization": [
        "DepreciationDepletionAndAmortization",
        "DepreciationAndAmortization",
        "Depreciation",
        "AmortizationOfIntangibleAssets",
    ],
    "nonoperating_income": [
        "NonoperatingIncomeExpense",
        "OtherIncomeExpense",
        "OtherNonoperatingIncomeExpense",
    ],
    "pretax_income": [
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
        "IncomeBeforeTax",
    ],
    "income_tax": [
        "IncomeTaxExpenseBenefit",
        "IncomeTaxExpense",
        "ProvisionForIncomeTaxes",
    ],
    "net_income": [
        "NetIncomeLoss",
        "ProfitLoss",
        "NetIncome",
        "NetEarnings",
    ],
}

CF_ALIASES: Mapping[str, List[str]] = {
    "cfo": [
        "NetCashProvidedByUsedInOperatingActivities",
        "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
        "NetCashFlowsFromUsedInOperatingActivities",
    ],
    "cfi": [
        "NetCashProvidedByUsedInInvestingActivities",
        "NetCashFlowsFromUsedInInvestingActivities",
    ],
    "cff": [
        "NetCashProvidedByUsedInFinancingActivities",
        "NetCashFlowsFromUsedInFinancingActivities",
    ],
    "capex": [
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PurchasesOfPropertyAndEquipment",
        "CapitalExpenditures",
        "PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities",
    ],
    "stock_based_compensation": [
        "StockBasedCompensation",
        "ShareBasedCompensation",
        "StockBasedCompensationAndBenefits",
    ],
    "working_capital_changes": [
        "ChangesInOperatingAssetsAndLiabilitiesNet",
        "ChangesInWorkingCapital",
        "IncreaseDecreaseInOperatingCapital",
    ],
    "dividends_paid": [
        "PaymentsOfDividends",
        "CashDividendsPaid",
        "DividendsPaid",
    ],
    "debt_issued": [
        "ProceedsFromIssuanceOfLongTermDebt",
        "ProceedsFromDebt",
        "IssuanceOfDebtSecurities",
    ],
    "debt_repaid": [
        "RepaymentsOfLongTermDebt",
        "RepaymentsOfDebt",
        "PaymentsOfDebtPrincipal",
    ],
    "share_repurchases": [
        "PaymentsForRepurchaseOfCommonStock",
        "PurchaseOfTreasuryStock",
        "StockRepurchased",
    ],
}

SHARE_ALIASES: Mapping[str, List[str]] = {
    "shares_basic": [
        "WeightedAverageNumberOfSharesOutstandingBasic",
        "SharesOutstandingBasic",
        "CommonStockSharesOutstanding",
    ],
    "shares_diluted": [
        "WeightedAverageNumberOfDilutedSharesOutstanding",
        "SharesOutstandingDiluted",
        "CommonStockSharesOutstandingDiluted",
    ],
    "eps_basic": [
        "EarningsPerShareBasic",
        "EPSBasic",
    ],
    "eps_diluted": [
        "EarningsPerShareDiluted",
        "EPSDiluted",
    ],
    "shares_outstanding": [
        "CommonStockSharesOutstanding",
        "SharesOutstanding",
        "CommonStockIssued",
    ],
}

DERIVED_SECTION = {
    "gross_profit": ("revenue", "cogs"),
    "fcf": ("cfo", "capex"),
}


def get_canonical_map(taxonomy: str) -> Dict[str, str]:
    """Return canonical mapping for the provided taxonomy."""
    taxonomy_lower = (taxonomy or "").lower()
    if taxonomy_lower == "us-gaap":
        return CANON_US_GAAP
    if taxonomy_lower == "ifrs-full":
        return CANON_IFRS
    raise ValueError(f"Unsupported taxonomy '{taxonomy}'.")

