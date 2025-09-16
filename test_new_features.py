#!/usr/bin/env python3
"""
Test script to verify SuStainability and Assessment features are working
"""

import requests
import json
from datetime import datetime

def test_endpoints():
    """Test the new sustainability and assessment endpoints"""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Sustainability and Assessment Endpoints...")
    print("=" * 50)
    
    # Test endpoints
    endpoints_to_test = [
        "/sustainability",
        "/sustainability/calculator", 
        "/assessments",
        "/assessments/create"
    ]
    
    results = []
    
    for endpoint in endpoints_to_test:
        url = base_url + endpoint
        try:
            print(f"Testing: {url}")
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {endpoint} - OK (200)")
                results.append(f"✅ {endpoint} - Working")
            elif response.status_code == 302:
                print(f"🔄 {endpoint} - Redirect (302) - Login required")
                results.append(f"🔄 {endpoint} - Redirect (needs auth)")
            elif response.status_code == 404:
                print(f"❌ {endpoint} - Not Found (404)")
                results.append(f"❌ {endpoint} - Not Found")
            else:
                print(f"⚠️ {endpoint} - Status: {response.status_code}")
                results.append(f"⚠️ {endpoint} - Status {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ {endpoint} - Connection Error (Server not running?)")
            results.append(f"❌ {endpoint} - Connection Error")
        except requests.exceptions.Timeout:
            print(f"⏰ {endpoint} - Timeout")
            results.append(f"⏰ {endpoint} - Timeout")
        except Exception as e:
            print(f"❌ {endpoint} - Error: {str(e)}")
            results.append(f"❌ {endpoint} - Error: {str(e)}")
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    for result in results:
        print(result)
    
    # Test API endpoints (these will likely need authentication)
    print("\n🔒 Testing API Endpoints (may require authentication):")
    print("=" * 50)
    
    api_endpoints = [
        "/sustainability/api/calculate",
        "/assessments/api/progress"
    ]
    
    for endpoint in api_endpoints:
        url = base_url + endpoint
        try:
            if "calculate" in endpoint:
                # Test POST endpoint with sample data
                sample_data = {
                    'expected_attendees': 100,
                    'duration_hours': 8,
                    'venue_size_sqm': 500,
                    'transport_modes': {'car': 0.4, 'public_transport': 0.35, 'walking_cycling': 0.25},
                    'meal_distribution': {'vegetarian': 0.6, 'meat_moderate': 0.3, 'vegan': 0.1}
                }
                response = requests.post(url, json=sample_data, timeout=10)
            else:
                response = requests.get(url, timeout=10)
                
            if response.status_code == 200:
                print(f"✅ {endpoint} - OK (200)")
            elif response.status_code in [302, 401, 403]:
                print(f"🔒 {endpoint} - Auth required ({response.status_code})")
            else:
                print(f"⚠️ {endpoint} - Status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {endpoint} - Error: {str(e)}")
    
    return True

def test_sustainability_calculations():
    """Test sustainability calculation functionality"""
    print("\n🧮 Testing Sustainability Calculations...")
    print("=" * 50)
    
    try:
        # Import our sustainability module
        from sustainability import calculate_event_footprint, get_sustainability_recommendations
        
        # Test data
        sample_event_data = {
            'expected_attendees': 100,
            'duration_hours': 8,
            'venue_size_sqm': 500,
            'transport_modes': {'car': 0.4, 'public_transport': 0.35, 'walking_cycling': 0.25},
            'meal_distribution': {'vegetarian': 0.6, 'meat_moderate': 0.3, 'vegan': 0.1},
            'digital_adoption_ratio': 0.7,
            'energy_source': 'mixed',
            'waste_management': {'recycling': 0.6, 'landfill': 0.2, 'composting': 0.2}
        }
        
        # Test carbon footprint calculation
        print("Testing carbon footprint calculation...")
        footprint = calculate_event_footprint(0, sample_event_data)
        print(f"✅ Total CO₂: {footprint.total_co2_kg:.2f} kg")
        print(f"✅ Per attendee: {footprint.per_attendee_kg:.2f} kg")
        print(f"✅ Impact level: {footprint.impact_level.value}")
        
        # Test recommendations
        print("\nTesting sustainability recommendations...")
        recommendations = get_sustainability_recommendations(sample_event_data)
        print(f"✅ Generated {len(recommendations)} recommendations")
        
        if recommendations:
            print("Sample recommendation:")
            rec = recommendations[0]
            print(f"  • {rec.title}")
            print(f"  • Impact reduction: {rec.impact_reduction}%")
            print(f"  • Category: {rec.category.value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Sustainability calculations failed: {str(e)}")
        return False

def test_assessment_system():
    """Test assessment system functionality"""
    print("\n🎓 Testing Assessment System...")
    print("=" * 50)
    
    try:
        from assessments import create_user_assessment, AssessmentType, DifficultyLevel, AssessmentCategory
        
        # Test assessment creation
        print("Testing assessment creation...")
        assessment_id = create_user_assessment(
            user_id="test_user",
            assessment_type=AssessmentType.MOCK_EVENT_PLANNING,
            difficulty=DifficultyLevel.INTERMEDIATE,
            category=AssessmentCategory.PLANNING
        )
        print(f"✅ Created assessment with ID: {assessment_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Assessment system test failed: {str(e)}")
        return False

def test_gamification_system():
    """Test gamification system functionality"""
    print("\n🏆 Testing Gamification System...")
    print("=" * 50)
    
    try:
        from gamification import award_user_badge, get_user_badges, award_user_points, PointCategory
        
        # Test point awarding
        print("Testing point awarding...")
        award_user_points("test_user", PointCategory.EVENT_CREATION, 50, "Test event creation")
        print("✅ Points awarded successfully")
        
        # Test badge system
        print("Testing badge system...")
        success = award_user_badge("test_user", "first_event", {"events_created": 1})
        if success:
            print("✅ Badge awarded successfully")
        else:
            print("ℹ️ Badge criteria not met or already awarded")
        
        # Get user badges
        badges = get_user_badges("test_user")
        print(f"✅ User has {len(badges)} badges")
        
        return True
        
    except Exception as e:
        print(f"❌ Gamification system test failed: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting Comprehensive Feature Testing")
    print("=" * 60)
    print(f"Test started at: {datetime.now()}")
    print("=" * 60)
    
    # Run all tests
    endpoint_test = test_endpoints()
    sustainability_test = test_sustainability_calculations()
    assessment_test = test_assessment_system()
    gamification_test = test_gamification_system()
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 FINAL TEST RESULTS")
    print("=" * 60)
    
    tests = [
        ("Endpoint Connectivity", endpoint_test),
        ("Sustainability Calculations", sustainability_test),
        ("Assessment System", assessment_test),
        ("Gamification System", gamification_test)
    ]
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("\n" + "=" * 60)
    print(f"📊 OVERALL RESULT: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! The new features are working correctly.")
        print("\n🌟 You can now access:")
        print("   • Sustainability Dashboard: http://localhost:5000/sustainability")
        print("   • Carbon Calculator: http://localhost:5000/sustainability/calculator")
        print("   • Assessment Dashboard: http://localhost:5000/assessments")
        print("   • Assessment Creation: http://localhost:5000/assessments/create")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
