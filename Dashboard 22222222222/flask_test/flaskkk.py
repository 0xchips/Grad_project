from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
import datetime
import uuid
import threading
import time
import os
import json

# Correct static folder configuration
app = Flask(__name__, 
            static_folder='templates/static',  # Point to a 'static' subfolder
            template_folder='templates')
CORS(app)  # Enable cross-origin requests

# Database setup
def init_db():
    conn = sqlite3.connect('security_dashboard.db')
    c = conn.cursor()

    # Alerts table
    c.execute('''
    CREATE TABLE IF NOT EXISTS alerts (
        id TEXT PRIMARY KEY,
        tool_name TEXT NOT NULL,
        alert_type TEXT NOT NULL,
        severity TEXT NOT NULL,
        description TEXT,
        raw_data TEXT,
        timestamp TEXT NOT NULL
    )
    ''')

    # GPS data table
    c.execute('''
    CREATE TABLE IF NOT EXISTS gps_data (
        id TEXT PRIMARY KEY,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        timestamp TEXT NOT NULL,
        device_id TEXT
    )
    ''')

    # Network attacks table
    c.execute('''
    CREATE TABLE IF NOT EXISTS network_attacks (
        id TEXT PRIMARY KEY,
        timestamp TEXT NOT NULL,
        alert_type TEXT NOT NULL,
        attacker_bssid TEXT,
        attacker_ssid TEXT,
        destination_bssid TEXT,
        destination_ssid TEXT,
        attack_count INTEGER
    )
    ''')

    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Log file path
log_file = "../deauth_log.json"  # Correct path to the JSON log file

# Endpoint to receive alerts from security tools
@app.route('/api/alerts', methods=['POST'])
def receive_alert():
    data = request.json
    
    # Validate required fields
    required_fields = ['tool_name', 'alert_type', 'severity']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Generate unique ID and timestamp
    alert_id = str(uuid.uuid4())
    timestamp = datetime.datetime.now().isoformat()
    
    # Store in database
    conn = sqlite3.connect('security_dashboard.db')
    c = conn.cursor()
    c.execute(
        "INSERT INTO alerts VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            alert_id,
            data['tool_name'],
            data['alert_type'],
            data['severity'],
            data.get('description', ''),
            data.get('raw_data', ''),
            timestamp
        )
    )
    conn.commit()
    conn.close()
    
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            logs = json.load(f)
    else:
        logs = []
    logs.append({
        "id": alert_id,
        "tool_name": data["tool_name"],
        "alert_type": data["alert_type"],
        "severity": data["severity"],
        "description": data.get("description", ""),
        "raw_data": data.get("raw_data", ""),
        "timestamp": timestamp
    })
    with open(log_file, "w") as f:
        json.dump(logs, f, indent=2)
    
    return jsonify({'id': alert_id, 'timestamp': timestamp}), 201

@app.route('/logs')
def get_logs():
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            logs = json.load(f)
        return jsonify(logs)  # Return logs as JSON
    else:
        return jsonify([])  # Return an empty list if no logs exist

# Endpoint to receive GPS data
@app.route('/api/gps', methods=['POST'])
def receive_gps():
    data = request.json
    
    # Validate required fields
    if 'latitude' not in data or 'longitude' not in data:
        return jsonify({'error': 'Missing required GPS coordinates'}), 400
    
    # Generate unique ID and timestamp
    gps_id = str(uuid.uuid4())
    timestamp = datetime.datetime.now().isoformat()
    
    # Store in database
    conn = sqlite3.connect('security_dashboard.db')
    c = conn.cursor()
    c.execute(
        "INSERT INTO gps_data VALUES (?, ?, ?, ?, ?)",
        (
            gps_id,
            data['latitude'],
            data['longitude'],
            timestamp,
            data.get('device_id', '')
        )
    )
    conn.commit()
    conn.close()
    
    return jsonify({'id': gps_id, 'timestamp': timestamp}), 201

# Endpoint to get recent alerts
@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    # Get query parameters for filtering
    tool_name = request.args.get('tool_name')
    severity = request.args.get('severity')
    hours = request.args.get('hours', 24, type=int)  # Default to last 24 hours
    
    # Build query with possible filters
    query = "SELECT * FROM alerts WHERE timestamp >= datetime('now', '-{} hours')".format(hours)
    params = []
    
    if tool_name:
        query += " AND tool_name = ?"
        params.append(tool_name)
    
    if severity:
        query += " AND severity = ?"
        params.append(severity)
    
    query += " ORDER BY timestamp DESC"
    
    # Execute query
    conn = sqlite3.connect('security_dashboard.db')
    conn.row_factory = sqlite3.Row  # This enables column access by name
    c = conn.cursor()
    c.execute(query, params)
    
    # Convert results to list of dictionaries
    alerts = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return jsonify(alerts)

# Endpoint to get GPS data
@app.route('/api/gps', methods=['GET'])
def get_gps():
    # Get query parameters
    device_id = request.args.get('device_id')
    hours = request.args.get('hours', 24, type=int)
    
    # Build query
    query = "SELECT * FROM gps_data WHERE timestamp >= datetime('now', '-{} hours')".format(hours)
    params = []
    
    if device_id:
        query += " AND device_id = ?"
        params.append(device_id)
    
    query += " ORDER BY timestamp DESC"
    
    # Execute query
    conn = sqlite3.connect('security_dashboard.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(query, params)
    
    # Convert results to list of dictionaries
    gps_data = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return jsonify(gps_data)

# Endpoint to get summary statistics
@app.route('/api/stats', methods=['GET'])
def get_stats():
    hours = request.args.get('hours', 24, type=int)
    
    conn = sqlite3.connect('security_dashboard.db')
    c = conn.cursor()
    
    # Get total alerts per tool
    c.execute("""
    SELECT tool_name, COUNT(*) as count 
    FROM alerts 
    WHERE timestamp >= datetime('now', '-{} hours')
    GROUP BY tool_name
    """.format(hours))
    tools_stats = {row[0]: row[1] for row in c.fetchall()}
    
    # Get alerts by severity
    c.execute("""
    SELECT severity, COUNT(*) as count 
    FROM alerts 
    WHERE timestamp >= datetime('now', '-{} hours')
    GROUP BY severity
    """.format(hours))
    severity_stats = {row[0]: row[1] for row in c.fetchall()}
    
    conn.close()
    
    return jsonify({
        'by_tool': tools_stats,
        'by_severity': severity_stats,
        'timeframe_hours': hours
    })

# Simple heartbeat endpoint
@app.route('/api/ping', methods=['GET'])
def ping():
    return jsonify({'status': 'online', 'timestamp': datetime.datetime.now().isoformat()})

@app.route('/api/deauth_logs', methods=['GET'])
def get_deauth_logs():
    conn = sqlite3.connect('security_dashboard.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM network_attacks ORDER BY timestamp DESC")
    logs = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(logs)

# Main routes for pages
@app.route('/')
def index():
    return render_template('main.html')

@app.route('/<page>.html')
def render_page(page):
    try:
        return render_template(f"{page}.html")
    except:
        return "Page not found", 404

@app.route('/index')
def index_alt():
    return render_template('main.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)