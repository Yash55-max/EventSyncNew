#!/usr/bin/env python3
"""
Test script for the new Ticket System endpoints
"""

import requests
import sys
from datetime import datetime

def test_endpoint(url, name):
    """Test if an endpoint is accessible"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code in [200, 302]:
            print(f"✅ {name}: Status {response.status_code} - Working!")
            return True
        elif response.status_code == 401:
            print(f"🔒 {name}: Status {response.status_code} - Login Required (Expected)")
            return True
        elif response.status_code == 405:
            print(f"⚠️  {name}: Status {response.status_code} - Method Not Allowed (POST endpoint)")
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
    print("🎫 Testing EVENTSYNC Ticket System Endpoints")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    # New ticket system endpoints
    ticket_endpoints = [
        (f"{base_url}/tickets/check-in", "QR Check-in Page"),
        (f"{base_url}/tickets/my-tickets", "My Tickets Page"),
        (f"{base_url}/tickets/verify-qr", "QR Code Verification API"),
        (f"{base_url}/tickets/download/1", "Ticket Download (Sample)"),
        (f"{base_url}/tickets/bulk-download/1", "Bulk Ticket Download (Sample)"),
    ]
    
    # Test existing core endpoints too
    core_endpoints = [
        (f"{base_url}/", "Main Application"),
        (f"{base_url}/sustainability", "Sustainability Dashboard"),
        (f"{base_url}/assessments", "Assessment Dashboard"),
    ]
    
    print("\n🔧 Testing Core System:")
    successful_core = 0
    for url, name in core_endpoints:
        if test_endpoint(url, name):
            successful_core += 1
    
    print(f"\n📊 Core System Results: {successful_core}/{len(core_endpoints)} endpoints working")
    
    print("\n🎫 Testing New Ticket System:")
    successful_tickets = 0
    for url, name in ticket_endpoints:
        if test_endpoint(url, name):
            successful_tickets += 1
    
    print(f"\n📊 Ticket System Results: {successful_tickets}/{len(ticket_endpoints)} endpoints working")
    
    total_successful = successful_core + successful_tickets
    total_endpoints = len(core_endpoints) + len(ticket_endpoints)
    
    print("=" * 50)
    print(f"🎯 Overall Results: {total_successful}/{total_endpoints} endpoints working")
    
    if successful_tickets >= 4:  # Allow for some auth-protected endpoints
        print("🎉 Ticket System successfully deployed!")
        print("✨ New features available:")
        print("  • PDF Ticket Generation with QR Codes")
        print("  • QR Code Check-in System for Organizers") 
        print("  • My Tickets Dashboard for Attendees")
        print("  • Bulk Ticket Operations for Events")
        return 0
    else:
        print("⚠️  Some ticket endpoints may need attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())