"""
Test script for Calendar system endpoints
Tests all calendar API endpoints to ensure they're working correctly
"""
import requests
import json
from datetime import datetime, timedelta

def test_endpoint(url, description):
    """Test an endpoint and return the result"""
    print(f"\n🔍 Testing: {description}")
    print(f"   URL: {url}")
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {response.status_code}")
            print(f"   📊 Response Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            
            # Show some data details
            if isinstance(data, dict):
                if 'success' in data:
                    print(f"   📈 Success: {data['success']}")
                if 'statistics' in data:
                    stats = data['statistics']
                    print(f"   📊 Stats: Total={stats.get('total_events', 0)}, Upcoming={stats.get('upcoming_events', 0)}")
                if 'categories' in data:
                    print(f"   🏷️ Categories: {len(data['categories'])} found")
                if 'data' in data:
                    print(f"   📅 Data: {type(data['data'])}")
                if 'results' in data:
                    print(f"   🔍 Search Results: {len(data['results'])} found")
                    
            return True
        else:
            print(f"   ❌ Status: {response.status_code}")
            print(f"   📄 Response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error: {str(e)}")
        return False
    except Exception as e:
        print(f"   ❌ JSON Error: {str(e)}")
        return False

def main():
    """Test all calendar endpoints"""
    print("🧪 EVENTSYNC Calendar System - Endpoint Testing")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    # List of endpoints to test
    endpoints = [
        # Main calendar page
        (f"{base_url}/calendar/", "Calendar Main Page"),
        
        # API endpoints
        (f"{base_url}/calendar/api/statistics", "Calendar Statistics API"),
        (f"{base_url}/calendar/api/categories", "Event Categories API"),
        
        # Calendar view APIs
        (f"{base_url}/calendar/api/month-view?year=2024&month=1", "Month View API (January 2024)"),
        (f"{base_url}/calendar/api/week-view", "Week View API (Current week)"),
        (f"{base_url}/calendar/api/day-view", "Day View API (Today)"),
        
        # Date-specific views
        (f"{base_url}/calendar/api/day-view?date=2024-01-15", "Day View API (January 15, 2024)"),
        (f"{base_url}/calendar/api/week-view?week_start=2024-01-15", "Week View API (Week of Jan 15, 2024)"),
        
        # Search API
        (f"{base_url}/calendar/api/search?q=test", "Search API (query: test)"),
        (f"{base_url}/calendar/api/search?q=event", "Search API (query: event)"),
        (f"{base_url}/calendar/api/search?q=conference", "Search API (query: conference)"),
    ]
    
    results = []
    
    # Test each endpoint
    for url, description in endpoints:
        success = test_endpoint(url, description)
        results.append((description, success))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {description}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\n📈 Total: {len(results)} tests")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"🎯 Success Rate: {passed/len(results)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 All calendar endpoints are working perfectly!")
        print("✨ The Mobile-Responsive Event Calendar feature is ready to use!")
    else:
        print(f"\n⚠️  {failed} endpoint(s) need attention")
        print("💡 Make sure the Flask application is running on http://localhost:5000")
        print("💡 Check that all required dependencies are installed")
        print("💡 Verify the database contains some sample events for testing")

if __name__ == "__main__":
    main()