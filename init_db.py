# init_db.py
import os
import sys

# Add current directory to path
current_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, current_dir)
print(f"Added {current_dir} to Python path")

try:
    from app import db, app
    print("Successfully imported db and app")
    
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully!")
except ImportError as e:
    print(f"Import error: {e}")
    print("Files in current directory:")
    for file in os.listdir(current_dir):
        print(f"  - {file}")