"""
reconstruct_note18_from_xbrl.py

This script:
1. Fetches Ford Motor Company's SEC XBRL companyfacts.
2. Extracts all interest-bearing debt tags.
3. Classifies them by segment + maturity bucket.
4. Reconstructs a Note 18–style debt table, similar to the PDF 10-K.
5. Exports the final Note 18 reconstruction into a JSON file.

Replace SEC_USER_AGENT with your actual information.
"""

import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple

import requests

# =========================
# CONFIGURATION
# =========================

FORD_CIK = "0000037996"
TARGET_YEAR = 2024

COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

SEC_USER_AGENT = "YOUR_NAME_YOUR_APP your_email@example.com"

# Output JSON file
OUTPUT_JSON_PATH = "ford_note18_reconstructed.json"

# Debt tagging universe
WITHIN_ONE_YEAR_TAGS = {
    "us-gaap:DebtCurrent",
    "us-gaap:ShortTermBorrowings",
    "us-gaap:CommercialPaper",
    "us-gaap:LongTermDebtCurrent",
    "us-gaap:LongTermDebtAndCapitalLeaseObligationsCurrent",
}

AFTER_ONE_YEAR_TAGS = {
    "us-gaap:DebtNoncurrent",
    "us-gaap:LongTermDebtNoncurrent",
    "us-gaap:LongTermDebt",
    "us-gaap:LongTermDebtAndCapitalLeaseObligations",
    "us-gaap:VariableInterestEntityDebt",
}

LEASE_TAGS = {
    "us-gaap:FinanceLeaseLiabilityCurrent",
    "us-gaap:FinanceLeaseLiabilityNoncurrent",
    "us-gaap:FinanceLeaseLiability",
}

ALL_DEBT_TAGS = WITHIN_ONE_YEAR_TAGS | AFTER_ONE_YEAR_TAGS | LEASE_TAGS


# =========================
# DATA STRUCTURES
# =========================

class Segment(Enum):
    CONSOLIDATED = "consolidated"
    COMPANY_EXCL_FORD_CREDIT = "company_excl_ford_credit"
    FORD_CREDIT = "ford_credit"
    OTHER = "other"


class MaturityBucket(Enum):
    WITHIN_ONE_YEAR = "within_one_year"
    AFTER_ONE_YEAR = "after_one_year"
    OTHER = "other"


@dataclass
class DebtFact:
    tag: str
    value: float
    unit: str
    end_date: str
    segment: Segment
    bucket: MaturityBucket
    raw_segment: Optional[dict]


@dataclass
class Note18Row:
    segment: Segment
    bucket: MaturityBucket
    amount: float


@dataclass
class Note18Table:
    company: str
    cik: str
    fiscal_year: int
    report_date: str
    rows: List[Note18Row]

    def to_json_dict(self) -> dict:
        return {
            "company": self.company,
            "cik": self.cik,
            "fiscal_year": self.fiscal_year,
            "report_date": self.report_date,
            "rows": [
                {
                    "segment": row.segment.value,
                    "bucket": row.bucket.value,
                    "amount": row.amount,
                }
                for row in self.rows
            ],
        }

    def to_pretty_string(self) -> str:
        lines = []
        lines.append(
            f"Reconstructed Note 18 – Debt and Commitments (XBRL)\n"
            f"Company: {self.company} (CIK {self.cik})  Year: {self.fiscal_year}  Report date: {self.report_date}\n"
        )

        segments = sorted({r.segment for r in self.rows}, key=lambda s: s.value)

        header = f"{'Segment':30} {'Within 1 Year':>18} {'After 1 Year':>18} {'Total':>18}"
        lines.append(header)
        lines.append("-" * len(header))

        for seg in segments:
            within = sum(
                r.amount for r in self.rows
                if r.segment == seg and r.bucket == MaturityBucket.WITHIN_ONE_YEAR
            )
            after = sum(
                r.amount for r in self.rows
                if r.segment == seg and r.bucket == MaturityBucket.AFTER_ONE_YEAR
            )
            total = within + after

            lines.append(
                f"{seg.value:30} {within:18,.0f} {after:18,.0f} {total:18,.0f}"
            )

        return "\n".join(lines)


# =========================
# XBRL HELPERS
# =========================

def fetch_companyfacts(cik: str) -> Dict:
    url = COMPANYFACTS_URL.format(cik=cik)
    headers = {"User-Agent": SEC_USER_AGENT}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()


def _parse_date(d: str) -> datetime:
    return datetime.strptime(d, "%Y-%m-%d")


def _pick_latest_for_year(facts: List[Dict], target_year: int) -> Optional[Dict]:
    """
    For each tag+unit list, pick the latest fact whose end date is in the target year.
    """
    if not facts:
        return None

    year_facts = [
        f for f in facts if "end" in f and _parse_date(f["end"]).year == target_year
    ]
    candidates = year_facts or facts

    return max(
        candidates,
        key=lambda f: _parse_date(f["end"]) if "end" in f else datetime.min,
    )


def classify_segment(seg: Optional[dict]) -> Segment:
    """
    Very simple heuristic mapping for Ford.
    """
    if not seg:
        return Segment.CONSOLIDATED

    s = json.dumps(seg).lower()

    if "ford credit" in s:
        return Segment.FORD_CREDIT
    if "company excluding ford credit" in s:
        return Segment.COMPANY_EXCL_FORD_CREDIT
    if "consolidated" in s:
        return Segment.CONSOLIDATED

    return Segment.OTHER


def classify_bucket(tag: str) -> MaturityBucket:
    if tag in WITHIN_ONE_YEAR_TAGS:
        return MaturityBucket.WITHIN_ONE_YEAR
    if tag in AFTER_ONE_YEAR_TAGS:
        return MaturityBucket.AFTER_ONE_YEAR
    if tag in LEASE_TAGS:
        return MaturityBucket.AFTER_ONE_YEAR

    return MaturityBucket.OTHER


def extract_debt_facts(companyfacts: Dict, target_year: int) -> List[DebtFact]:
    out: List[DebtFact] = []
    facts_root = companyfacts.get("facts", {})

    for full_tag in ALL_DEBT_TAGS:
        taxonomy, tag = full_tag.split(":")
        taxonomy_dict = facts_root.get(taxonomy)
        if not taxonomy_dict:
            continue

        tag_entry = taxonomy_dict.get(tag)
        if not tag_entry:
            continue

        units = tag_entry.get("units", {})
        for unit, fact_list in units.items():
            best = _pick_latest_for_year(fact_list, target_year)
            if not best or "val" not in best:
                continue

            value = float(best["val"])
            end_date = best.get("end", "")
            seg = best.get("seg")

            out.append(
                DebtFact(
                    tag=full_tag,
                    value=value,
                    unit=unit,
                    end_date=end_date,
                    segment=classify_segment(seg),
                    bucket=classify_bucket(full_tag),
                    raw_segment=seg,
                )
            )

    return out


# =========================
# RECONSTRUCT NOTE 18
# =========================

def reconstruct_note18(companyfacts: Dict, target_year: int) -> Note18Table:
    company = companyfacts.get("entityName", "Unknown Company")
    cik = companyfacts.get("cik", FORD_CIK)

    debt_facts = extract_debt_facts(companyfacts, target_year)
    if not debt_facts:
        raise RuntimeError("No debt facts found. Expand tag list or inspect companyfacts.")

    report_date = max(f.end_date for f in debt_facts)

    # aggregate (segment, bucket)
    rows: List[Note18Row] = []
    bucket_map: Dict[Tuple[Segment, MaturityBucket], float] = {}

    for f in debt_facts:
        if f.bucket == MaturityBucket.OTHER:
            continue
        key = (f.segment, f.bucket)
        bucket_map[key] = bucket_map.get(key, 0.0) + f.value

    for (segment, bucket), amount in bucket_map.items():
        rows.append(Note18Row(segment=segment, bucket=bucket, amount=amount))

    return Note18Table(
        company=company,
        cik=str(cik).zfill(10),
        fiscal_year=target_year,
        report_date=report_date,
        rows=rows,
    )


# =========================
# MAIN
# =========================

def main():
    print(f"Fetching Ford SEC companyfacts ({FORD_CIK})...")
    cf = fetch_companyfacts(FORD_CIK)

    print(f"Reconstructing Note 18 table for {TARGET_YEAR}...")
    table = reconstruct_note18(cf, TARGET_YEAR)

    print("\n--- Pretty Table ---\n")
    print(table.to_pretty_string())

    # Export JSON
    json_dict = table.to_json_dict()

    with open(OUTPUT_JSON_PATH, "w") as f:
        json.dump(json_dict, f, indent=2)

    print(f"\nJSON exported to: {OUTPUT_JSON_PATH}\n")


if __name__ == "__main__":
    main()
