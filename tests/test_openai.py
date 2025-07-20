#!/usr/bin/env python3
"""
Simple test script to verify OpenAI API key is working correctly.
"""

import os
from dotenv import load_dotenv

def test_openai_api():
    """Test the OpenAI API key and connection."""
    
    # Load environment variables
    load_dotenv()
    
    # Check if API key is loaded
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        return False
    
    if api_key == 'your_openai_api_key_here':
        print("❌ Error: OPENAI_API_KEY is still the placeholder value")
        return False
    
    print(f"✅ API Key found: {api_key[:20]}...{api_key[-10:]} (partially hidden)")
    
    # Test the API connection
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=api_key)
        
        print("🔄 Testing OpenAI API connection...")
        
        # Simple test request
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Using cheaper model for testing
            messages=[
                {"role": "user", "content": "Say 'Hello, OpenAI API is working!' in exactly 5 words."}
            ],
            max_tokens=50,
            temperature=0
        )
        
        result = response.choices[0].message.content.strip()
        print(f"✅ OpenAI API Response: {result}")
        print("🎉 OpenAI API is working correctly!")
        return True
        
    except ImportError:
        print("❌ Error: OpenAI library not installed. Run: pip install openai")
        return False
    except Exception as e:
        print(f"❌ Error testing OpenAI API: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 OpenAI API Test")
    print("=" * 30)
    success = test_openai_api()
    print("=" * 30)
    if success:
        print("✅ Test completed successfully!")
    else:
        print("❌ Test failed. Please check your configuration.")
