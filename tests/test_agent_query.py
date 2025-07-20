#!/usr/bin/env python3
"""
Test script to query the agent about available tables
"""

import json
import requests

def test_agent_query():
    """Test querying the agent about available tables."""
    
    url = "http://localhost:8002/agent/process"
    
    payload = {
        "user_request": "What tables are available in Snowflake?"
    }
    
    print("🤖 Testing Agent Query: 'What tables are available in the database?'")
    print("=" * 70)
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Agent Response:")
            print(f"Response: {result.get('response', 'No response')}")
            
            if 'tools_used' in result:
                print(f"\n🔧 Tools Used: {result['tools_used']}")
            
            if 'tool_results' in result:
                print("\n📊 Tool Results:")
                tool_results = result['tool_results']
                if isinstance(tool_results, list):
                    for tool_result in tool_results:
                        if isinstance(tool_result, dict):
                            tool_name = tool_result.get('tool_name', 'Unknown')
                            status = tool_result.get('status', 'Unknown')
                            data = tool_result.get('data', {})
                            print(f"  {tool_name} ({status}): Found {len(data.get('tables', []))} items")
                        else:
                            print(f"  Result: {tool_result}")
                else:
                    print(f"  Results: {tool_results}")
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            print(f"Error details: {response.text}")
                    
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    test_agent_query()
