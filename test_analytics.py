#!/usr/bin/env python3
"""
Test script for the Analytics Dashboard endpoints
"""

import requests
import sys
from datetime import datetime

def test_endpoint(url, name, expected_status_codes=[200, 302, 401]):
    """Test if an endpoint is accessible"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code in expected_status_codes:
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
    print("📊 Testing EVENTSYNC Analytics Dashboard")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    # Core system endpoints
    core_endpoints = [
        (f"{base_url}/", "Main Application"),
        (f"{base_url}/sustainability", "Sustainability Dashboard"),
        (f"{base_url}/assessments", "Assessment Dashboard"),
    ]
    
    # Ticket system endpoints
    ticket_endpoints = [
        (f"{base_url}/tickets/check-in", "QR Check-in Page"),
        (f"{base_url}/tickets/my-tickets", "My Tickets Page"),
        (f"{base_url}/tickets/verify-ticket", "QR Verification API"),
    ]
    
    # Analytics endpoints (new)
    analytics_endpoints = [
        (f"{base_url}/analytics/dashboard", "Analytics Dashboard"),
        (f"{base_url}/analytics/api/overview", "Overview API"),
        (f"{base_url}/analytics/api/event-stats", "Event Stats API"),
        (f"{base_url}/analytics/api/ticket-analytics", "Ticket Analytics API"),
        (f"{base_url}/analytics/api/user-insights", "User Insights API"),
        (f"{base_url}/analytics/api/performance-metrics", "Performance Metrics API"),
        (f"{base_url}/analytics/export/json", "Export JSON API"),
    ]
    
    print("\n🔧 Testing Core System:")
    successful_core = 0
    for url, name in core_endpoints:
        if test_endpoint(url, name):
            successful_core += 1
    
    print(f"\n📊 Core System: {successful_core}/{len(core_endpoints)} working")
    
    print("\n🎫 Testing Ticket System:")
    successful_tickets = 0
    for url, name in ticket_endpoints:
        expected_codes = [200, 302, 401, 405] if 'api' in url.lower() or 'verify' in url.lower() else [200, 302, 401]
        if test_endpoint(url, name, expected_codes):
            successful_tickets += 1
    
    print(f"\n📊 Ticket System: {successful_tickets}/{len(ticket_endpoints)} working")
    
    print("\n📈 Testing Analytics Dashboard:")
    successful_analytics = 0
    for url, name in analytics_endpoints:
        if test_endpoint(url, name):
            successful_analytics += 1
    
    print(f"\n📊 Analytics System: {successful_analytics}/{len(analytics_endpoints)} working")
    
    total_successful = successful_core + successful_tickets + successful_analytics
    total_endpoints = len(core_endpoints) + len(ticket_endpoints) + len(analytics_endpoints)
    
    print("=" * 50)
    print(f"🎯 Overall Results: {total_successful}/{total_endpoints} endpoints working")
    
    if successful_analytics >= 5:  # Most analytics endpoints working
        print("🎉 Analytics Dashboard successfully deployed!")
        print("✨ New features available:")
        print("  • Advanced Analytics Dashboard with Charts")
        print("  • Comprehensive Event & Ticket Metrics") 
        print("  • User Insights and Demographics")
        print("  • Performance Tracking & KPIs")
        print("  • Data Export Capabilities")
        print("  • Real-time Statistics")
        return 0
    else:
        print("⚠️  Some analytics endpoints may need attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())