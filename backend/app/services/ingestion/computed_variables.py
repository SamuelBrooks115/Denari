"""
computed_variables.py — Compute derived DCF variables from core anchors.

Computes required DCF variables using deterministic formulas when direct tags
are absent or low-confidence. Returns computed/proxy status with supporting tags.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Set

from app.core.model_role_map import (
    BS_ACCOUNTS_PAYABLE,
    BS_ACCRUED_LIABILITIES,
    BS_AP_AND_ACCRUED,
    BS_DEBT_CURRENT,
    BS_DEBT_NONCURRENT,
    IS_COGS,
    IS_D_AND_A,
    IS_EBITDA,
    IS_GROSS_PROFIT,
    IS_OPERATING_EXPENSE,
    IS_OPERATING_INCOME,
    IS_REVENUE,
)
from app.services.ingestion.core_anchors import AnchorFact, get_latest_period_value


class ComputedVariable:
    """Represents a computed or proxy variable."""
    
    def __init__(
        self,
        variable_name: str,
        model_role: str,
        periods: Dict[str, float],
        status: str,  # "computed" or "proxy"
        supporting_tags: List[str],
        computation_method: str,
        guardrails: List[str],
    ):
        self.variable_name = variable_name
        self.model_role = model_role
        self.periods = periods
        self.status = status
        self.supporting_tags = supporting_tags
        self.computation_method = computation_method
        self.guardrails = guardrails
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "variable_name": self.variable_name,
            "model_role": self.model_role,
            "periods": self.periods,
            "status": self.status,
            "supporting_tags": self.supporting_tags,
            "computation_method": self.computation_method,
            "guardrails": self.guardrails,
        }


def compute_operating_costs(
    anchors: Dict[str, Optional[AnchorFact]],
) -> Optional[ComputedVariable]:
    """
    Compute Operating Costs from anchors.
    
    Primary: OperatingCosts = Revenue - OperatingIncome
    Secondary: OperatingCosts = COGS + SG&A + R&D (if Op Income missing)
    """
    revenue_anchor = anchors.get(IS_REVENUE)
    operating_income_anchor = anchors.get(IS_OPERATING_INCOME)
    cogs_anchor = anchors.get(IS_COGS)
    
    guardrails = []
    supporting_tags = []
    
    # Primary method: Revenue - Operating Income
    if revenue_anchor and operating_income_anchor:
        revenue_periods = revenue_anchor.periods
        op_income_periods = operating_income_anchor.periods
        
        # Compute for each period
        computed_periods = {}
        all_periods = set(revenue_periods.keys()) | set(op_income_periods.keys())
        
        for period in all_periods:
            revenue_val = revenue_periods.get(period)
            op_income_val = op_income_periods.get(period)
            
            if revenue_val is not None and op_income_val is not None:
                computed_val = revenue_val - op_income_val
                if computed_val > 0:  # Sanity check
                    computed_periods[period] = computed_val
        
        if computed_periods:
            return ComputedVariable(
                variable_name="Operating Costs / Margin",
                model_role=IS_OPERATING_EXPENSE,
                periods=computed_periods,
                status="computed",
                supporting_tags=[revenue_anchor.tag, operating_income_anchor.tag],
                computation_method="Revenue - Operating Income",
                guardrails=guardrails,
            )
        else:
            guardrails.append("Could not compute for any period: missing Revenue or Operating Income values")
    
    # Secondary method: COGS only (if we have it but no Operating Income)
    if cogs_anchor and not operating_income_anchor:
        guardrails.append("Using COGS as proxy for Operating Costs (Operating Income not available)")
        return ComputedVariable(
            variable_name="Operating Costs / Margin",
            model_role=IS_OPERATING_EXPENSE,
            periods=cogs_anchor.periods.copy(),
            status="proxy",
            supporting_tags=[cogs_anchor.tag],
            computation_method="COGS (proxy - Operating Income not available)",
            guardrails=guardrails,
        )
    
    return None


def compute_ebitda(
    anchors: Dict[str, Optional[AnchorFact]],
) -> Optional[ComputedVariable]:
    """
    Compute EBITDA from anchors.
    
    Formula: EBITDA = Operating Income + Depreciation & Amortization
    """
    operating_income_anchor = anchors.get(IS_OPERATING_INCOME)
    da_anchor = anchors.get(IS_D_AND_A)
    
    guardrails = []
    
    if not operating_income_anchor:
        guardrails.append("Operating Income anchor missing - cannot compute EBITDA")
        return None
    
    if not da_anchor:
        guardrails.append("Depreciation & Amortization anchor missing - cannot compute EBITDA")
        return None
    
    op_income_periods = operating_income_anchor.periods
    da_periods = da_anchor.periods
    
    computed_periods = {}
    all_periods = set(op_income_periods.keys()) | set(da_periods.keys())
    
    for period in all_periods:
        op_income_val = op_income_periods.get(period)
        da_val = da_periods.get(period)
        
        if op_income_val is not None and da_val is not None:
            computed_periods[period] = op_income_val + da_val
    
    if not computed_periods:
        guardrails.append("Could not compute for any period: missing values")
        return None
    
    return ComputedVariable(
        variable_name="EBITDA Margins / Costs",
        model_role=IS_EBITDA,
        periods=computed_periods,
        status="computed",
        supporting_tags=[operating_income_anchor.tag, da_anchor.tag],
        computation_method="Operating Income + Depreciation & Amortization",
        guardrails=guardrails,
    )


def _collect_candidates_by_role(
    line_items: List[Dict[str, Any]],
    roles: Tuple[str, ...],
) -> List[Dict[str, Any]]:
    """Collect line items matching any of the specified roles."""
    cands: List[Dict[str, Any]] = []
    for li in line_items:
        role = li.get("model_role") or li.get("llm_classification", {}).get("best_fit_role", "")
        if role in roles:
            cands.append(li)
    return cands


def _collect_candidates_by_keywords(
    line_items: List[Dict[str, Any]],
    keywords: Tuple[str, ...],
) -> List[Dict[str, Any]]:
    """Collect line items matching any of the specified keywords in tag or label."""
    cands: List[Dict[str, Any]] = []
    for li in line_items:
        label = (li.get("label") or "").lower()
        tag = (li.get("tag") or "").lower()
        if any(k.lower() in label for k in keywords) or any(k.lower() in tag for k in keywords):
            cands.append(li)
    return cands


def compute_debt_amount_from_normalized(
    normalized: Dict[str, List[Dict[str, Any]]],
    *,
    confidence_threshold: float = 0.80,
) -> Optional[ComputedVariable]:
    """
    Fallback for Debt Amount (WACC debt) from normalized line items.
    
    Formula: TotalDebt = DebtCurrent + DebtNoncurrent
    
    Priority:
      1) Use role-classified candidates: BS_DEBT_CURRENT / BS_DEBT_NONCURRENT
      2) If missing, use keyword candidates (interest-bearing only)
      3) Sum by aligned periods
    
    Args:
        normalized: Normalized statement data with balance_sheet line items
        confidence_threshold: Minimum LLM confidence to accept (default 0.80)
        
    Returns:
        ComputedVariable or None if not computable
    """
    bs_items = normalized.get("balance_sheet", []) or []
    
    # 1) Role-based candidates
    current_roles = (BS_DEBT_CURRENT,)
    noncurrent_roles = (BS_DEBT_NONCURRENT,)
    
    cur_cands = _collect_candidates_by_role(bs_items, current_roles)
    noncur_cands = _collect_candidates_by_role(bs_items, noncurrent_roles)
    
    # Filter out low-confidence LLM-only assignments
    def _is_confident(li: Dict[str, Any]) -> bool:
        llm_conf = li.get("llm_classification", {}).get("confidence")
        # deterministic roles (no llm_conf) are treated as confident
        return (llm_conf is None) or (llm_conf >= confidence_threshold)
    
    cur_cands = [c for c in cur_cands if _is_confident(c)]
    noncur_cands = [c for c in noncur_cands if _is_confident(c)]
    
    # 2) Keyword fallback if roles missing
    # Keep it tight to interest-bearing debt terms
    if not cur_cands:
        cur_cands = _collect_candidates_by_keywords(
            bs_items,
            keywords=(
                "short-term debt",
                "short term debt",
                "current debt",
                "long-term debt current",
                "current portion of long-term debt",
                "short-term borrowings",
                "notes payable current",
                "debt current",
            ),
        )
    
    if not noncur_cands:
        noncur_cands = _collect_candidates_by_keywords(
            bs_items,
            keywords=(
                "long-term debt",
                "long term debt",
                "debt noncurrent",
                "notes payable noncurrent",
                "total long-term debt",
            ),
        )
    
    # If still nothing, we cannot compute
    if not cur_cands and not noncur_cands:
        return None
    
    # 3) Choose best candidate per side (rank by most recent magnitude)
    def _pick_best(cands: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not cands:
            return None
        # Most recent period magnitude heuristic
        def _score(li: Dict[str, Any]) -> float:
            periods = li.get("periods", {}) or {}
            if not periods:
                return 0.0
            # take last period value by sorted date key
            sorted_keys = sorted(periods.keys())
            if not sorted_keys:
                return 0.0
            last_key = sorted_keys[-1]
            val = periods[last_key]
            try:
                return abs(float(val))
            except Exception:
                return 0.0
        
        return sorted(cands, key=_score, reverse=True)[0]
    
    best_cur = _pick_best(cur_cands)
    best_noncur = _pick_best(noncur_cands)
    
    # 4) Align periods and sum
    value_by_period: Dict[str, float] = {}
    supporting_tags: List[str] = []
    
    def _period_map(li: Optional[Dict[str, Any]]) -> Dict[str, float]:
        if not li:
            return {}
        out: Dict[str, float] = {}
        for p, v in (li.get("periods") or {}).items():
            try:
                out[p] = float(v)
            except Exception:
                continue
        return out
    
    cur_map = _period_map(best_cur)
    noncur_map = _period_map(best_noncur)
    
    all_periods = sorted(set(cur_map.keys()) | set(noncur_map.keys()))
    for p in all_periods:
        value_by_period[p] = cur_map.get(p, 0.0) + noncur_map.get(p, 0.0)
    
    if best_cur:
        supporting_tags.append(best_cur.get("tag", ""))
    if best_noncur:
        supporting_tags.append(best_noncur.get("tag", ""))
    
    if not value_by_period:
        return None
    
    # Determine status
    if best_cur and best_noncur:
        status = "computed"
        method = "Debt Current + Debt Noncurrent"
    elif best_cur:
        status = "proxy"
        method = "Debt Current (proxy - Debt Noncurrent not available)"
    else:
        status = "proxy"
        method = "Debt Noncurrent (proxy - Debt Current not available)"
    
    return ComputedVariable(
        variable_name="Debt Amount",
        model_role=BS_DEBT_CURRENT,  # Using current as primary role for validator matching
        periods=value_by_period,
        status=status,
        supporting_tags=supporting_tags,
        computation_method=method,
        guardrails=[],
    )


def compute_debt_amount(
    anchors: Dict[str, Optional[AnchorFact]],
) -> Optional[ComputedVariable]:
    """
    Compute Total Debt Amount from anchors.
    
    Formula: TotalDebt = sum(BS_DEBT_CURRENT anchors) + sum(BS_DEBT_NONCURRENT anchors)
    
    If multiple tags exist per side, sum all confident candidates by period.
    """
    debt_current_anchor = anchors.get(BS_DEBT_CURRENT)
    debt_noncurrent_anchor = anchors.get(BS_DEBT_NONCURRENT)
    
    guardrails = []
    supporting_tags = []
    
    # If we have both, compute sum
    if debt_current_anchor and debt_noncurrent_anchor:
        current_periods = debt_current_anchor.periods
        noncurrent_periods = debt_noncurrent_anchor.periods
        
        computed_periods = {}
        all_periods = set(current_periods.keys()) | set(noncurrent_periods.keys())
        
        for period in all_periods:
            current_val = current_periods.get(period, 0.0)
            noncurrent_val = noncurrent_periods.get(period, 0.0)
            
            if current_val is not None and noncurrent_val is not None:
                computed_periods[period] = current_val + noncurrent_val
        
        if computed_periods:
            return ComputedVariable(
                variable_name="Debt Amount",
                model_role=BS_DEBT_CURRENT,  # Using current as primary role for validator matching
                periods=computed_periods,
                status="computed",
                supporting_tags=[debt_current_anchor.tag, debt_noncurrent_anchor.tag],
                computation_method=f"{debt_current_anchor.tag} + {debt_noncurrent_anchor.tag}",
                guardrails=guardrails,
            )
    
    # If only one exists, use it as proxy
    if debt_current_anchor and not debt_noncurrent_anchor:
        guardrails.append("Using Debt Current as proxy (Debt Noncurrent not available)")
        return ComputedVariable(
            variable_name="Debt Amount",
            model_role=BS_DEBT_CURRENT,
            periods=debt_current_anchor.periods.copy(),
            status="proxy",
            supporting_tags=[debt_current_anchor.tag],
            computation_method=f"{debt_current_anchor.tag} (proxy - Debt Noncurrent not available)",
            guardrails=guardrails,
        )
    
    if debt_noncurrent_anchor and not debt_current_anchor:
        guardrails.append("Using Debt Noncurrent as proxy (Debt Current not available)")
        return ComputedVariable(
            variable_name="Debt Amount",
            model_role=BS_DEBT_NONCURRENT,
            periods=debt_noncurrent_anchor.periods.copy(),
            status="proxy",
            supporting_tags=[debt_noncurrent_anchor.tag],
            computation_method=f"{debt_noncurrent_anchor.tag} (proxy - Debt Current not available)",
            guardrails=guardrails,
        )
    
    guardrails.append("Both Debt Current and Debt Noncurrent anchors missing")
    return None


def _as_floatmap(li: Dict[str, Any]) -> Dict[str, float]:
    """Convert line item periods to float map."""
    out = {}
    for p, v in (li.get("periods") or {}).items():
        try:
            out[p] = float(v)
        except (ValueError, TypeError):
            pass
    return out


def compute_debt_amount_dict(normalized: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute Debt Amount from normalized balance sheet items with BS_DEBT_* roles.
    
    This function looks for line items that have been tagged with BS_DEBT_CURRENT
    or BS_DEBT_NONCURRENT roles (from anchor_balance_sheet_debt or LLM classification)
    and sums them by period.
    
    Returns a dictionary format for use in computed_variables storage.
    
    Args:
        normalized: Structured JSON with statements.balance_sheet.line_items
        
    Returns:
        Dictionary with status, reason, periods, and supporting tags
    """
    bs = normalized.get("statements", {}).get("balance_sheet", {}).get("line_items", [])
    
    # Find all items with debt roles
    cur = [li for li in bs if li.get("model_role") == BS_DEBT_CURRENT]
    non = [li for li in bs if li.get("model_role") == BS_DEBT_NONCURRENT]
    
    if not cur and not non:
        return {
            "status": "not_computable",
            "reason": "No BS debt roles found.",
            "periods": {},
            "supporting": []
        }
    
    def sum_list(items: List[Dict[str, Any]]) -> Dict[str, float]:
        """Sum periods across multiple line items."""
        total = {}
        for li in items:
            fmap = _as_floatmap(li)
            for p, v in fmap.items():
                total[p] = total.get(p, 0.0) + v
        return total
    
    cur_map = sum_list(cur)
    non_map = sum_list(non)
    
    # Combine periods
    all_periods: Set[str] = set(cur_map.keys()) | set(non_map.keys())
    periods = {p: cur_map.get(p, 0.0) + non_map.get(p, 0.0) for p in all_periods}
    
    return {
        "status": "computed",
        "reason": "Computed as BS_DEBT_CURRENT + BS_DEBT_NONCURRENT.",
        "periods": periods,
        "supporting": [li.get("tag", "Unknown") for li in cur + non]
    }


def compute_accrued_expenses(
    anchors: Dict[str, Optional[AnchorFact]],
) -> Optional[ComputedVariable]:
    """
    Compute Accrued Expenses from anchors.
    
    If combined AP+Accrued AND separable AP exist:
        Accrued = (AP+Accrued) - AP
    Else: accept combined as proxy for accrued liabilities.
    """
    ap_anchor = anchors.get(BS_ACCOUNTS_PAYABLE)
    ap_and_accrued_anchor = anchors.get(BS_AP_AND_ACCRUED)
    
    guardrails = []
    
    # Best case: can compute from combined minus AP
    if ap_and_accrued_anchor and ap_anchor:
        combined_periods = ap_and_accrued_anchor.periods
        ap_periods = ap_anchor.periods
        
        computed_periods = {}
        all_periods = set(combined_periods.keys()) | set(ap_periods.keys())
        
        for period in all_periods:
            combined_val = combined_periods.get(period)
            ap_val = ap_periods.get(period, 0.0)
            
            if combined_val is not None and ap_val is not None:
                accrued_val = combined_val - ap_val
                if accrued_val >= 0:  # Sanity check
                    computed_periods[period] = accrued_val
        
        if computed_periods:
            return ComputedVariable(
                variable_name="Accrued Expenses",
                model_role=BS_ACCRUED_LIABILITIES,
                periods=computed_periods,
                status="computed",
                supporting_tags=[ap_and_accrued_anchor.tag, ap_anchor.tag],
                computation_method="(Accounts Payable + Accrued Combined) - Accounts Payable",
                guardrails=guardrails,
            )
    
    # Fallback: use combined tag as proxy
    if ap_and_accrued_anchor and not ap_anchor:
        guardrails.append("Using combined AP+Accrued as proxy (separate AP not available)")
        return ComputedVariable(
            variable_name="Accrued Expenses",
            model_role=BS_ACCRUED_LIABILITIES,
            periods=ap_and_accrued_anchor.periods.copy(),
            status="proxy",
            supporting_tags=[ap_and_accrued_anchor.tag],
            computation_method="Accounts Payable + Accrued Liabilities Combined (proxy)",
            guardrails=guardrails,
        )
    
    guardrails.append("No AP+Accrued combined tag or separate AP anchor found")
    return None


def compute_gross_profit(
    anchors: Dict[str, Optional[AnchorFact]],
) -> Optional[ComputedVariable]:
    """
    Compute Gross Profit from anchors.
    
    Formula: Gross Profit = Revenue - COGS
    """
    revenue_anchor = anchors.get(IS_REVENUE)
    cogs_anchor = anchors.get(IS_COGS)
    
    guardrails = []
    
    if not revenue_anchor:
        guardrails.append("Revenue anchor missing - cannot compute Gross Profit")
        return None
    
    if not cogs_anchor:
        guardrails.append("COGS anchor missing - cannot compute Gross Profit")
        return None
    
    revenue_periods = revenue_anchor.periods
    cogs_periods = cogs_anchor.periods
    
    computed_periods = {}
    all_periods = set(revenue_periods.keys()) | set(cogs_periods.keys())
    
    for period in all_periods:
        revenue_val = revenue_periods.get(period)
        cogs_val = cogs_periods.get(period)
        
        if revenue_val is not None and cogs_val is not None:
            computed_periods[period] = revenue_val - cogs_val
    
    if not computed_periods:
        guardrails.append("Could not compute for any period: missing values")
        return None
    
    return ComputedVariable(
        variable_name="Gross Profit",
        model_role=IS_GROSS_PROFIT,
        periods=computed_periods,
        status="computed",
        supporting_tags=[revenue_anchor.tag, cogs_anchor.tag],
        computation_method="Revenue - COGS",
        guardrails=guardrails,
    )


def compute_operating_margin(
    anchors: Dict[str, Optional[AnchorFact]],
) -> Optional[ComputedVariable]:
    """
    Compute Operating Margin from anchors.
    
    Formula: Operating Margin = Operating Income / Revenue
    Returns as percentage (0.15 = 15%)
    """
    operating_income_anchor = anchors.get(IS_OPERATING_INCOME)
    revenue_anchor = anchors.get(IS_REVENUE)
    
    guardrails = []
    
    if not operating_income_anchor:
        guardrails.append("Operating Income anchor missing - cannot compute Operating Margin")
        return None
    
    if not revenue_anchor:
        guardrails.append("Revenue anchor missing - cannot compute Operating Margin")
        return None
    
    op_income_periods = operating_income_anchor.periods
    revenue_periods = revenue_anchor.periods
    
    computed_periods = {}
    all_periods = set(op_income_periods.keys()) | set(revenue_periods.keys())
    
    for period in all_periods:
        op_income_val = op_income_periods.get(period)
        revenue_val = revenue_periods.get(period)
        
        if op_income_val is not None and revenue_val is not None and revenue_val != 0:
            computed_periods[period] = op_income_val / revenue_val
    
    if not computed_periods:
        guardrails.append("Could not compute for any period: missing values or zero revenue")
        return None
    
    return ComputedVariable(
        variable_name="Operating Margin",
        model_role=IS_OPERATING_INCOME,  # Using same role for now
        periods=computed_periods,
        status="computed",
        supporting_tags=[operating_income_anchor.tag, revenue_anchor.tag],
        computation_method="Operating Income / Revenue",
        guardrails=guardrails,
    )


def compute_all_derived_variables(
    anchors: Dict[str, Optional[AnchorFact]],
) -> Dict[str, Optional[ComputedVariable]]:
    """
    Compute all derived DCF variables from anchors.
    
    Args:
        anchors: Dictionary of extracted core anchors
        
    Returns:
        Dictionary mapping variable_name -> ComputedVariable (or None if not computable)
    """
    computed = {}
    
    computed["Operating Costs / Margin"] = compute_operating_costs(anchors)
    computed["EBITDA Margins / Costs"] = compute_ebitda(anchors)
    computed["Debt Amount"] = compute_debt_amount(anchors)
    computed["Accrued Expenses"] = compute_accrued_expenses(anchors)
    computed["Gross Profit"] = compute_gross_profit(anchors)
    computed["Operating Margin"] = compute_operating_margin(anchors)
    
    return computed

