"""
Utility script to validate and inspect fuel data
Run with: python manage.py shell < scripts/load_fuel_data.py
Or: python scripts/load_fuel_data.py
"""
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from core.config import FUEL_DATA_PATH


def validate_fuel_data():
    """Validate fuel data file"""
    print(f"Loading fuel data from: {FUEL_DATA_PATH}")
    
    if not FUEL_DATA_PATH.exists():
        print(f"ERROR: File not found at {FUEL_DATA_PATH}")
        return False
    
    try:
        df = pd.read_csv(FUEL_DATA_PATH)
        print(f"\n✓ Successfully loaded {len(df)} records")
        print(f"\nColumns: {list(df.columns)}")
        print(f"\nSample data:")
        print(df.head())
        
        # Check for missing values
        print(f"\nMissing values per column:")
        print(df.isnull().sum())
        
        # Price statistics
        if 'Retail Price' in df.columns:
            df['Retail Price'] = pd.to_numeric(df['Retail Price'], errors='coerce')
            print(f"\nPrice statistics:")
            print(f"  Min: ${df['Retail Price'].min():.2f}")
            print(f"  Max: ${df['Retail Price'].max():.2f}")
            print(f"  Mean: ${df['Retail Price'].mean():.2f}")
            print(f"  Median: ${df['Retail Price'].median():.2f}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error loading data: {str(e)}")
        return False


if __name__ == '__main__':
    validate_fuel_data()
