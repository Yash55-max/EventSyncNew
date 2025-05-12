import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app import app, db

with app.app_context():
    db.create_all()
    print("Database tables created successfully!")