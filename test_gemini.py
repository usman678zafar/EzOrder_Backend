#!/usr/bin/env python3
"""
Test Gemini API connection
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_gemini_api():
    """Test Gemini API with current credentials"""
    api_key = os.getenv("GEMINI_API_KEY")
    base_url = os.getenv("GEMINI_BASE_URL")
    model_name = os.getenv("MODEL_NAME")
    
    print(f"Testing Gemini API...")
    print(f"API Key: {api_key[:20]}...")
    print(f"Base URL: {base_url}")
    print(f"Model: {model_name}")
    
    # Test API endpoint
    try:
        url = f"{base_url}chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model_name,
            "messages": [
                {"role": "user", "content": "Hello, this is a test message."}
            ],
            "max_tokens": 50
        }
        
        print(f"\n[TEST] Testing API endpoint: {url}")
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("[SUCCESS] Gemini API is working!")
            print(f"Response: {data}")
            return True
        else:
            print(f"[ERROR] API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Connection error: {e}")
        return False

if __name__ == "__main__":
    test_gemini_api()
