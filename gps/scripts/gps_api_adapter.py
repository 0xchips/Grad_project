#!/usr/bin/env python3
"""
GPS API Adapter for WiGuard Security Dashboard

This script provides a bridge between the ESP32 GPS Jamming Detector
and the MySQL database used by the main application.
"""
import os
import MySQLdb
import MySQLdb.cursors
import json
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime, timedelta
import uuid
import logging
import threading
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("GPS_API_Adapter")

# Create a Flask app for the API adapter
app = Flask(__name__)
CORS(app)

# In-memory cache for recent data to improve performance
gps_cache = {
    'last_update': datetime.now(),
    'data': [],
    'stats': {
        'total': 0,
        'anomalies': 0,
        'recent_count': 0
    }
}

# MySQL Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'dashboard',
    'passwd': 'securepass',
    'db': 'security_dashboard',
}

@app.route('/api/gps', methods=['GET'])
def get_gps():
    """Get GPS data from MySQL database"""
    # Get query parameters
    device_id = request.args.get('device_id')
    hours = request.args.get('hours', 24, type=int)
    
    # Build query for MySQL
    query = "SELECT * FROM gps_data WHERE timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)"
    params = [hours]
    
    if device_id:
        query += " AND device_id = %s"
        params.append(device_id)
    
    query += " ORDER BY timestamp DESC"
    
    # Execute query
    try:
        conn = MySQLdb.connect(**DB_CONFIG)
        c = conn.cursor(MySQLdb.cursors.DictCursor)
        c.execute(query, params)
        
        # Convert results to list of dictionaries
        gps_data = c.fetchall()
        conn.close()
        
        logger.info(f"Found {len(gps_data)} GPS records")
        return jsonify(gps_data)
    except Exception as e:
        logger.error(f"Database error: {e}")
        return jsonify([])

@app.route('/api/gps', methods=['POST'])
def receive_gps():
    """Save GPS data to MySQL database"""
    data = request.json
    logger.info(f"Received GPS data: {data}")
    
    # Validate required fields
    if 'latitude' not in data or 'longitude' not in data:
        logger.warning("Missing required GPS coordinates")
        return jsonify({'error': 'Missing required GPS coordinates'}), 400
    
    try:
        conn = MySQLdb.connect(**DB_CONFIG)
        c = conn.cursor()
        
        # Generate unique ID and timestamp
        gps_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Determine if jamming is detected (if not explicitly provided)
        satellites = data.get('satellites', 0)
        hdop = data.get('hdop', 99.9)
        jamming_detected = data.get('jamming_detected', False)
        
        # If jamming_detected wasn't provided explicitly, calculate it
        if 'jamming_detected' not in data:
            jamming_detected = 1 if (satellites < 3 or hdop > 2.0) else 0
        
        # Insert into database - MySQL uses %s for all param types
        c.execute(
            """
            INSERT INTO gps_data (id, latitude, longitude, timestamp, 
                                device_id, satellites, hdop, jamming_detected)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                gps_id,
                data['latitude'],
                data['longitude'],
                timestamp,
                data.get('device_id', 'ESP32-GPS'),
                satellites,
                hdop,
                jamming_detected
            )
        )
        
        conn.commit()
        conn.close()
        
        logger.info(f"GPS data saved with ID: {gps_id}, Jamming: {jamming_detected}")
        
        # Create the response data
        response_data = {
            'success': True,
            'id': gps_id, 
            'timestamp': timestamp,
            'jamming_detected': bool(jamming_detected)
        }
        
        # Add the new entry to the cache immediately
        new_entry = {
            'id': gps_id,
            'latitude': data['latitude'],
            'longitude': data['longitude'],
            'timestamp': timestamp,
            'device_id': data.get('device_id', 'ESP32-GPS'),
            'satellites': satellites,
            'hdop': hdop,
            'jamming_detected': jamming_detected
        }
        
        # Update cache with new entry (at the beginning of the list)
        gps_cache['data'].insert(0, new_entry)
        gps_cache['stats']['total'] += 1
        gps_cache['stats']['recent_count'] += 1
        if jamming_detected:
            gps_cache['stats']['anomalies'] += 1
        
        return jsonify(response_data), 201
    except Exception as e:
        logger.error(f"Error saving GPS data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/esp32/gps', methods=['POST'])
def receive_esp32_gps():
    """Special endpoint for ESP32 devices to send GPS data"""
    # This simply forwards to the standard endpoint
    return receive_gps()

@app.route('/api/gps/test', methods=['GET'])
def test_gps_api():
    """Test endpoint that generates random GPS data"""
    import random
    
    # Generate test data
    test_data = {
        'latitude': 31.9210905 + random.uniform(-0.01, 0.01),
        'longitude': 35.9355047 + random.uniform(-0.01, 0.01),
        'device_id': 'API-TEST-DEVICE',
        'satellites': random.randint(0, 12),
        'hdop': random.uniform(0.8, 5.0),
    }
    
    # Calculate jamming based on satellites and HDOP
    test_data['jamming_detected'] = 1 if (test_data['satellites'] < 3 or test_data['hdop'] > 2.0) else 0
    
    # Save to database using the existing endpoint
    response = app.test_client().post('/api/gps', json=test_data)
    result = json.loads(response.data.decode('utf-8'))
    
    # Return the full test data along with the result
    return jsonify({
        'test_data': test_data,
        'result': result
    })

# Function to update the GPS cache
def update_gps_cache():
    """Update the in-memory cache of GPS data"""
    try:
        conn = MySQLdb.connect(**DB_CONFIG)
        c = conn.cursor(MySQLdb.cursors.DictCursor)
        
        # Get recent data (last hour)
        c.execute("""
            SELECT * FROM gps_data 
            WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
            ORDER BY timestamp DESC
        """)
        
        gps_cache['data'] = c.fetchall()
        gps_cache['last_update'] = datetime.now()
        
        # Update statistics
        c.execute("SELECT COUNT(*) as total FROM gps_data")
        gps_cache['stats']['total'] = c.fetchone()['total']
        
        c.execute("SELECT COUNT(*) as anomalies FROM gps_data WHERE jamming_detected = 1")
        gps_cache['stats']['anomalies'] = c.fetchone()['anomalies']
        
        gps_cache['stats']['recent_count'] = len(gps_cache['data'])
        
        conn.close()
        logger.debug(f"Cache updated with {len(gps_cache['data'])} entries")
    except Exception as e:
        logger.error(f"Error updating cache: {e}")

# Cache update scheduler
def cache_updater():
    """Background thread to update cache periodically"""
    while True:
        update_gps_cache()
        time.sleep(5)  # Update every 5 seconds

# Add new endpoint for optimized data retrieval
@app.route('/api/gps/fast', methods=['GET'])
def get_gps_fast():
    """Get GPS data from cache for faster dashboard updates"""
    # Initialize with data from memory cache
    response_data = gps_cache['data']
    
    # Check if the client sent a last-id parameter
    # This is used for efficient polling (only get updates since last fetch)
    last_id = request.args.get('last_id')
    if last_id:
        # Filter to only return entries after the specified ID
        filtered_data = [item for item in response_data if item['id'] != last_id and 
                         item not in [entry for i, entry in enumerate(response_data) if i > 0 and entry['id'] == last_id]]
        return jsonify(filtered_data)
    
    return jsonify(response_data)

# Add endpoint for quick statistics
@app.route('/api/gps/stats', methods=['GET'])
def get_gps_stats():
    """Get GPS statistics from cache"""
    return jsonify(gps_cache['stats'])

@app.route('/api/gps/clear', methods=['POST'])
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
        
        # Clear the cache
        gps_cache['data'] = []
        gps_cache['stats']['total'] = 0
        gps_cache['stats']['anomalies'] = 0
        gps_cache['stats']['recent_count'] = 0
        gps_cache['last_update'] = datetime.now()
        
        logger.info(f"Cleared {deleted_count} GPS records from database")
        
        return jsonify({
            'success': True,
            'message': f'Successfully cleared {deleted_count} GPS records',
            'deleted_count': deleted_count
        }), 200
    except Exception as e:
        logger.error(f"Error clearing GPS data: {e}")
        return jsonify({'error': str(e)}), 500
    
if __name__ == '__main__':
    # Start the API adapter server on port 5050
    port = int(os.environ.get('PORT', 5050))
    logger.info(f"Starting GPS API adapter on port {port}...")
    try:
        # Quick test connection to database
        conn = MySQLdb.connect(**DB_CONFIG)
        conn.close()
        logger.info("Database connection successful!")
        
        # Initial cache update
        update_gps_cache()
        
        # Start background cache updater
        cache_thread = threading.Thread(target=cache_updater, daemon=True)
        cache_thread.start()
        logger.info("Background cache updater started")
        
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
    
    app.run(host='0.0.0.0', port=port, debug=True, threaded=True)
