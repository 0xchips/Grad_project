#!/usr/bin/env python3
"""
Database Connection Tester
Verifies connection to the dashboard database and checks for required tables
"""

import MySQLdb
import sys
import argparse
import uuid
from datetime import datetime

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'dashboard',
    'passwd': 'securepass',
    'db': 'security_dashboard',
}

def test_connection():
    """Test basic database connection"""
    print("[*] Testing database connection...")
    
    try:
        conn = MySQLdb.connect(**db_config)
        print("[+] Connection successful!")
        conn.close()
        return True
    except Exception as e:
        print(f"[!] Connection failed: {str(e)}")
        return False

def check_tables():
    """Check if required tables exist"""
    print("[*] Checking for required tables...")
    
    try:
        conn = MySQLdb.connect(**db_config)
        cursor = conn.cursor()
        
        # Check for the network_attacks table
        cursor.execute("SHOW TABLES LIKE 'network_attacks'")
        if cursor.fetchone():
            print("[+] network_attacks table exists")
            
            # Check table structure
            cursor.execute("DESCRIBE network_attacks")
            columns = [row[0] for row in cursor.fetchall()]
            
            required_columns = [
                'id', 'timestamp', 'alert_type', 'attacker_bssid', 
                'attacker_ssid', 'destination_bssid', 'destination_ssid', 
                'attack_count'
            ]
            
            missing_columns = [col for col in required_columns if col not in columns]
            
            if missing_columns:
                print(f"[!] Missing columns: {', '.join(missing_columns)}")
            else:
                print("[+] All required columns exist")
        else:
            print("[!] network_attacks table does not exist")
            create_table = input("Create table? (y/n): ")
            
            if create_table.lower() == 'y':
                create_network_attacks_table(cursor)
        
        conn.close()
        return True
    except Exception as e:
        print(f"[!] Error checking tables: {str(e)}")
        return False

def create_network_attacks_table(cursor):
    """Create the network_attacks table"""
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS network_attacks (
                id VARCHAR(36) PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                alert_type VARCHAR(100) NOT NULL,
                attacker_bssid VARCHAR(17),
                attacker_ssid VARCHAR(255),
                destination_bssid VARCHAR(17),
                destination_ssid VARCHAR(255),
                attack_count INT DEFAULT 1,
                source_ip VARCHAR(45),
                INDEX idx_timestamp (timestamp),
                INDEX idx_alert_type (alert_type),
                INDEX idx_attacker_bssid (attacker_bssid)
            )
        """)
        print("[+] network_attacks table created successfully")
        return True
    except Exception as e:
        print(f"[!] Error creating table: {str(e)}")
        return False

def insert_test_data():
    """Insert a test record"""
    print("[*] Inserting test data...")
    
    try:
        conn = MySQLdb.connect(**db_config)
        cursor = conn.cursor()
        
        attack_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute("""
            INSERT INTO network_attacks 
            (id, timestamp, alert_type, attacker_bssid, attacker_ssid, 
             destination_bssid, destination_ssid, attack_count)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            attack_id,
            timestamp,
            "Test Deauth",
            "00:11:22:33:44:55",
            "TestAttacker",
            "AA:BB:CC:DD:EE:FF",
            "TestVictim",
            10
        ))
        
        conn.commit()
        conn.close()
        
        print(f"[+] Test data inserted successfully with ID: {attack_id}")
        return True
    except Exception as e:
        print(f"[!] Error inserting test data: {str(e)}")
        return False

def query_recent_data(limit=10):
    """Query recent attack data"""
    print(f"[*] Querying the {limit} most recent attack records...")
    
    try:
        conn = MySQLdb.connect(**db_config)
        cursor = conn.cursor()
        
        cursor.execute(f"""
            SELECT id, timestamp, alert_type, attacker_bssid, destination_bssid, attack_count
            FROM network_attacks
            ORDER BY timestamp DESC
            LIMIT {limit}
        """)
        
        rows = cursor.fetchall()
        
        if not rows:
            print("[!] No attack records found")
        else:
            print(f"[+] Found {len(rows)} records:")
            print("\n{:<10} {:<20} {:<15} {:<18} {:<18} {:<8}".format(
                "ID", "TIMESTAMP", "TYPE", "ATTACKER", "TARGET", "COUNT"
            ))
            print("-" * 90)
            
            for row in rows:
                attack_id = row[0][:8] + "..."  # Truncate ID for display
                print("{:<10} {:<20} {:<15} {:<18} {:<18} {:<8}".format(
                    attack_id, str(row[1]), row[2][:15], row[3] or "Unknown", 
                    row[4] or "Unknown", str(row[5])
                ))
        
        conn.close()
        return True
    except Exception as e:
        print(f"[!] Error querying data: {str(e)}")
        return False

def clear_all_data():
    """Clear all attack data"""
    print("[!] WARNING: This will delete ALL attack records!")
    confirm = input("Are you sure? (yes/no): ")
    
    if confirm.lower() != "yes":
        print("[*] Operation cancelled")
        return False
    
    try:
        conn = MySQLdb.connect(**db_config)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM network_attacks")
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        print(f"[+] Successfully deleted {deleted_count} attack records")
        return True
    except Exception as e:
        print(f"[!] Error clearing data: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Test database connection and operations')
    parser.add_argument('--check', action='store_true', help='Check database connection and tables')
    parser.add_argument('--test-data', action='store_true', help='Insert test data')
    parser.add_argument('--query', action='store_true', help='Query recent attack data')
    parser.add_argument('--limit', type=int, default=10, help='Limit for query results')
    parser.add_argument('--clear', action='store_true', help='Clear all attack data')
    parser.add_argument('--all', action='store_true', help='Run all tests (except clear)')
    
    args = parser.parse_args()
    
    # Default to --check if no arguments provided
    if not any([args.check, args.test_data, args.query, args.clear, args.all]):
        args.check = True
    
    # Run all tests
    if args.all:
        test_connection()
        print()
        check_tables()
        print()
        insert_test_data()
        print()
        query_recent_data(args.limit)
        return
    
    # Run individual tests
    if args.check:
        test_connection()
        print()
        check_tables()
    
    if args.test_data:
        insert_test_data()
    
    if args.query:
        query_recent_data(args.limit)
    
    if args.clear:
        clear_all_data()

if __name__ == "__main__":
    main()
