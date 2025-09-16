#!/usr/bin/env python3
"""
Quick live endpoint test for running Flask server
"""
import requests
import sys

def test_endpoint(url, name):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code in [200, 302]:
            print(f"✅ {name}: Status {response.status_code} - Working!")
            return True
        else:
            print(f"⚠️  {name}: Status {response.status_code} - Unexpected")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ {name}: Connection failed - Server not running")
        return False
    except Exception as e:
        print(f"❌ {name}: Error - {e}")
        return False

def main():
    print("🧪 Testing Live EVENTSYNC Endpoints")
    print("=" * 40)
    
    base_url = "http://localhost:5000"
    endpoints = [
        (f"{base_url}/", "Main App"),
        (f"{base_url}/sustainability", "Sustainability Dashboard"),
        (f"{base_url}/sustainability/calculator", "Carbon Calculator"),
        (f"{base_url}/assessments", "Assessment Dashboard"),
        (f"{base_url}/assessments/create", "Assessment Creator"),
        (f"{base_url}/admin", "Admin Panel")
    ]
    
    successful = 0
    total = len(endpoints)
    
    for url, name in endpoints:
        if test_endpoint(url, name):
            successful += 1
    
    print("=" * 40)
    print(f"🎯 Results: {successful}/{total} endpoints working")
    
    if successful == total:
        print("🎉 All endpoints are live and accessible!")
        print("✨ New features successfully deployed!")
    else:
        print("⚠️  Some endpoints may need attention")
    
    return 0 if successful == total else 1

if __name__ == "__main__":
    sys.exit(main())