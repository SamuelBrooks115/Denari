"""
excel_dcf_scenarios.py — Helpers to populate DCF Bear/Bull scenario formulas.

This module builds a dictionary of Excel formula templates for Bull/Bear
DCF scenarios and applies them to a given worksheet based on scenario
assumptions coming from the converted legacy assumptions format.
"""

from __future__ import annotations

from typing import Dict, Any, List

from app.core.logging import get_logger

logger = get_logger(__name__)


def build_scenario_formula_dict() -> Dict[str, Dict[str, Dict[str, str]]]:
    """
    Build the full formula template dictionary for DCF Bull/Bear scenarios.

    Structure:
        {
          "line_item_key": {
              "step":    {"G": "=...", "H": "=...", ..., "K": "=..."},
              "constant":{"G": "=...", ...},
              "custom":  {"G": "=...", ...},
          },
          ...
        }

    Line item keys:
        - "revenue_growth"  (row 18)
        - "gp_margin"       (row 21)
        - "ebit_margin"     (row 25)
        - "da_pct_rev"      (row 28)
        - "capex_pct_rev"   (row 29, % of revenue)
        - "capex_pct_da"    (row 29, % of D&A)
        - "wc_change"       (row 30)
    """

    # Helper to build the simple step/constant/custom patterns for rows that
    # just increment off the previous column in the same row.
    def _simple_row_step(row: int) -> Dict[str, str]:
        return {
            "G": f"=F{row}+{{x}}",
            "H": f"=G{row}+{{x}}",
            "I": f"=H{row}+{{x}}",
            "J": f"=I{row}+{{x}}",
            "K": f"=J{row}+{{x}}",
        }

    def _simple_row_constant(row: int) -> Dict[str, str]:
        return {
            "G": "={y}",
            "H": "={y}",
            "I": "={y}",
            "J": "={y}",
            "K": "={y}",
        }

    def _simple_row_custom(row: int) -> Dict[str, str]:
        return {
            "G": "={a}",
            "H": "={b}",
            "I": "={c}",
            "J": "={d}",
            "K": "={e}",
        }

    # Revenue growth, GP margin, EBIT margin all use the same pattern with
    # different row numbers.
    revenue_growth_step = _simple_row_step(18)
    revenue_growth_const = _simple_row_constant(18)
    revenue_growth_custom = _simple_row_custom(18)

    gp_margin_step = _simple_row_step(21)
    gp_margin_const = _simple_row_constant(21)
    gp_margin_custom = _simple_row_custom(21)

    ebit_margin_step = _simple_row_step(25)
    ebit_margin_const = _simple_row_constant(25)
    ebit_margin_custom = _simple_row_custom(25)

    # D&A (% of Revenue) – row 28, formulas provided in the prompt
    da_step = {
        "G": "=(F28/F17)+{x}*G17",
        "H": "=(F28/F17)+{x}*H17",
        "I": "=(F28/F17)+{x}*I17",
        "J": "=(F28/F17)+{x}*J17",
        "K": "=(F28/F17)+{x}*K17",
    }
    da_custom = {
        "G": "={a}*G17",
        "H": "={b}*H17",
        "I": "={c}*I17",
        "J": "={d}*J17",
        "K": "={e}*K17",
    }
    da_const = {
        "G": "={y}*G17",
        "H": "={y}*H17",
        "I": "={y}*I17",
        "J": "={y}*J17",
        "K": "={y}*K17",
    }

    # CapEx (% of Revenue) – row 29, same structure as D&A (% of Revenue)
    capex_rev_step = {
        "G": "=(F29/F17)+{x}*G17",
        "H": "=(F29/F17)+{x}*H17",
        "I": "=(F29/F17)+{x}*I17",
        "J": "=(F29/F17)+{x}*J17",
        "K": "=(F29/F17)+{x}*K17",
    }
    capex_rev_custom = {
        "G": "={a}*G17",
        "H": "={b}*H17",
        "I": "={c}*I17",
        "J": "={d}*J17",
        "K": "={e}*K17",
    }
    capex_rev_const = {
        "G": "={y}*G17",
        "H": "={y}*H17",
        "I": "={y}*I17",
        "J": "={y}*J17",
        "K": "={y}*K17",
    }

    # CapEx as % of D&A – row 29, analogous to D&A but driven off row 28
    capex_da_step = {
        "G": "=(F29/F28)+{x}*G28",
        "H": "=(F29/F28)+{x}*H28",
        "I": "=(F29/F28)+{x}*I28",
        "J": "=(F29/F28)+{x}*J28",
        "K": "=(F29/F28)+{x}*K28",
    }
    capex_da_custom = {
        "G": "={a}*G28",
        "H": "={b}*H28",
        "I": "={c}*I28",
        "J": "={d}*J28",
        "K": "={e}*K28",
    }
    capex_da_const = {
        "G": "={y}*G28",
        "H": "={y}*H28",
        "I": "={y}*I28",
        "J": "={y}*J28",
        "K": "={y}*K28",
    }

    # Changes in WC – row 30, with provided step/custom/constant patterns
    wc_step = {
        "G": "=F30+{x}",
        "H": "=F30+{x}",
        "I": "=F30+{x}",
        "J": "=F30+{x}",
        "K": "=F30+{x}",
    }
    wc_custom = {
        "G": "={a}",
        "H": "={b}",
        "I": "={c}",
        "J": "={d}",
        "K": "={e}",
    }
    wc_const = {
        "G": "={y}",
        "H": "={y}",
        "I": "={y}",
        "J": "={y}",
        "K": "={y}",
    }

    formula_dict: Dict[str, Dict[str, Dict[str, str]]] = {
        "revenue_growth": {
            "step": revenue_growth_step,
            "constant": revenue_growth_const,
            "custom": revenue_growth_custom,
        },
        "gp_margin": {
            "step": gp_margin_step,
            "constant": gp_margin_const,
            "custom": gp_margin_custom,
        },
        "ebit_margin": {
            "step": ebit_margin_step,
            "constant": ebit_margin_const,
            "custom": ebit_margin_custom,
        },
        "da_pct_rev": {
            "step": da_step,
            "constant": da_const,
            "custom": da_custom,
        },
        "capex_pct_rev": {
            "step": capex_rev_step,
            "constant": capex_rev_const,
            "custom": capex_rev_custom,
        },
        "capex_pct_da": {
            "step": capex_da_step,
            "constant": capex_da_const,
            "custom": capex_da_custom,
        },
        "wc_change": {
            "step": wc_step,
            "constant": wc_const,
            "custom": wc_custom,
        },
    }

    return formula_dict


def apply_scenario_to_sheet(
    sheet,
    scenario_assumptions: Dict[str, Any],
    formula_dict: Dict[str, Dict[str, Dict[str, str]]],
) -> None:
    """
    Apply a Bull/Bear scenario to a DCF worksheet.

    Args:
        sheet: openpyxl Worksheet for DCF Bear or DCF Bull.
        scenario_assumptions: Dict from legacy assumptions format, e.g.:
            {
              "revenue_growth": {"type": "step", "values": [0.01, ...]},
              "gp_margin":      {"type": "custom", "values": [0.30, 0.31, ...]},
              ...
            }
        formula_dict: Output of build_scenario_formula_dict().
    """

    if not scenario_assumptions:
        logger.info(f"No scenario assumptions provided for sheet {sheet.title}, skipping.")
        return

    # Fixed rows for each line item
    line_item_rows: Dict[str, int] = {
        "revenue_growth": 18,
        "gp_margin": 21,
        "ebit_margin": 25,
        "da_pct_rev": 28,
        "capex_pct_rev": 29,
        "capex_pct_da": 29,
        "wc_change": 30,
    }

    # Column order for forecast years
    forecast_cols: List[str] = ["G", "H", "I", "J", "K"]

    def _extract_values(assumption: Dict[str, Any]) -> List[float]:
        vals = assumption.get("values", [])
        if not isinstance(vals, list):
            return []
        return vals

    def _apply_for_line_item(line_key: str, assumption: Dict[str, Any]) -> None:
        # CapEx selection logic: if we're handling capex_pct_rev but capex_pct_da
        # is present, skip here so % of D&A can override.
        if line_key == "capex_pct_rev" and "capex_pct_da" in scenario_assumptions:
            logger.debug("CapEx % of D&A present; skipping CapEx % of Revenue formulas.")
            return

        row = line_item_rows.get(line_key)
        if row is None:
            logger.warning(f"Unknown line item key '{line_key}', skipping.")
            return

        templates_by_method = formula_dict.get(line_key)
        if not templates_by_method:
            logger.warning(f"No formula templates found for line item '{line_key}', skipping.")
            return

        method_type = (assumption.get("type") or "").lower()
        if method_type not in templates_by_method:
            logger.warning(
                f"Unsupported method '{method_type}' for line item '{line_key}', skipping."
            )
            return

        templates_for_method = templates_by_method[method_type]
        values = _extract_values(assumption)

        # Determine placeholder values
        placeholder_map: Dict[str, Any] = {}
        if method_type == "step":
            # Use first value as the step increment x
            if not values:
                logger.warning(f"No values for step method on '{line_key}', skipping.")
                return
            placeholder_map["x"] = values[0]
        elif method_type == "constant":
            if not values:
                logger.warning(f"No values for constant method on '{line_key}', skipping.")
                return
            placeholder_map["y"] = values[0]
        elif method_type == "custom":
            if not values:
                logger.warning(f"No values for custom method on '{line_key}', skipping.")
                return
            # Pad or truncate to exactly 5 values
            padded = list(values[:5])
            if len(padded) < 5:
                last_val = padded[-1] if padded else 0.0
                padded.extend([last_val] * (5 - len(padded)))
            a, b, c, d, e = padded[:5]
            placeholder_map.update({"a": a, "b": b, "c": c, "d": d, "e": e})

        # Apply formulas to G–K for this row
        for col in forecast_cols:
            template = templates_for_method.get(col)
            if not template:
                continue
            try:
                final_formula = template.format(**placeholder_map)
            except Exception as e:  # noqa: BLE001
                logger.warning(
                    f"Failed to format formula for {line_key} at {col}{row}: "
                    f"template='{template}', placeholders={placeholder_map}, error={e}"
                )
                continue

            if not final_formula.startswith("="):
                # Ensure formulas always start with '='
                final_formula = "=" + final_formula

            cell_ref = f"{col}{row}"
            sheet[cell_ref].value = final_formula
            logger.debug(f"Wrote scenario formula for {line_key} to {cell_ref}: {final_formula}")

    # Iterate through the line items we know about
    for key in line_item_rows.keys():
        assumption = scenario_assumptions.get(key)
        if not assumption:
            continue
        if not isinstance(assumption, dict):
            logger.warning(f"Scenario assumption for '{key}' is not a dict, skipping.")
            continue
        _apply_for_line_item(key, assumption)


