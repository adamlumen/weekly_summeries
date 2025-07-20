#!/usr/bin/env python3
"""
Debug script to test Pydantic settings with .env
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional

class TestSettings(BaseSettings):
    """Test settings."""
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8", 
        case_sensitive=False,
        extra="allow"
    )
    
    # OpenAI settings  
    openai_api_key: str = "test"
    
    # Snowflake settings
    snowflake_account: Optional[str] = None
    snowflake_user: Optional[str] = None
    snowflake_role: Optional[str] = None
    snowflake_warehouse: Optional[str] = None
    snowflake_database: Optional[str] = None
    snowflake_authenticator: str = "externalbrowser"

def main():
    """Test settings loading."""
    print("🧪 Testing Pydantic Settings")
    print("=" * 40)
    
    try:
        settings = TestSettings()
        print("✅ Settings loaded successfully")
        print(f"Snowflake Account: {settings.snowflake_account}")
        print(f"Snowflake User: {settings.snowflake_user}")
    except Exception as e:
        print(f"❌ Error loading settings: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
