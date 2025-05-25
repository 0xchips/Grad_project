#!/usr/bin/env python3
"""
Clear GPS Data Script
This script provides a function to clear GPS data from the database
"""

import MySQLdb
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("GPS_Clear_Data")

# MySQL Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'dashboard',
    'passwd': 'securepass',
    'db': 'security_dashboard',
}

def clear_gps_data():
    """Clear all GPS data from the database"""
    try:
        conn = MySQLdb.connect(**DB_CONFIG)
        c = conn.cursor()
        
        # Delete all records from the gps_data table
        c.execute("DELETE FROM gps_data")
        
        # Get count of deleted rows
        deleted_count = c.rowcount
        
        conn.commit()
        conn.close()
        
        logger.info(f"Cleared {deleted_count} GPS records from database")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error clearing GPS data: {e}")
        return -1

if __name__ == "__main__":
    # When run directly, clear the data
    cleared = clear_gps_data()
    if cleared >= 0:
        print(f"Successfully cleared {cleared} GPS records from the database.")
    else:
        print("Failed to clear GPS records.")
