#!/usr/bin/env python3
"""
GPS API Adapter for CyberShield Security Dashboard

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
        
        # Return the result with jamming detection information
        return jsonify({
            'success': True,
            'id': gps_id, 
            'timestamp': timestamp,
            'jamming_detected': bool(jamming_detected)
        }), 201
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

if __name__ == '__main__':
    # Start the API adapter server on port 5050
    port = int(os.environ.get('PORT', 5050))
    logger.info(f"Starting GPS API adapter on port {port}...")
    try:
        # Quick test connection to database
        conn = MySQLdb.connect(**DB_CONFIG)
        conn.close()
        logger.info("Database connection successful!")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
    
    app.run(host='0.0.0.0', port=port, debug=True)
