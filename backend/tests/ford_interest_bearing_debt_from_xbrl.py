"""
ford_interest_bearing_debt_from_xbrl.py

End-to-end script to:
1. Call the SEC 'companyfacts' XBRL API for Ford (CIK 0000037996)
2. Pull all relevant debt-related tags
3. Aggregate them into a single interest-bearing debt number suitable for WACC
4. Show a transparent breakdown of which tags and values were used

This is intentionally written as a standalone script so you can:
- Run it directly, or
- Integrate the core functions into your Denari pipeline.
"""

import requests
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# =========================
# CONFIGURATION
# =========================

# Ford Motor Company CIK in SEC "companyfacts" format (10 digits, leading zeros)
FORD_CIK = "0000037996"

# SEC companyfacts endpoint template
COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

# YOU **MUST** set this to comply with SEC's fair access policy.
# Use something like "YourName YourAppName Contact@yourdomain.com".
SEC_USER_AGENT = "YOUR_NAME_YOUR_APP your_email@example.com"

# Tags we consider for interest-bearing debt.
# This is not exhaustive, but a practical starting set.
DEBT_TAGS_PRIORITY = {
    # Current debt "totals"
    "us-gaap:DebtCurrent": "current_total",
    # Noncurrent debt "totals"
    "us-gaap:DebtNoncurrent": "noncurrent_total",
    # More granular pieces (only used if totals missing or for diagnostics)
    "us-gaap:ShortTermBorrowings": "current_component",
    "us-gaap:CommercialPaper": "current_component",
    "us-gaap:LongTermDebtCurrent": "current_component",
    "us-gaap:LongTermDebtAndCapitalLeaseObligationsCurrent": "current_component",
    "us-gaap:LongTermDebtNoncurrent": "noncurrent_component",
    "us-gaap:LongTermDebt": "noncurrent_component",
    "us-gaap:LongTermDebtAndCapitalLeaseObligations": "noncurrent_component",
    # Finance lease liabilities (interest-bearing)
    "us-gaap:FinanceLeaseLiabilityCurrent": "current_component",
    "us-gaap:FinanceLeaseLiabilityNoncurrent": "noncurrent_component",
    "us-gaap:FinanceLeaseLiability": "lease_total",
    # Asset-backed / other debt if tagged as such
    "us-gaap:VariableInterestEntityDebt": "noncurrent_component",
}

# =========================
# DATA STRUCTURES
# =========================

@dataclass
class DebtFact:
    tag: str
    label: str
    value: float
    unit: str
    end_date: str
    segment: Optional[str]  # None = consolidated or unsegmented
    group: str              # "current_total", "noncurrent_total", "current_component", etc.

@dataclass
class InterestBearingDebtResult:
    current_debt: float
    noncurrent_debt: float
    lease_component: float
    total_interest_bearing_debt: float
    facts_used: List[DebtFact]

    def to_human_readable(self) -> str:
        lines = []
        lines.append("Ford Motor Company – Interest-Bearing Debt (from SEC XBRL companyfacts)")
        lines.append("All amounts are in the units reported by SEC (usually USD).\n")

        lines.append("Facts used:")
        for f in self.facts_used:
            lines.append(
                f"  - {f.tag} ({f.label}), group={f.group}, "
                f"end_date={f.end_date}, segment={f.segment or 'None'}, "
                f"value={f.value:,.0f} {f.unit}"
            )

        lines.append("")
        lines.append(f"Current debt estimate:   {self.current_debt:,.0f}")
        lines.append(f"Noncurrent debt estimate:{self.noncurrent_debt:,.0f}")
        if self.lease_component:
            lines.append(f"Finance lease component: {self.lease_component:,.0f}")
        lines.append("-" * 60)
        lines.append(
            f"TOTAL interest-bearing debt: {self.total_interest_bearing_debt:,.0f}"
        )
        return "\n".join(lines)


# =========================
# HELPER FUNCTIONS
# =========================

def fetch_companyfacts(cik: str) -> Dict:
    """
    Fetch the SEC 'companyfacts' JSON for a given CIK.
    """
    url = COMPANYFACTS_URL.format(cik=cik)
    headers = {"User-Agent": SEC_USER_AGENT}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()


def _pick_latest_fact(fact_list: List[Dict], target_year: int) -> Optional[Dict]:
    """
    Given a list of fact entries from companyfacts["facts"][taxonomy][tag]["units"][unit],
    pick the latest fact whose end date falls in the target year.
    If none match the target year, fall back to the overall latest fact.
    """
    def parse_date(d: str) -> datetime:
        return datetime.strptime(d, "%Y-%m-%d")

    if not fact_list:
        return None

    # Filter by target year if possible
    year_facts = [
        f for f in fact_list
        if "end" in f and parse_date(f["end"]).year == target_year
    ]
    candidates = year_facts or fact_list

    # Choose the one with the latest end date
    best = max(
        candidates,
        key=lambda f: parse_date(f["end"]) if "end" in f else datetime.min
    )
    return best


def extract_debt_facts_for_year(
    companyfacts: Dict,
    target_year: int,
) -> List[DebtFact]:
    """
    Extract all relevant debt-related facts for the given year
    from the SEC companyfacts JSON.
    """
    facts_out: List[DebtFact] = []
    facts_root = companyfacts.get("facts", {})

    for full_tag, group in DEBT_TAGS_PRIORITY.items():
        taxonomy, tag = full_tag.split(":")
        if taxonomy not in facts_root:
            continue
        taxonomy_facts = facts_root[taxonomy]

        if tag not in taxonomy_facts:
            continue

        tag_entry = taxonomy_facts[tag]
        units_dict: Dict[str, List[Dict]] = tag_entry.get("units", {})

        # In practice, you'll often see "USD" as the unit key.
        for unit, fact_list in units_dict.items():
            best_fact = _pick_latest_fact(fact_list, target_year)
            if not best_fact:
                continue

            value = best_fact.get("val")
            if value is None:
                continue

            # Filter out clearly non-consolidated / weird segments if needed;
            # for now, we just capture any segment info to inspect later.
            segment = None
            if "seg" in best_fact:
                # Very simple representation; you can expand this
                segment = str(best_fact["seg"])

            label = tag_entry.get("label", tag)

            facts_out.append(
                DebtFact(
                    tag=full_tag,
                    label=label,
                    value=float(value),
                    unit=unit,
                    end_date=best_fact.get("end", ""),
                    segment=segment,
                    group=group,
                )
            )

    return facts_out


def compute_interest_bearing_debt_from_facts(
    debt_facts: List[DebtFact],
) -> InterestBearingDebtResult:
    """
    Aggregate individual debt facts into an interest-bearing debt estimate.

    Priority logic:
    1. If DebtCurrent exists, use it as current debt; otherwise sum current components.
    2. If DebtNoncurrent exists, use it as noncurrent debt; otherwise use LongTermDebtNoncurrent,
       or sum noncurrent components.
    3. If FinanceLeaseLiability exists, add it; otherwise sum its current + noncurrent components
       if present.
    """
    current_total = None
    noncurrent_total = None
    lease_total = 0.0

    current_components: List[DebtFact] = []
    noncurrent_components: List[DebtFact] = []
    lease_components: List[DebtFact] = []

    for f in debt_facts:
        if f.group == "current_total":
            # If multiple values exist (different segments), prefer the largest
            current_total = max(current_total or 0.0, f.value)
        elif f.group == "noncurrent_total":
            noncurrent_total = max(noncurrent_total or 0.0, f.value)
        elif f.group == "current_component":
            current_components.append(f)
        elif f.group == "noncurrent_component":
            noncurrent_components.append(f)
        elif f.group == "lease_total":
            lease_components.append(f)

    # Current debt
    if current_total is not None:
        current_debt = current_total
        used_current_facts = [f for f in debt_facts if f.group == "current_total" and f.value == current_total]
    else:
        current_debt = sum(f.value for f in current_components)
        used_current_facts = current_components

    # Noncurrent debt
    if noncurrent_total is not None:
        noncurrent_debt = noncurrent_total
        used_noncurrent_facts = [f for f in debt_facts if f.group == "noncurrent_total" and f.value == noncurrent_total]
    else:
        # Try noncurrent components
        noncurrent_debt = sum(f.value for f in noncurrent_components)
        used_noncurrent_facts = noncurrent_components

    # Lease component
    if lease_components:
        lease_total = max(f.value for f in lease_components)
        used_lease_facts = [
            f for f in lease_components if f.value == lease_total
        ]
    else:
        lease_total = 0.0
        used_lease_facts = []

    total = current_debt + noncurrent_debt + lease_total

    facts_used = used_current_facts + used_noncurrent_facts + used_lease_facts

    return InterestBearingDebtResult(
        current_debt=current_debt,
        noncurrent_debt=noncurrent_debt,
        lease_component=lease_total,
        total_interest_bearing_debt=total,
        facts_used=facts_used,
    )


# =========================
# MAIN ENTRYPOINT
# =========================

def main():
    target_year = 2024  # adjust if needed

    print(f"Fetching SEC companyfacts for Ford (CIK {FORD_CIK})...")
    data = fetch_companyfacts(FORD_CIK)

    print(f"Extracting debt-related XBRL facts for year {target_year}...")
    debt_facts = extract_debt_facts_for_year(data, target_year)

    if not debt_facts:
        print("No debt facts found with the current tag configuration. "
              "You may need to expand DEBT_TAGS_PRIORITY or inspect raw companyfacts.")
        return

    print(f"Found {len(debt_facts)} debt-related facts. Computing interest-bearing debt...")
    result = compute_interest_bearing_debt_from_facts(debt_facts)

    print()
    print(result.to_human_readable())


if __name__ == "__main__":
    main()
