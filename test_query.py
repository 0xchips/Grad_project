#!/usr/bin/env python3

import MySQLdb
import json

def get_db_connection():
    try:
        conn = MySQLdb.connect(
            host='localhost',
            user='dashboard', 
            passwd='securepass',
            db='security_dashboard',
            charset='utf8'
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def test_query():
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database")
        return
    
    try:
        c = conn.cursor(MySQLdb.cursors.DictCursor)
        
        query = """
            SELECT id, timestamp, alert_signature, alert_severity, category, protocol, 
                   source_ip, destination_ip, source_port, destination_port, action, 
                   classification, signature_id, flow_id FROM nids_alerts 
            WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            ORDER BY timestamp DESC LIMIT 1
        """
        
        c.execute(query)
        alerts = c.fetchall()
        
        print("Query Results:")
        print(json.dumps(alerts, indent=2, default=str))
        print(f"\nNumber of alerts: {len(alerts)}")
        
        if alerts:
            print(f"\nColumns in result: {list(alerts[0].keys())}")
            
    except Exception as e:
        print(f"Query error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    test_query()
