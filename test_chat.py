#!/usr/bin/env python3
"""
Test script for chat room creation functionality
"""

import os
import sys

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from database import db
from models import User
from chat_manager import get_chat_manager
from models_chat import ChatRoomType


def test_room_creation():
    """Test room creation functionality"""
    
    with app.app_context():
        # Get the first user (or create a test user)
        user = User.query.first()
        
        if not user:
            print("❌ No users found. Please create a user first through the web interface.")
            return False
            
        print(f"✓ Testing with user: {user.username} (ID: {user.id})")
        
        # Get chat manager
        chat_manager = get_chat_manager()
        
        # Test room creation
        try:
            result = chat_manager.create_room(
                name="Test Room - Auto Created",
                creator_id=user.id,
                room_type=ChatRoomType.GENERAL,
                description="This is a test room created by the test script",
                event_id=None,
                settings={
                    'is_public': True,
                    'allow_file_sharing': True
                }
            )
            
            if result['success']:
                room = result['room']
                print(f"✅ Room created successfully!")
                print(f"   - Room ID: {room['id']}")
                print(f"   - Room Name: {room['name']}")
                print(f"   - Room Type: {room['room_type']}")
                print(f"   - Participants: {room['participant_count']}")
                return True
            else:
                print(f"❌ Room creation failed: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ Exception during room creation: {e}")
            import traceback
            traceback.print_exc()
            return False


def test_room_listing():
    """Test room listing functionality"""
    
    with app.app_context():
        user = User.query.first()
        
        if not user:
            print("❌ No users found for room listing test")
            return False
            
        chat_manager = get_chat_manager()
        
        try:
            rooms = chat_manager.get_user_rooms(user.id)
            print(f"✓ User has {len(rooms)} rooms:")
            
            for room in rooms:
                print(f"   - {room['name']} (ID: {room['id']}) - {room['room_type']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Exception during room listing: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main test function"""
    print("🧪 Testing EVENTSYNC Chat Room Creation")
    print("=" * 50)
    
    # Test 1: Room Creation
    print("\n📝 Test 1: Room Creation")
    creation_success = test_room_creation()
    
    # Test 2: Room Listing
    print("\n📋 Test 2: Room Listing")
    listing_success = test_room_listing()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"   Room Creation: {'✅ PASS' if creation_success else '❌ FAIL'}")
    print(f"   Room Listing:  {'✅ PASS' if listing_success else '❌ FAIL'}")
    
    if creation_success and listing_success:
        print("\n🎉 All tests passed! Room creation is working correctly.")
        print("💡 You can now use the web interface to create rooms.")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")
    
    return creation_success and listing_success


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)