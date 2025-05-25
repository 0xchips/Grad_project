#!/usr/bin/env python3
"""
GPS Data Simulator with Web Interface

This script provides a web-based interface to simulate GPS readings and send them to the dashboard
via the REST API. It includes features for controlling the simulation, adjusting parameters,
and viewing a live log of the simulated data.
"""
import time
import random
import uuid
import threading
import logging
import json
import queue
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
import os
import sys
import argparse
import MySQLdb

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("GPS_Simulator")

# Database configuration (following deauth system pattern)
MAX_RETRIES = 3
RETRY_DELAY = 2

# Multiple database configurations for fallback
DB_CONFIGS = [
    {
        'host': '127.0.0.1',
        'port': 3306,
        'user': 'dashboard',
        'passwd': 'securepass',
        'db': 'security_dashboard',
    },
    {
        'host': 'localhost',
        'port': 3306,
        'user': 'dashboard',
        'passwd': 'securepass',
        'db': 'security_dashboard',
    },
    {
        'host': 'host.docker.internal',
        'port': 3306,
        'user': 'dashboard',
        'passwd': 'securepass',
        'db': 'security_dashboard',
    }
]

def get_db_connection():
    """Get a database connection using multiple fallback configurations"""
    last_error = None
    
    for attempt in range(MAX_RETRIES):
        for config_index, db_config in enumerate(DB_CONFIGS):
            try:
                conn = MySQLdb.connect(**db_config)
                logger.info(f"Connected to database using config {config_index+1} ({db_config['host']})")
                return conn
            except MySQLdb.Error as e:
                last_error = e
                logger.warning(f"Database connection failed for config {config_index+1} ({db_config['host']}): {e}")
        
        if attempt < MAX_RETRIES - 1:
            logger.info(f"Retrying database connection in {RETRY_DELAY} seconds...")
            time.sleep(RETRY_DELAY)
    
    logger.error(f"Failed to connect to database after {MAX_RETRIES} attempts with all configs")
    return None

DEFAULT_DEVICE_ID = 'GPS-SIM-1'
DEFAULT_LATITUDE = 31.833360
DEFAULT_LONGITUDE = 35.890387
DEFAULT_PORT = 5051

# API endpoints for sending GPS data (fallback order)
API_ENDPOINTS = [
    'http://localhost:5000/api/gps',      # Main Flask app
    'http://localhost:5050/api/gps',      # GPS API adapter
    'http://127.0.0.1:5000/api/gps',      # Alternative localhost
    'http://127.0.0.1:5050/api/gps'       # Alternative adapter
]

# Global variables for simulator state
simulator_running = False
simulator_thread = None
simulation_logs = []
MAX_LOGS = 100  # Maximum number of log entries to keep
simulator_lock = threading.Lock()
current_config = {
    'latitude': DEFAULT_LATITUDE,
    'longitude': DEFAULT_LONGITUDE,
    'device_id': DEFAULT_DEVICE_ID,
    'interval': 2.0,
    'jamming_probability': 0.2,
    'movement_enabled': True,
    'movement_radius': 0.002,
}

# Create a Flask app for the web interface
app = Flask(__name__)

# In-memory HTML template for the web UI
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GPS Simulator</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-radius: 8px;
            padding: 20px;
        }
        h1 {
            color: #2c3e50;
            margin-top: 0;
            padding-bottom: 10px;
            border-bottom: 1px solid #eee;
        }
        .control-panel {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin-bottom: 20px;
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 5px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
        }
        input, select {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        .btn {
            padding: 10px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 600;
            transition: background-color 0.2s;
        }
        .btn-primary {
            background-color: #3498db;
            color: white;
        }
        .btn-primary:hover {
            background-color: #2980b9;
        }
        .btn-danger {
            background-color: #e74c3c;
            color: white;
        }
        .btn-danger:hover {
            background-color: #c0392b;
        }
        .btn-success {
            background-color: #2ecc71;
            color: white;
        }
        .btn-success:hover {
            background-color: #27ae60;
        }
        .status {
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 15px;
            font-weight: 600;
        }
        .status-running {
            background-color: #d5f5e3;
            color: #27ae60;
        }
        .status-stopped {
            background-color: #fadbd8;
            color: #c0392b;
        }
        .log-container {
            height: 400px;
            overflow-y: auto;
            background-color: #2c3e50;
            color: #ecf0f1;
            padding: 10px;
            border-radius: 4px;
            font-family: monospace;
        }
        .log-entry {
            margin-bottom: 5px;
            padding: 5px;
            border-bottom: 1px solid #34495e;
        }
        .log-normal {
            color: #2ecc71;
        }
        .log-jamming {
            color: #e74c3c;
        }
        .log-info {
            color: #3498db;
        }
        .columns {
            display: flex;
            gap: 20px;
        }
        .column {
            flex: 1;
        }
        .stat-card {
            background-color: white;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-bottom: 15px;
        }
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            margin: 10px 0;
        }
        .stat-label {
            color: #7f8c8d;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>GPS Simulator Control Panel</h1>
        
        <div id="status" class="status status-stopped">
            Status: Stopped
        </div>
        
        <div class="control-panel">
            <div class="column">
                <div class="form-group">
                    <label for="latitude">Base Latitude:</label>
                    <input type="number" id="latitude" step="0.000001" value="31.833360">
                </div>
                <div class="form-group">
                    <label for="longitude">Base Longitude:</label>
                    <input type="number" id="longitude" step="0.000001" value="35.890387">
                </div>
                <div class="form-group">
                    <label for="device_id">Device ID:</label>
                    <input type="text" id="device_id" value="GPS-SIM-1">
                </div>
            </div>
            
            <div class="column">
                <div class="form-group">
                    <label for="interval">Update Interval (seconds):</label>
                    <input type="number" id="interval" min="0.5" step="0.5" value="2">
                </div>
                <div class="form-group">
                    <label for="jamming_probability">Jamming Probability (0-1):</label>
                    <input type="number" id="jamming_probability" min="0" max="1" step="0.05" value="0.2">
                </div>
                <div class="form-group">
                    <label for="movement">Enable Movement:</label>
                    <input type="checkbox" id="movement" checked style="width: auto;">
                </div>
                <div class="form-group">
                    <label for="movement_radius">Movement Radius:</label>
                    <input type="number" id="movement_radius" min="0.0001" step="0.0005" value="0.002">
                </div>
            </div>
            
            <div class="column" style="display: flex; flex-direction: column; justify-content: flex-end;">
                <div class="form-group">
                    <button id="start-btn" class="btn btn-success">Start Simulation</button>
                </div>
                <div class="form-group">
                    <button id="stop-btn" class="btn btn-danger" disabled>Stop Simulation</button>
                </div>
                <div class="form-group">
                    <button id="send-jamming-btn" class="btn btn-primary">Send Jamming Event</button>
                </div>
            </div>
        </div>
        
        <div class="columns">
            <div class="column">
                <h2>Statistics</h2>
                <div class="stat-card">
                    <div class="stat-label">Total Readings</div>
                    <div class="stat-value" id="total-readings">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Normal Readings</div>
                    <div class="stat-value" id="normal-readings">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Jamming Events</div>
                    <div class="stat-value" id="jamming-events">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">API Success Rate</div>
                    <div class="stat-value" id="success-rate">0%</div>
                </div>
            </div>
            
            <div class="column">
                <h2>Simulation Log</h2>
                <div class="log-container" id="log-container">
                    <div class="log-entry log-info">GPS Simulator ready. Click "Start Simulation" to begin.</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Global variables
        let stats = {
            totalReadings: 0,
            normalReadings: 0,
            jammingEvents: 0,
            apiSuccesses: 0,
            apiFails: 0
        };
        
        // DOM elements
        const startBtn = document.getElementById('start-btn');
        const stopBtn = document.getElementById('stop-btn');
        const sendJammingBtn = document.getElementById('send-jamming-btn');
        const statusEl = document.getElementById('status');
        const logContainer = document.getElementById('log-container');
        
        // Statistics elements
        const totalReadingsEl = document.getElementById('total-readings');
        const normalReadingsEl = document.getElementById('normal-readings');
        const jammingEventsEl = document.getElementById('jamming-events');
        const successRateEl = document.getElementById('success-rate');
        
        // Update status function
        function updateStatus(running) {
            if (running) {
                statusEl.className = 'status status-running';
                statusEl.textContent = 'Status: Running';
                startBtn.disabled = true;
                stopBtn.disabled = false;
            } else {
                statusEl.className = 'status status-stopped';
                statusEl.textContent = 'Status: Stopped';
                startBtn.disabled = false;
                stopBtn.disabled = true;
            }
        }
        
        // Add log entry function
        function addLogEntry(message, className) {
            const entry = document.createElement('div');
            entry.className = `log-entry ${className || ''}`;
            entry.textContent = message;
            logContainer.appendChild(entry);
            logContainer.scrollTop = logContainer.scrollHeight;
            
            // Limit log entries
            if (logContainer.children.length > 100) {
                logContainer.removeChild(logContainer.children[0]);
            }
        }
        
        // Update statistics function
        function updateStats() {
            totalReadingsEl.textContent = stats.totalReadings;
            normalReadingsEl.textContent = stats.normalReadings;
            jammingEventsEl.textContent = stats.jammingEvents;
            
            const total = stats.apiSuccesses + stats.apiFails;
            const rate = total > 0 ? Math.round((stats.apiSuccesses / total) * 100) : 0;
            successRateEl.textContent = `${rate}%`;
        }
        
        // Set up event source for server-sent events
        const eventSource = new EventSource('/events');
        
        eventSource.onmessage = function(event) {
            const data = JSON.parse(event.data);
            
            if (data.type === 'status') {
                updateStatus(data.running);
            } else if (data.type === 'log') {
                let className = 'log-info';
                if (data.status === 'NORMAL') className = 'log-normal';
                if (data.status === 'JAMMING') className = 'log-jamming';
                
                addLogEntry(data.message, className);
                
                // Update statistics
                stats.totalReadings++;
                if (data.status === 'NORMAL') stats.normalReadings++;
                if (data.status === 'JAMMING') stats.jammingEvents++;
                if (data.api_success) stats.apiSuccesses++;
                else stats.apiFails++;
                
                updateStats();
            }
        };
        
        eventSource.onerror = function() {
            addLogEntry('Connection to server lost. Please refresh the page.', 'log-error');
        };
        
        // Start button event handler
        startBtn.addEventListener('click', function() {
            const config = {
                latitude: parseFloat(document.getElementById('latitude').value),
                longitude: parseFloat(document.getElementById('longitude').value),
                device_id: document.getElementById('device_id').value,
                interval: parseFloat(document.getElementById('interval').value),
                jamming_probability: parseFloat(document.getElementById('jamming_probability').value),
                movement_enabled: document.getElementById('movement').checked,
                movement_radius: parseFloat(document.getElementById('movement_radius').value)
            };
            
            fetch('/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addLogEntry('Simulation started with configuration: ' + JSON.stringify(config), 'log-info');
                } else {
                    addLogEntry('Failed to start simulation: ' + data.error, 'log-error');
                }
            });
        });
        
        // Stop button event handler
        stopBtn.addEventListener('click', function() {
            fetch('/stop', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addLogEntry('Simulation stopped', 'log-info');
                } else {
                    addLogEntry('Failed to stop simulation: ' + data.error, 'log-error');
                }
            });
        });
        
        // Send jamming event button handler
        sendJammingBtn.addEventListener('click', function() {
            fetch('/send_jamming', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addLogEntry('Manual jamming event sent', 'log-jamming');
                } else {
                    addLogEntry('Failed to send jamming event: ' + data.error, 'log-error');
                }
            });
        });
        
        // Initialize UI with server state
        fetch('/status')
            .then(response => response.json())
            .then(data => {
                updateStatus(data.running);
                
                // Set form values based on current configuration
                document.getElementById('latitude').value = data.config.latitude;
                document.getElementById('longitude').value = data.config.longitude;
                document.getElementById('device_id').value = data.config.device_id;
                document.getElementById('interval').value = data.config.interval;
                document.getElementById('jamming_probability').value = data.config.jamming_probability;
                document.getElementById('movement').checked = data.config.movement_enabled;
                document.getElementById('movement_radius').value = data.config.movement_radius;
                
                // Load existing logs
                data.logs.forEach(log => {
                    let className = 'log-info';
                    if (log.status === 'NORMAL') className = 'log-normal';
                    if (log.status === 'JAMMING') className = 'log-jamming';
                    
                    addLogEntry(log.message, className);
                });
                
                // Update statistics
                stats.totalReadings = data.stats.total;
                stats.normalReadings = data.stats.normal;
                stats.jammingEvents = data.stats.jamming;
                stats.apiSuccesses = data.stats.api_success;
                stats.apiFails = data.stats.api_fail;
                updateStats();
            });
    </script>
</body>
</html>
"""

def simulate_gps_reading(base_lat, base_lon, device_id, simulate_jamming=False, movement_enabled=True, movement_radius=0.002):
    """Generate a simulated GPS reading"""
    
    # Create some variation in the position
    if simulate_jamming:
        # Larger variations and poor accuracy during jamming
        lat_variation = random.uniform(-0.05, 0.05)
        lon_variation = random.uniform(-0.05, 0.05)
        satellites = random.randint(0, 3)  # Few or no satellites during jamming
        hdop = random.uniform(2.0, 10.0)   # Poor accuracy (high HDOP)
        jamming = True
    else:
        # Normal variations - smaller if movement not enabled
        if movement_enabled:
            lat_variation = random.uniform(-movement_radius, movement_radius)
            lon_variation = random.uniform(-movement_radius, movement_radius)
        else:
            lat_variation = random.uniform(-0.000001, 0.000001)  # Tiny variation for sensor noise
            lon_variation = random.uniform(-0.000001, 0.000001)  # Tiny variation for sensor noise
        
        satellites = random.randint(6, 12)  # Normal number of satellites
        hdop = random.uniform(0.8, 1.5)    # Good accuracy (low HDOP)
        jamming = False
    
    # Generate the reading
    reading = {
        'id': str(uuid.uuid4()),
        'latitude': base_lat + lat_variation,
        'longitude': base_lon + lon_variation,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'device_id': device_id,
        'satellites': satellites,
        'hdop': hdop,
        'jamming_detected': 1 if jamming else 0
    }
    
    return reading

def save_to_database(reading):
    """Save GPS data directly to MySQL database (following deauth system pattern)"""
    try:
        # Get database connection
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to get database connection")
            return False, None
            
        cursor = conn.cursor()
        
        # Generate unique ID if not provided
        if 'id' not in reading:
            reading['id'] = str(uuid.uuid4())
        
        # Use current timestamp if not provided
        if 'timestamp' not in reading:
            reading['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Set default values for optional fields
        satellites = reading.get('satellites', 0)
        hdop = reading.get('hdop', 99.9)
        device_id = reading.get('device_id', DEFAULT_DEVICE_ID)
        
        # Determine if jamming is detected (if not explicitly provided)
        if 'jamming_detected' not in reading:
            jamming_detected = 1 if (satellites < 3 or hdop > 2.0) else 0
        else:
            jamming_detected = reading['jamming_detected']
        
        # Insert GPS data into database
        cursor.execute(
            """
            INSERT INTO gps_data (id, latitude, longitude, timestamp, 
                                device_id, satellites, hdop, jamming_detected)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                reading['id'],
                reading['latitude'],
                reading['longitude'],
                reading['timestamp'],
                device_id,
                satellites,
                hdop,
                jamming_detected
            )
        )
        
        conn.commit()
        conn.close()
        
        logger.info(f"GPS data saved to database with ID: {reading['id']}, Jamming: {bool(jamming_detected)}")
        return True, {"id": reading['id'], "jamming_detected": bool(jamming_detected)}
        
    except MySQLdb.Error as e:
        logger.error(f"Database error: {e}")
        return False, None
    except Exception as e:
        logger.error(f"Error saving GPS data: {e}")
        return False, None

def simulator_worker(config):
    """Background worker that continuously generates GPS readings"""
    global simulator_running, simulation_logs
    
    # Statistics for this simulation run
    stats = {
        'total': 0,
        'normal': 0,
        'jamming': 0,
        'api_success': 0,
        'api_fail': 0
    }
    
    logger.info(f"Starting GPS simulator with config: {config}")
    
    base_lat = config['latitude']
    base_lon = config['longitude']
    device_id = config['device_id']
    interval = config['interval']
    jamming_probability = config['jamming_probability']
    movement_enabled = config['movement_enabled']
    movement_radius = config['movement_radius']
    
    # Main simulation loop
    while simulator_running:
        # Decide if this reading will simulate jamming
        simulate_jamming = random.random() < jamming_probability
        
        # Generate the reading
        reading = simulate_gps_reading(
            base_lat, 
            base_lon, 
            device_id, 
            simulate_jamming,
            movement_enabled,
            movement_radius
        )
        
        # Save directly to database (like deauth system)
        success, response = save_to_database(reading)
        
        # Create log message
        status = "JAMMING" if simulate_jamming else "NORMAL"
        log_message = f"[{status}] Lat: {reading['latitude']:.6f}, Lon: {reading['longitude']:.6f}, " \
                      f"Sats: {reading['satellites']}, HDOP: {reading['hdop']:.2f}, " \
                      f"DB: {'Success' if success else 'Failed'}"
        
        # Update statistics
        stats['total'] += 1
        if simulate_jamming:
            stats['jamming'] += 1
        else:
            stats['normal'] += 1
        
        if success:
            stats['api_success'] += 1
        else:
            stats['api_fail'] += 1
        
        # Add to log
        with simulator_lock:
            simulation_logs.append({
                'timestamp': datetime.now().isoformat(),
                'message': log_message,
                'status': status,
                'api_success': success,
                'stats': stats.copy()
            })
            
            # Keep logs under the limit
            if len(simulation_logs) > MAX_LOGS:
                simulation_logs.pop(0)
        
        # Log to console
        logger.info(log_message)
        
        # Send SSE event to clients
        send_sse_message('log', {
            'message': log_message,
            'status': status,
            'api_success': success
        })
        
        # Wait for the next interval
        time.sleep(interval)
    
    logger.info("GPS simulator stopped")

def send_sse_message(type, data):
    """Send a Server-Sent Event to all clients"""
    data['type'] = type
    # This will be used by the main thread to send messages
    sse_message = f"data: {json.dumps(data)}\n\n"
    for client in sse_clients:
        client.put(sse_message)

# SSE setup for real-time updates
sse_clients = set()

@app.route('/events')
def events():
    """Server-Sent Events endpoint for real-time updates"""
    def event_stream():
        client_queue = queue.Queue()
        sse_clients.add(client_queue)
        
        # Send initial status
        client_queue.put(f"data: {json.dumps({'type': 'status', 'running': simulator_running})}\n\n")
        
        try:
            while True:
                message = client_queue.get();
                yield message
        finally:
            sse_clients.remove(client_queue)
    
    return Response(stream_with_context(event_stream()), 
                   content_type='text/event-stream')

@app.route('/')
def index():
    """Main page with simulator controls"""
    return HTML_TEMPLATE

@app.route('/start', methods=['POST'])
def start_simulator():
    """Start the GPS simulator with the provided configuration"""
    global simulator_running, simulator_thread, current_config
    
    if simulator_running:
        return jsonify({'success': False, 'error': 'Simulator is already running'})
    
    # Get configuration from request
    try:
        config = request.json
        
        # Validate configuration
        if not all(k in config for k in ['latitude', 'longitude', 'device_id', 'interval', 'jamming_probability']):
            return jsonify({'success': False, 'error': 'Missing required configuration parameters'})
        
        # Update current configuration
        current_config = config
        
        # Start simulator thread
        simulator_running = True
        simulator_thread = threading.Thread(target=simulator_worker, args=(config,))
        simulator_thread.daemon = True
        simulator_thread.start()
        
        # Send status update to all clients
        send_sse_message('status', {'running': True})
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error starting simulator: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/stop', methods=['POST'])
def stop_simulator():
    """Stop the GPS simulator"""
    global simulator_running, simulator_thread
    
    if not simulator_running:
        return jsonify({'success': False, 'error': 'Simulator is not running'})
    
    # Stop simulator thread
    simulator_running = False
    if simulator_thread:
        simulator_thread.join(timeout=2.0)
    
    # Send status update to all clients
    send_sse_message('status', {'running': False})
    
    return jsonify({'success': True})

@app.route('/send_jamming', methods=['POST'])
def send_jamming_event():
    """Manually send a jamming event"""
    global current_config
    
    # Generate a jamming reading
    reading = simulate_gps_reading(
        current_config['latitude'],
        current_config['longitude'],
        current_config['device_id'],
        True,  # Force jamming
        current_config['movement_enabled'],
        current_config['movement_radius']
    )
    
    # Send to database
    success, response = save_to_database(reading)
    
    # Create log message
    log_message = f"[MANUAL JAMMING] Lat: {reading['latitude']:.6f}, Lon: {reading['longitude']:.6f}, " \
                  f"Sats: {reading['satellites']}, HDOP: {reading['hdop']:.2f}, " \
                  f"DB: {'Success' if success else 'Failed'}"
    
    # Add to log
    with simulator_lock:
        simulation_logs.append({
            'timestamp': datetime.now().isoformat(),
            'message': log_message,
            'status': 'JAMMING',
            'api_success': success
        })
        
        # Keep logs under the limit
        if len(simulation_logs) > MAX_LOGS:
            simulation_logs.pop(0)
    
    # Log to console
    logger.info(log_message)
    
    # Send SSE event to clients
    send_sse_message('log', {
        'message': log_message,
        'status': 'JAMMING',
        'api_success': success
    })
    
    return jsonify({'success': True})

@app.route('/status', methods=['GET'])
def get_status():
    """Get the current simulator status and configuration"""
    global simulator_running, current_config, simulation_logs
    
    # Calculate statistics from logs
    stats = {
        'total': 0,
        'normal': 0,
        'jamming': 0,
        'api_success': 0,
        'api_fail': 0
    }
    
    if simulation_logs:
        # Get the most recent statistics
        latest_log = simulation_logs[-1]
        if 'stats' in latest_log:
            stats = latest_log['stats']
    
    return jsonify({
        'running': simulator_running,
        'config': current_config,
        'logs': simulation_logs,
        'stats': stats
    })

def main():
    """Main entry point for the application"""
    global API_ENDPOINTS
    
    parser = argparse.ArgumentParser(description='GPS Simulator with Web Interface')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help='Web server port')
    parser.add_argument('--api', type=str, help='Primary API endpoint URL')
    parser.add_argument('--alt-api', type=str, help='Alternative API endpoint URL')
    parser.add_argument('--db-host', type=str, help='Database hostname (for direct DB writer)')
    parser.add_argument('--db-port', type=int, default=3306, help='Database port (for direct DB writer)')
    parser.add_argument('--auto-retry', action='store_true', help='Enable automatic retry on all endpoints')
    
    args = parser.parse_args()
    
    # Update API endpoints if provided
    if args.api:
        # Replace first endpoint with provided one
        API_ENDPOINTS[0] = args.api
    
    if args.alt_api:
        # Insert alternative API at position 1
        if args.alt_api in API_ENDPOINTS:
            API_ENDPOINTS.remove(args.alt_api)  # Avoid duplicates
        API_ENDPOINTS.insert(1, args.alt_api)
    
    # If database host is provided, update the DB_CONFIG in the database writer
    if args.db_host:
        db_writer_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gps_db_writer.py')
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("gps_db_writer", db_writer_path)
            db_writer = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(db_writer)
            
            # Update the first DB config
            if hasattr(db_writer, 'DB_CONFIGS') and len(db_writer.DB_CONFIGS) > 0:
                db_writer.DB_CONFIGS[0]['host'] = args.db_host
                db_writer.DB_CONFIGS[0]['port'] = args.db_port
                logger.info(f"Updated database writer to use {args.db_host}:{args.db_port}")
        except Exception as e:
            logger.warning(f"Failed to update database configuration: {e}")
    
    logger.info(f"Starting GPS Simulator on port {args.port}")
    logger.info(f"API endpoints: {API_ENDPOINTS}")
    
    # Start the web server
    app.run(host='0.0.0.0', port=args.port, debug=True, threaded=True)

if __name__ == "__main__":
    main()
