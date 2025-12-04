"""
test_env_fmp_key.py — Test script to verify FMP_API_KEY is loaded from .env file.

This script loads the .env file and reads the FMP_API_KEY to verify it's set correctly.
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    print("ERROR: python-dotenv is not installed. Install with: pip install python-dotenv")
    exit(1)


def main():
    """Load .env and test FMP_API_KEY."""
    # Find .env file in project root
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    
    if not env_file.exists():
        print(f"WARNING: .env file not found at {env_file}")
        print("Creating a template .env file...")
        print("\nPlease add your FMP API key to the .env file:")
        print("FMP_API_KEY=your-api-key-here")
        return
    
    # Load .env file
    load_dotenv(env_file)
    
    # Read FMP_API_KEY
    api_key_path_or_value = os.getenv("FMP_API_KEY")
    
    if not api_key_path_or_value:
        print("ERROR: FMP_API_KEY not found in .env file")
        print(f"\nPlease add it to {env_file}:")
        print("FMP_API_KEY=your-api-key-here")
        print("OR")
        print("FMP_API_KEY=C:\\path\\to\\key.txt")
        return
    
    # Check if it's a file path
    is_file_path = (
        "\\" in api_key_path_or_value or 
        "/" in api_key_path_or_value or
        api_key_path_or_value.endswith(".txt") or
        api_key_path_or_value.endswith(".key")
    )
    
    if is_file_path:
        # Read from file
        key_file = Path(api_key_path_or_value).expanduser()
        if not key_file.exists():
            print(f"ERROR: FMP_API_KEY file not found: {key_file}")
            return
        
        try:
            with key_file.open("r", encoding="utf-8") as f:
                api_key = f.read().strip()
            
            if not api_key:
                print(f"ERROR: FMP_API_KEY file is empty: {key_file}")
                return
            
            print(f"✓ Successfully loaded FMP_API_KEY from file")
            print(f"  .env file: {env_file}")
            print(f"  Key file: {key_file}")
            print(f"  Key length: {len(api_key)} characters")
            
            # Show first and last few characters for security
            if len(api_key) > 8:
                masked = f"{api_key[:4]}...{api_key[-4:]}"
            else:
                masked = "***"
            print(f"  Key preview: {masked}")
            print(f"\n✓ FMP_API_KEY is ready to use!")
        
        except Exception as e:
            print(f"ERROR: Failed to read FMP_API_KEY from file {key_file}: {e}")
            return
    else:
        # Direct API key value
        api_key = api_key_path_or_value.strip()
        
        # Show first and last few characters for security
        if len(api_key) > 8:
            masked = f"{api_key[:4]}...{api_key[-4:]}"
        else:
            masked = "***"
        
        print(f"✓ Successfully loaded FMP_API_KEY from .env file")
        print(f"  File: {env_file}")
        print(f"  Key length: {len(api_key)} characters")
        print(f"  Key preview: {masked}")
        print(f"\n✓ FMP_API_KEY is ready to use!")


if __name__ == "__main__":
    main()

