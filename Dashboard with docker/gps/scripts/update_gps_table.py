#!/usr/bin/env python3
"""
Update the gps_data table schema to include columns needed for GPS jamming detection.
"""
import MySQLdb
import sys
import os

# MySQL database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'dashboard',
    'passwd': 'securepass',
    'db': 'security_dashboard',
}

def update_gps_table():
    """Add columns to the gps_data table for jamming detection"""
    
    print(f"Updating MySQL database schema...")
    
    conn = None
    try:
        conn = MySQLdb.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check if the table exists
        cursor.execute("SHOW TABLES LIKE 'gps_data'")
        if not cursor.fetchone():
            print("Creating gps_data table...")
            cursor.execute("""
            CREATE TABLE gps_data (
                id VARCHAR(36) PRIMARY KEY,
                latitude FLOAT NOT NULL,
                longitude FLOAT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                device_id VARCHAR(100),
                satellites INT,
                hdop FLOAT,
                jamming_detected BOOLEAN DEFAULT FALSE
            )
            """)
            print("Table created successfully.")
            return True
            
        # Get existing columns
        cursor.execute("DESCRIBE gps_data")
        columns = [row[0] for row in cursor.fetchall()]
        
        # Add satellites column if it doesn't exist
        if 'satellites' not in columns:
            print("Adding 'satellites' column...")
            cursor.execute("ALTER TABLE gps_data ADD COLUMN satellites INT")
        
        # Add hdop column if it doesn't exist
        if 'hdop' not in columns:
            print("Adding 'hdop' column...")
            cursor.execute("ALTER TABLE gps_data ADD COLUMN hdop FLOAT")
        
        # Add jamming_detected column if it doesn't exist
        if 'jamming_detected' not in columns:
            print("Adding 'jamming_detected' column...")
            cursor.execute("ALTER TABLE gps_data ADD COLUMN jamming_detected BOOLEAN DEFAULT FALSE")
        
        conn.commit()
        print("Database schema updated successfully.")
        return True
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    update_gps_table()
