"""
Integration script to add Sustainability and Assessment features to the Event Management System
Run this script to integrate the new features with the main Flask application
"""

import os
import sys
from pathlib import Path

def integrate_sustainability_and_assessments():
    """
    Integrate sustainability tracking and assessment systems into the main Flask app
    """
    
    print("🚀 Starting integration of Sustainability and Assessment features...")
    
    # Check if main app.py exists
    app_path = Path("app.py")
    if not app_path.exists():
        print("❌ app.py not found. Please run this script from the project root directory.")
        return False
    
    try:
        # Read current app.py content
        with open(app_path, 'r', encoding='utf-8') as f:
            app_content = f.read()
        
        # Check if sustainability routes are already integrated
        if 'register_sustainability_routes' in app_content:
            print("✅ Sustainability and Assessment features appear to be already integrated.")
            return True
        
        # Prepare the integration code
        integration_code = """
# Import sustainability and assessment routes
try:
    from sustainability_routes import register_sustainability_routes, register_assessment_routes
    SUSTAINABILITY_AVAILABLE = True
except ImportError:
    print("⚠️  Sustainability and Assessment modules not found. Some features will be unavailable.")
    SUSTAINABILITY_AVAILABLE = False

# Register sustainability and assessment routes (add this after other route registrations)
if SUSTAINABILITY_AVAILABLE:
    register_sustainability_routes(app)
    register_assessment_routes(app)
    print("✅ Sustainability and Assessment routes registered successfully")
"""
        
        # Find the right place to insert the code (before if __name__ == '__main__':)
        if 'if __name__ == \'__main__\':' in app_content:
            # Insert before the main block
            main_block_index = app_content.find('if __name__ == \'__main__\':')
            new_content = (
                app_content[:main_block_index] + 
                integration_code + "\n\n" + 
                app_content[main_block_index:]
            )
        else:
            # Append to the end
            new_content = app_content + "\n\n" + integration_code
        
        # Write the updated content back
        with open(app_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Successfully integrated sustainability and assessment routes into app.py")
        
        # Check and create necessary template directories
        create_template_directories()
        
        # Update navigation if base template exists
        update_navigation()
        
        print("🎉 Integration completed successfully!")
        print("\n📝 Next steps:")
        print("1. Install any missing dependencies (if any)")
        print("2. Run the application: python app.py")
        print("3. Navigate to /sustainability or /assessments to try the new features")
        print("4. Check that all templates render correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during integration: {str(e)}")
        return False

def create_template_directories():
    """Ensure template directories exist"""
    template_dirs = [
        "templates/sustainability",
        "templates/assessments"
    ]
    
    for dir_path in template_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ Template directory created/verified: {dir_path}")

def update_navigation():
    """Update navigation in base template to include new features"""
    base_template_path = Path("templates/base.html")
    
    if not base_template_path.exists():
        print("⚠️  Base template not found. You'll need to manually add navigation links.")
        return
    
    try:
        with open(base_template_path, 'r', encoding='utf-8') as f:
            base_content = f.read()
        
        # Check if navigation already updated
        if 'sustainability' in base_content.lower() and 'assessments' in base_content.lower():
            print("✅ Navigation appears to already include sustainability and assessments links.")
            return
        
        # Look for navigation section to add new menu items
        nav_items = '''
                        <li class="nav-item">
                            <a class="nav-link" href="{{ url_for('sustainability.dashboard') }}">
                                <i class="fas fa-leaf mr-2"></i>Sustainability
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="{{ url_for('assessments.dashboard') }}">
                                <i class="fas fa-graduation-cap mr-2"></i>Assessments
                            </a>
                        </li>'''
        
        # Try to find and update navigation
        if '<ul class="navbar-nav' in base_content:
            # Find the closing </ul> of the navigation
            nav_start = base_content.find('<ul class="navbar-nav')
            nav_end = base_content.find('</ul>', nav_start)
            
            if nav_start != -1 and nav_end != -1:
                # Insert new nav items before closing </ul>
                updated_content = (
                    base_content[:nav_end] + 
                    nav_items + "\n                    " +
                    base_content[nav_end:]
                )
                
                with open(base_template_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                
                print("✅ Navigation updated with sustainability and assessments links")
                return
        
        print("⚠️  Could not automatically update navigation. Please manually add links to:")
        print("   - /sustainability (Sustainability Dashboard)")
        print("   - /assessments (Assessment Dashboard)")
        
    except Exception as e:
        print(f"⚠️  Could not update navigation: {str(e)}")

def create_sample_data():
    """Create some sample data for demonstration"""
    print("📊 Creating sample data for demonstration...")
    
    sample_data_script = '''
"""
Sample data initialization for Sustainability and Assessment features
"""

from sustainability import sustainability_tracker, SustainabilityTracker
from assessments import assessment_manager, AssessmentManager  
from gamification import gamification_system, award_user_points, PointCategory
from datetime import datetime

def initialize_sample_data():
    """Initialize sample data for demo purposes"""
    
    # Sample user ID (replace with actual user ID from your system)
    sample_user_id = "user_123"
    
    # Initialize sample sustainability data
    sample_event_data = {
        'expected_attendees': 150,
        'duration_hours': 8,
        'venue_size_sqm': 400,
        'transport_modes': {'car': 0.4, 'public_transport': 0.35, 'walking_cycling': 0.25},
        'meal_distribution': {'vegetarian': 0.6, 'meat_moderate': 0.3, 'vegan': 0.1},
        'digital_adoption_ratio': 0.8,
        'energy_source': 'mixed',
        'waste_management': {'recycling': 0.6, 'landfill': 0.2, 'composting': 0.2}
    }
    
    print("✅ Sample sustainability data prepared")
    
    # Award some sample points
    award_user_points(sample_user_id, PointCategory.EVENT_CREATION, 50, "Created first event")
    award_user_points(sample_user_id, PointCategory.SUSTAINABILITY_ACTION, 75, "Used carbon calculator")
    
    print("✅ Sample gamification data created")
    
    return True

if __name__ == "__main__":
    initialize_sample_data()
    print("🎉 Sample data initialization completed!")
'''
    
    with open("initialize_sample_data.py", 'w', encoding='utf-8') as f:
        f.write(sample_data_script)
    
    print("✅ Sample data script created: initialize_sample_data.py")

def verify_files():
    """Verify that all necessary files are in place"""
    required_files = [
        "sustainability.py",
        "assessments.py", 
        "gamification.py",
        "sustainability_routes.py",
        "templates/sustainability/dashboard.html",
        "templates/sustainability/calculator.html",
        "templates/assessments/dashboard.html",
        "templates/assessments/create.html"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing required files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    else:
        print("✅ All required files are present")
        return True

def main():
    """Main integration function"""
    print("=" * 60)
    print("🎯 Event Management System - Feature Integration")
    print("   Adding: Sustainability Tracking & Practical Assessments")
    print("=" * 60)
    
    # Verify all files are present
    if not verify_files():
        print("\n❌ Integration aborted due to missing files.")
        print("Please ensure all required files are in place before running integration.")
        return
    
    # Perform integration
    if integrate_sustainability_and_assessments():
        create_sample_data()
        
        print("\n" + "=" * 60)
        print("🎉 INTEGRATION SUCCESSFUL!")
        print("=" * 60)
        print("Your Event Management System now includes:")
        print("✅ Sustainability Tracking System")
        print("   - Carbon footprint calculator")
        print("   - Eco-friendly recommendations")
        print("   - Green metrics dashboard")
        print("")
        print("✅ Practical Assessment System")
        print("   - Mock event planning scenarios")
        print("   - AI-powered feedback")
        print("   - Skill assessment and progress tracking")
        print("")
        print("✅ Gamification System")
        print("   - Achievement badges")
        print("   - Points and levels")
        print("   - Progress tracking")
        print("")
        print("🚀 Ready to launch! Run: python app.py")
        print("=" * 60)
    else:
        print("\n❌ Integration failed. Please check the errors above.")

if __name__ == "__main__":
    main()