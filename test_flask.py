#!/usr/bin/env python3

import MySQLdb
import json
from flask import Flask, jsonify

app = Flask(__name__)

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

@app.route('/test-nids-alerts')
def test_nids_alerts():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
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
        
        return jsonify({
            'alerts': alerts,
            'count': len(alerts),
            'columns': list(alerts[0].keys()) if alerts else []
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5054, debug=False)
