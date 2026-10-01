#!/usr/bin/env python3
"""
Test script for Chat API
Run: python test_chat_api.py
"""

import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

BASE_URL = "http://localhost:8000"

def test_chat_status():
    """Test /chat/status endpoint"""
    print("\n" + "="*50)
    print("TEST 1: Chat Status Check")
    print("="*50)
    try:
        response = requests.get(f"{BASE_URL}/chat/status")
        data = response.json()
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(data, indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_chat_simple():
    """Test /chat/test endpoint (simple test without MCP)"""
    print("\n" + "="*50)
    print("TEST 2: Simple Chat Test")
    print("="*50)
    try:
        response = requests.post(
            f"{BASE_URL}/chat/test",
            params={"message": "Bonjour, comment allez-vous?"}
        )
        data = response.json()
        print(f"Status: {response.status_code}")
        print(f"Request: {response.request.url}")
        print(f"Response: {json.dumps(data, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_chat_main():
    """Test /chat endpoint (main chat)"""
    print("\n" + "="*50)
    print("TEST 3: Main Chat Endpoint")
    print("="*50)
    try:
        payload = {
            "message": "Quel est mon statut WiFi?",
            "history": [],
            "gateway_id": 1
        }
        print(f"Request payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            f"{BASE_URL}/chat",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        data = response.json()
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    print("\n" + "="*70)
    print("HGW CHAT API TEST SUITE")
    print("="*70)
    print(f"Base URL: {BASE_URL}")
    print(f"Groq API Key: {'SET' if os.getenv('GROQ_API_KEY') else 'NOT SET'}")
    
    results = []
    
    results.append(("Status Check", test_chat_status()))
    results.append(("Simple Chat", test_chat_simple()))
    results.append(("Main Chat", test_chat_main()))
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:<30} {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")


if __name__ == "__main__":
    main()
