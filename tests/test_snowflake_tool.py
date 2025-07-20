#!/usr/bin/env python3
"""
Test script for Snowflake tool integration.
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.tools.database.snowflake_tool import SnowflakeTool

async def test_snowflake_tool():
    """Test the Snowflake tool functionality."""
    print("🧪 Snowflake Tool Test")
    print("=" * 40)
    
    # Create tool instance
    tool = SnowflakeTool()
    
    print(f"Tool Name: {tool.capabilities.name}")
    print(f"Tool Description: {tool.capabilities.description}")
    print("\n🔄 Testing simple query...")
    
    # Test 1: Simple query
    try:
        result = await tool.execute("SELECT CURRENT_DATE() as today, CURRENT_USER() as user_name")
        
        if result.status.name == "SUCCESS":
            print("✅ Simple query successful!")
            print(f"   Result: {result.data['rows'][0]}")
        else:
            print(f"❌ Simple query failed: {result.data}")
            
    except Exception as e:
        print(f"❌ Error during simple query: {e}")
    
    print("\n🔄 Testing schema info...")
    
    # Test 2: Schema info (if method exists)
    try:
        if hasattr(tool, 'get_schema_info'):
            schema_result = tool.get_schema_info()
            
            if schema_result.status.name == "SUCCESS":
                print("✅ Schema info retrieval successful!")
                print(f"   Found {schema_result.data['table_count']} tables in {schema_result.data['schema_count']} schemas")
            else:
                print(f"❌ Schema info failed: {schema_result.data}")
        else:
            print("ℹ️  Schema info method not available")
            
    except Exception as e:
        print(f"❌ Error during schema info: {e}")
    
    print("=" * 40)

if __name__ == "__main__":
    asyncio.run(test_snowflake_tool())
