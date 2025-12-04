"""
test_sp500_prices.py — Test script for sp500_price_fetcher.py

Run this from the backend directory:
    python -m app.test_sp500_prices
Or from the root:
    python backend/app/test_sp500_prices.py
"""

import sys
from pathlib import Path

# Add the backend directory to the path so we can import app modules
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.ingestion.sp500_price_fetcher import (
    get_ticker_price,
    get_all_prices,
    fetch_latest_sp500_prices,
)


def test_get_ticker_price():
    """Test getting a single ticker's price."""
    print("="*50)
    print("Testing get_ticker_price('AAPL')")
    print("="*50)
    
    aapl = get_ticker_price("AAPL")
    
    if aapl:
        print(f"\n✓ Successfully fetched AAPL price:")
        print(f"  Date: {aapl['date']}")
        print(f"  Close: ${aapl['close']:.2f}")
    else:
        print("\n✗ Failed to fetch AAPL price")
    
    return aapl


def test_get_all_prices():
    """Test getting all prices (first 5 tickers)."""
    print("\n" + "="*50)
    print("Testing get_all_prices() - showing first 5 tickers")
    print("="*50)
    
    prices = get_all_prices()
    
    print(f"\n✓ Successfully fetched prices for {len(prices)} companies")
    print("\nFirst 5 tickers:")
    for i, (ticker, data) in enumerate(list(prices.items())[:5]):
        print(f"  {ticker}: ${data['close']:.2f} (date: {data['date']})")
    
    return prices


def main():
    """Run all tests."""
    print("="*50)
    print("S&P 500 Price Fetcher Test")
    print("="*50)
    
    # Test 1: Get single ticker
    aapl = test_get_ticker_price()
    
    # Test 2: Get all prices
    prices = test_get_all_prices()
    
    # Summary
    print("\n" + "="*50)
    print("Test Summary")
    print("="*50)
    print(f"get_ticker_price: {'✓ PASS' if aapl else '✗ FAIL'}")
    print(f"get_all_prices: {'✓ PASS' if prices else '✗ FAIL'}")
    
    if aapl and prices:
        print("\n✓ All tests passed!")
        print(f"\nPrice file location: backend/data/sp500_latest_prices.json")
        return 0
    else:
        print("\n✗ Some tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

