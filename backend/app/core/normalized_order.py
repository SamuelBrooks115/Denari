"""
normalized_order.py — Canonical ordering for financial statement line items.

Defines the standard order for line items in each financial statement type.
These arrays are used to ensure consistent ordering in structured output.
"""

from typing import List

# Income Statement - ordered from top to bottom
INCOME_STATEMENT_ORDER = [
    "Revenues",
    "Revenue",
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "SalesRevenueNet",
    "CostOfRevenue",
    "CostOfGoodsAndServicesSold",
    "CostOfSales",
    "GrossProfit",
    "ResearchAndDevelopmentExpense",
    "SellingGeneralAndAdministrativeExpense",
    "SellingAndMarketingExpense",
    "GeneralAndAdministrativeExpense",
    "OperatingIncomeLoss",
    "OperatingProfitLoss",
    "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
    "EarningsBeforeInterestAndTaxes",
    "IncomeTaxExpenseBenefit",
    "IncomeTaxExpense",
    "NetIncomeLoss",
    "ProfitLoss",
]

# Balance Sheet - ordered: Assets, Liabilities, Equity
BALANCE_SHEET_ORDER = [
    # Assets - Current
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
    "AssetsCurrent",
    # Assets - Non-current
    "PropertyPlantAndEquipmentNet",
    "Goodwill",
    "IntangibleAssetsNetExcludingGoodwill",
    "FiniteLivedIntangibleAssetsNet",
    "OtherAssetsNoncurrent",
    "AssetsNoncurrent",
    "Assets",
    # Liabilities - Current
    "AccountsPayableCurrent",
    "AccruedLiabilitiesCurrent",
    "OtherLiabilitiesCurrent",
    "ShortTermBorrowings",
    "CommercialPaper",
    "LongTermDebtCurrent",
    "LongTermDebtAndCapitalLeaseObligationsCurrent",
    "LiabilitiesCurrent",
    # Liabilities - Non-current
    "LongTermDebtNoncurrent",
    "LongTermDebtAndCapitalLeaseObligationsNoncurrent",
    "DeferredTaxLiabilitiesNoncurrent",
    "OtherLiabilitiesNoncurrent",
    "LiabilitiesNoncurrent",
    "Liabilities",
    # Equity
    "CommonStockValue",
    "AdditionalPaidInCapital",
    "RetainedEarningsAccumulatedDeficit",
    "RetainedEarningsAccumulated",
    "AccumulatedOtherComprehensiveIncomeLossNetOfTax",
    "TreasuryStockValue",
    "StockholdersEquity",
    "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    "Equity",
]

# Cash Flow Statement - ordered: Operating, Investing, Financing
CASH_FLOW_ORDER = [
    # Operating Activities
    "NetCashProvidedByUsedInOperatingActivities",
    "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
    "DepreciationDepletionAndAmortization",
    "DepreciationAndAmortization",
    "ShareBasedCompensation",
    "DeferredIncomeTaxExpenseBenefit",
    "IncreaseDecreaseInAccountsReceivable",
    "IncreaseDecreaseInInventories",
    "IncreaseDecreaseInAccountsPayable",
    "IncreaseDecreaseInAccruedLiabilities",
    "IncreaseDecreaseInOtherOperatingAssets",
    "IncreaseDecreaseInOtherOperatingLiabilities",
    "AmortizationOfIntangibleAssets",
    "ImpairmentOfIntangibleAssets",
    "ImpairmentOfLongLivedAssetsHeldAndUsed",
    # Investing Activities
    "NetCashProvidedByUsedInInvestingActivities",
    "PaymentsToAcquirePropertyPlantAndEquipment",
    "PaymentsToAcquirePropertyAndEquipment",
    "PurchasesOfPropertyAndEquipment",
    "CapitalExpenditures",
    "ProceedsFromSaleOfPropertyPlantAndEquipment",
    "PaymentsToAcquireBusinessesNetOfCashAcquired",
    "PaymentsToAcquireInvestments",
    "ProceedsFromSaleOfInvestments",
    # Financing Activities
    "NetCashProvidedByUsedInFinancingActivities",
    "ProceedsFromIssuanceOfLongTermDebt",
    "RepaymentsOfLongTermDebt",
    "ProceedsFromIssuanceOfShortTermDebt",
    "RepaymentsOfShortTermDebt",
    "ProceedsFromIssuanceOfCommonStock",
    "PaymentsForRepurchaseOfCommonStock",
    "PaymentsOfDividends",
    "PaymentsOfFinancingCosts",
    "PaymentsForRepurchaseOfEquityInstruments",
    "ProceedsFromStockOptionsExercised",
    # Net Change
    "CashAndCashEquivalentsPeriodIncreaseDecrease",
    "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecrease",
    "EffectOfExchangeRateOnCashAndCashEquivalents",
    "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
]


def get_normalized_order(statement_type: str) -> List[str]:
    """
    Get the normalized order array for a statement type.

    Args:
        statement_type: One of "income_statement", "balance_sheet", "cash_flow_statement"

    Returns:
        List of tag names in canonical order
    """
    mapping = {
        "income_statement": INCOME_STATEMENT_ORDER,
        "balance_sheet": BALANCE_SHEET_ORDER,
        "cash_flow_statement": CASH_FLOW_ORDER,
    }
    return mapping.get(statement_type, [])

