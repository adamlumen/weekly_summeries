#!/usr/bin/env python3
"""
Test script to verify Snowflake configuration and connection.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.tools.database.utilities import get_snowflake_settings, test_snowflake_connection

def main():
    """Test Snowflake connection with environment variables."""
    print("🧪 Snowflake Configuration Test")
    print("=" * 40)
    
    # Get settings from environment
    sf_settings = get_snowflake_settings()
    
    print("Snowflake Settings:")
    for key, value in sf_settings.items():
        if key == 'user':
            print(f"  {key}: {value}")
        else:
            print(f"  {key}: {value}")
    
    print("\n🔄 Testing Snowflake connection...")
    
    try:
        success = test_snowflake_connection(sf_settings)
        if success:
            print("✅ Snowflake connection test successful!")
        else:
            print("❌ Snowflake connection test failed!")
    except Exception as e:
        print(f"❌ Error during connection test: {e}")
        print("Note: External browser authentication may require manual browser interaction.")
        
    print("=" * 40)

if __name__ == "__main__":
    main()
