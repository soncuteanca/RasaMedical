#!/usr/bin/env python3
"""
Database migration script to add missing updated_at column
"""

import sys
import os

# Add the project root to Python path so we can import from actions
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from actions.db_connect import db_manager

def migrate_database():
    """Add missing updated_at column to appointments table"""
    try:
        print("🔍 Checking if updated_at column exists...")
        
        # Check if column already exists
        check_query = """
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'medical_bot' 
            AND TABLE_NAME = 'appointments' 
            AND COLUMN_NAME = 'updated_at'
        """
        
        result = db_manager.execute_query(check_query)
        
        if result:
            print("✅ updated_at column already exists")
            return True
        
        print("➕ Adding updated_at column...")
        
        # Add the column
        alter_query = """
            ALTER TABLE appointments 
            ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        """
        
        db_manager.execute_query(alter_query, fetch=False)
        print("✅ Successfully added updated_at column to appointments table")
        
        # Verify the column was added
        verify_result = db_manager.execute_query(check_query)
        if verify_result:
            print("✅ Column addition verified!")
            return True
        else:
            print("❌ Column addition verification failed")
            return False
        
    except Exception as e:
        print(f"❌ Error migrating database: {str(e)}")
        return False

def check_database_connection():
    """Test database connection"""
    try:
        print("🔗 Testing database connection...")
        result = db_manager.execute_query("SELECT 1 as test")
        if result and result[0]['test'] == 1:
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database connection test failed")
            return False
    except Exception as e:
        print(f"❌ Database connection error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔄 Running database migration...")
    print("=" * 50)
    
    # First test connection
    if not check_database_connection():
        print("❌ Cannot proceed without database connection")
        sys.exit(1)
    
    # Run migration
    success = migrate_database()
    
    print("=" * 50)
    if success:
        print("✅ Database migration completed successfully!")
    else:
        print("❌ Database migration failed!")
        sys.exit(1) 