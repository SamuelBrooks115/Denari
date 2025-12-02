"""
download_ford_2024_ixbrl.py — Download Ford 2024 10-K iXBRL from SEC EDGAR.

This script:
1. Uses EdgarClient to get Ford's submissions
2. Finds the 2024 10-K filing
3. Downloads the iXBRL file (or ZIP archive)
4. Saves it to data/xbrl/ford_2024_10k.ixbrl

Usage:
    python scripts/download_ford_2024_ixbrl.py
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Optional

import requests
from app.core.config import settings
from app.services.ingestion.clients import EdgarClient

FORD_CIK = 37996
FORD_TICKER = "F"
TARGET_YEAR = 2024
TARGET_FORM = "10-K"

# SEC EDGAR URL patterns
SEC_BASE_URL = "https://www.sec.gov"
FILING_DETAILS_URL = "https://www.sec.gov/cgi-bin/viewer?action=view&cik={cik}&accession_number={accession}&xbrl_type=v"


def find_2024_10k_filing(edgar_client: EdgarClient) -> Optional[dict]:
    """Find Ford's 2024 10-K filing from submissions."""
    submissions = edgar_client.get_submissions(FORD_CIK)
    
    filings = submissions.get("filings", {}).get("recent", {})
    forms = filings.get("form", [])
    filing_dates = filings.get("filingDate", [])
    accession_numbers = filings.get("accessionNumber", [])
    
    # Find 2024 10-K (filed in 2024 or early 2025)
    for i, form in enumerate(forms):
        if form == TARGET_FORM:
            filing_date = filing_dates[i]
            accession = accession_numbers[i]
            
            # Check if it's 2024 (filed in 2024 or 2025 for 2024 fiscal year)
            if filing_date.startswith("2024") or filing_date.startswith("2025"):
                # Also check accession number - format is CIK-YY-NNNNNN
                # YY should be 24 for 2024 fiscal year
                if "-24-" in accession or "-25-" in accession:
                    return {
                        "form": form,
                        "filingDate": filing_date,
                        "accessionNumber": accession,
                    }
    
    return None


def download_file(url: str, output_path: Path, headers: dict) -> bool:
    """
    Download a file from URL to output path.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        response = requests.get(url, headers=headers, timeout=60, stream=True)
        if response.status_code == 200:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with output_path.open("wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        else:
            # Only print error for non-404s to avoid spam
            if response.status_code != 404:
                print(f"    HTTP {response.status_code} for {url.split('/')[-1]}")
    except requests.exceptions.RequestException as e:
        # Don't print errors for every failed attempt
        pass
    except Exception as e:
        print(f"    Error: {e}")
    
    return False


def extract_ixbrl_from_zip(zip_path: Path, output_path: Path) -> bool:
    """
    Extract the main iXBRL file from a ZIP archive.
    
    Looks for the actual XBRL instance file (e.g., f-20241231x10k.htm).
    """
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            all_files = zip_ref.namelist()
            
            # Priority 1: Look for XBRL instance file pattern (ticker-fiscaldate-form.htm)
            # e.g., f-20241231x10k.htm
            instance_pattern = re.compile(rf"{FORD_TICKER.lower()}-\d{{8}}x10k\.htm", re.IGNORECASE)
            instance_files = [f for f in all_files if instance_pattern.search(f)]
            
            if instance_files:
                # Prefer the largest instance file
                file_sizes = [(f, zip_ref.getinfo(f).file_size) for f in instance_files]
                target_file = max(file_sizes, key=lambda x: x[1])[0]
                print(f"  Found XBRL instance: {target_file}")
            else:
                # Priority 2: Look for files with "xbrl" in name
                ixbrl_files = [
                    name for name in all_files
                    if name.endswith((".ixbrl", ".htm", ".html")) and "xbrl" in name.lower()
                ]
                
                if ixbrl_files:
                    # Prefer the largest file
                    file_sizes = [(f, zip_ref.getinfo(f).file_size) for f in ixbrl_files]
                    target_file = max(file_sizes, key=lambda x: x[1])[0]
                    print(f"  Found XBRL file: {target_file}")
                else:
                    # Priority 3: Find any large HTML file (likely the main filing)
                    html_files = [
                        name for name in all_files
                        if name.endswith((".htm", ".html")) and not name.startswith("__")
                    ]
                    
                    if not html_files:
                        print(f"  No suitable files found in ZIP archive")
                        return False
                    
                    # Get the largest HTML file
                    file_sizes = [(f, zip_ref.getinfo(f).file_size) for f in html_files]
                    target_file = max(file_sizes, key=lambda x: x[1])[0]
                    print(f"  Found HTML file: {target_file}")
            
            print(f"  Extracting {target_file} from ZIP...")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with zip_ref.open(target_file) as source, output_path.open("wb") as target:
                target.write(source.read())
            
            # Validate the extracted file
            if validate_xbrl_file(output_path, min_size_kb=100):
                return True
            else:
                print(f"  ⚠ Extracted file doesn't appear to be a valid XBRL instance")
                return False
    
    except Exception as e:
        print(f"  Error extracting ZIP: {e}")
        return False


def validate_xbrl_file(file_path: Path, min_size_kb: int = 50) -> bool:
    """
    Validate that a file is a real XBRL instance with substantial content.
    
    Args:
        file_path: Path to the file to validate
        min_size_kb: Minimum file size in KB to consider valid
        
    Returns:
        True if file appears to be a valid XBRL instance
    """
    if not file_path.exists():
        return False
    
    # Check file size
    file_size_kb = file_path.stat().st_size / 1024
    if file_size_kb < min_size_kb:
        return False
    
    # Check for XBRL indicators
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        # Must have XBRL namespace and US-GAAP tags
        has_xbrl_ns = (
            "xmlns:xbrl" in content.lower() or 
            "xmlns:xbrli" in content.lower() or
            'xmlns="http://www.xbrl.org/' in content
        )
        has_gaap_tags = "us-gaap:" in content or "us-gaap:" in content.lower()
        has_facts = content.count("us-gaap:") > 10  # Should have many GAAP tags
        
        return has_xbrl_ns and has_gaap_tags and has_facts
    except Exception:
        return False


def download_ixbrl_file(accession_number: str, output_path: Path) -> bool:
    """
    Download iXBRL file for a given accession number.
    
    Args:
        accession_number: SEC accession number (e.g., "0000037996-24-000123")
        output_path: Path to save the file
        
    Returns:
        True if successful, False otherwise
    """
    # SEC EDGAR requires a User-Agent header
    user_agent = settings.EDGAR_USER_AGENT or "Company Name contact@example.com"
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate",
    }
    
    # Remove dashes from accession number for URL construction
    accession_clean = accession_number.replace("-", "")
    cik_str = str(FORD_CIK).zfill(10)
    
    # Base URL for EDGAR archives
    base_url = f"https://www.sec.gov/Archives/edgar/data/{FORD_CIK}/{accession_clean}"
    
    # Try different file patterns
    # 1. Try ZIP archive first (most reliable)
    # ZIP filename format: ACCESSION-xbrl.zip (with dashes)
    zip_filename_with_dashes = f"{accession_number}-xbrl.zip"
    zip_filename_clean = f"{accession_clean}-xbrl.zip"
    
    # Try both patterns
    for zip_filename in [zip_filename_with_dashes, zip_filename_clean]:
        zip_url = f"{base_url}/{zip_filename}"
        zip_path = output_path.parent / f"{output_path.stem}.zip"
        
        print(f"  Trying ZIP archive: {zip_filename}...")
        if download_file(zip_url, zip_path, headers):
            print(f"  ✓ Downloaded ZIP archive")
            # Extract iXBRL from ZIP
            if extract_ixbrl_from_zip(zip_path, output_path):
                print(f"  ✓ Extracted iXBRL file from ZIP")
                return True
            else:
                print(f"  ⚠ Could not extract iXBRL from ZIP, but ZIP is saved at: {zip_path}")
                # Continue to try other methods
                break
    
    print(f"  Trying ZIP archive: {zip_filename}...")
    if download_file(zip_url, zip_path, headers):
        print(f"  ✓ Downloaded ZIP archive")
        # Extract iXBRL from ZIP
        if extract_ixbrl_from_zip(zip_path, output_path):
            print(f"  ✓ Extracted iXBRL file from ZIP")
            # Optionally remove ZIP file to save space
            # zip_path.unlink()
            return True
        else:
            print(f"  ⚠ Could not extract iXBRL from ZIP, but ZIP is saved at: {zip_path}")
            return False
    
    # 2. Try direct iXBRL file
    ixbrl_filename = f"{accession_clean}.ixbrl"
    ixbrl_url = f"{base_url}/{ixbrl_filename}"
    print(f"  Trying direct iXBRL: {ixbrl_filename}...")
    if download_file(ixbrl_url, output_path, headers):
        # Validate it's a real XBRL file
        if validate_xbrl_file(output_path):
            print(f"  ✓ Downloaded iXBRL file directly")
            return True
    
    # 3. Try XBRL instance file (most common pattern: ticker-fiscaldate.htm)
    # For Ford 2024 10-K: f-20241231.htm (actual filename from directory listing)
    xbrl_instance_patterns = [
        f"{FORD_TICKER.lower()}-20241231.htm",  # Actual filename
        f"{FORD_TICKER.lower()}-20241231x10k.htm",
        f"{FORD_TICKER.lower()}-20241231-x10k.htm",
        f"{FORD_TICKER.upper()}-20241231.htm",
        f"{FORD_TICKER.upper()}-20241231x10k.htm",
        f"{FORD_TICKER.upper()}-20241231-X10K.htm",
    ]
    
    for xbrl_filename in xbrl_instance_patterns:
        xbrl_url = f"{base_url}/{xbrl_filename}"
        print(f"  Trying XBRL instance: {xbrl_filename}...")
        if download_file(xbrl_url, output_path, headers):
            if validate_xbrl_file(output_path, min_size_kb=100):
                print(f"  ✓ Downloaded XBRL instance file")
                return True
    
    # 4. Try HTML files that might be iXBRL (fallback)
    html_patterns = ["R1.htm", "R2.htm", "F.htm", f"{accession_clean}.htm"]
    for html_filename in html_patterns:
        html_url = f"{base_url}/{html_filename}"
        print(f"  Trying HTML: {html_filename}...")
        if download_file(html_url, output_path, headers):
            # Validate it's actually iXBRL with substantial content
            if validate_xbrl_file(output_path, min_size_kb=100):
                print(f"  ✓ Downloaded iXBRL file (as HTML)")
                return True
    
    # If all else fails, provide manual download instructions
    print(f"\n  ❌ Could not download automatically")
    print(f"\n  Please download manually from:")
    print(f"     https://www.sec.gov/cgi-bin/viewer?action=view&cik={FORD_CIK}&accession_number={accession_number}&xbrl_type=v")
    print(f"\n  Or try direct archive URL:")
    print(f"     {base_url}/")
    
    return False


def main():
    """Main entry point."""
    print("=" * 80)
    print(f"Downloading Ford {TARGET_YEAR} {TARGET_FORM} iXBRL file")
    print("=" * 80)
    
    # Initialize EdgarClient
    try:
        edgar_client = EdgarClient()
    except Exception as e:
        print(f"❌ Error initializing EdgarClient: {e}")
        print("\nMake sure EDGAR_USER_AGENT is set in your .env file")
        return
    
    # Find the filing
    print(f"\nLooking up {TARGET_YEAR} {TARGET_FORM} filing for Ford (CIK: {FORD_CIK})...")
    try:
        filing = find_2024_10k_filing(edgar_client)
    except Exception as e:
        print(f"❌ Error fetching submissions: {e}")
        return
    
    if not filing:
        print(f"❌ Could not find {TARGET_YEAR} {TARGET_FORM} filing for Ford")
        print("\nThis might mean:")
        print("  - The filing hasn't been filed yet")
        print("  - The filing year needs to be adjusted")
        print("  - There's an issue with the SEC EDGAR API")
        return
    
    print(f"✓ Found filing:")
    print(f"  Date: {filing['filingDate']}")
    print(f"  Accession: {filing['accessionNumber']}")
    
    # Download the iXBRL file
    output_path = Path("data/xbrl/ford_2024_10k.ixbrl")
    accession = filing["accessionNumber"]
    
    print(f"\nDownloading iXBRL file to: {output_path}")
    print("-" * 80)
    
    success = download_ixbrl_file(accession, output_path)
    
    print("-" * 80)
    if success:
        file_size_mb = output_path.stat().st_size / 1024 / 1024
        print(f"\n✓ Successfully downloaded Ford 2024 10-K iXBRL")
        print(f"  Location: {output_path}")
        print(f"  Size: {file_size_mb:.2f} MB")
        print(f"\nYou can now run:")
        print(f"  python scripts/build_ford_2024_structured_output.py \\")
        print(f"    --xbrl-file {output_path}")
    else:
        print(f"\n❌ Download failed")
        print(f"\nPlease download manually from SEC EDGAR:")
        print(f"  1. Visit: https://www.sec.gov/cgi-bin/viewer?action=view&cik={FORD_CIK}&accession_number={accession}&xbrl_type=v")
        print(f"  2. Look for 'Document Format Files' or 'Interactive Data'")
        print(f"  3. Download the iXBRL file or ZIP archive")
        print(f"  4. Save to: {output_path}")


if __name__ == "__main__":
    main()

