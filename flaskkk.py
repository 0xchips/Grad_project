from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import MySQLdb
import datetime
import uuid
import threading
import time
import os
import json
import logging
import subprocess
import re
from dotenv import load_dotenv
import secrets

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Correct static folder configuration
app = Flask(__name__, 
            static_folder='templates/static',
            template_folder='templates')

# Security configuration
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))
CORS(app, origins=os.getenv('CORS_ORIGINS', 'localhost:80,localhost:5050').split(','))

# MySQL Database configuration from environment
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'dashboard'),
    'passwd': os.getenv('DB_PASSWORD', 'securepass'),
    'db': os.getenv('DB_NAME', 'security_dashboard'),
}

# Rate limiting storage
request_counts = {}
REQUEST_LIMIT = 100  # requests per minute
BLOCKED_IPS = set()

def rate_limit_check(ip):
    """Check if IP is rate limited"""
    if ip in BLOCKED_IPS:
        return False
    
    current_time = time.time()
    if ip not in request_counts:
        request_counts[ip] = []
    
    # Remove old requests (older than 1 minute)
    request_counts[ip] = [req_time for req_time in request_counts[ip] 
                         if current_time - req_time < 60]
    
    # Check if limit exceeded
    if len(request_counts[ip]) >= REQUEST_LIMIT:
        BLOCKED_IPS.add(ip)
        logger.warning(f"Rate limit exceeded for IP: {ip}")
        return False
    
    request_counts[ip].append(current_time)
    return True

def get_db_connection():
    """Get database connection with error handling"""
    try:
        conn = MySQLdb.connect(**db_config)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

def validate_input(data, required_fields):
    """Validate input data"""
    if not isinstance(data, dict):
        return False, "Invalid JSON data"
    
    for field in required_fields:
        if field not in data or data[field] is None:
            return False, f"Missing required field: {field}"
    
    return True, "Valid"

# Database setup
def init_db():
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to initialize database")
        return
    
    try:
        c = conn.cursor()

        # Alerts table with improved schema
        c.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id VARCHAR(36) PRIMARY KEY,
            tool_name VARCHAR(100) NOT NULL,
            alert_type VARCHAR(100) NOT NULL,
            severity ENUM('low', 'medium', 'high', 'critical') NOT NULL,
            description TEXT,
            raw_data TEXT,
            timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            source_ip VARCHAR(45),
            INDEX idx_timestamp (timestamp),
            INDEX idx_severity (severity),
            INDEX idx_tool_name (tool_name)
        )
        ''')

        # GPS data table with enhanced schema
        c.execute('''
        CREATE TABLE IF NOT EXISTS gps_data (
            id VARCHAR(36) PRIMARY KEY,
            latitude DECIMAL(10,8) NOT NULL,
            longitude DECIMAL(11,8) NOT NULL,
            timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            device_id VARCHAR(100),
            satellites INT DEFAULT 0,
            hdop DECIMAL(4,2) DEFAULT 99.99,
            jamming_detected BOOLEAN DEFAULT FALSE,
            INDEX idx_timestamp (timestamp),
            INDEX idx_device_id (device_id),
            INDEX idx_jamming (jamming_detected)
        )
        ''')

        # Network attacks table with proper indexing
        c.execute('''
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
        ''')

        conn.commit()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    finally:
        conn.close()

# Initialize database on startup
init_db()

# Request middleware for rate limiting and logging
@app.before_request
def before_request():
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    
    # Rate limiting
    if not rate_limit_check(client_ip):
        logger.warning(f"Rate limited request from {client_ip}")
        return jsonify({'error': 'Rate limit exceeded'}), 429
    
    # Log request
    logger.info(f"Request from {client_ip}: {request.method} {request.path}")

# Endpoint to receive alerts from security tools
@app.route('/api/alerts', methods=['POST'])
def receive_alert():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Validate required fields
        is_valid, message = validate_input(data, ['tool_name', 'alert_type', 'severity'])
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Validate severity level
        valid_severities = ['low', 'medium', 'high', 'critical']
        if data['severity'] not in valid_severities:
            return jsonify({'error': 'Invalid severity level'}), 400
        
        # Generate unique ID and get client IP
        alert_id = str(uuid.uuid4())
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        
        # Store in database
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        try:
            c = conn.cursor()
            c.execute(
                """INSERT INTO alerts 
                   (id, tool_name, alert_type, severity, description, raw_data, source_ip)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (
                    alert_id,
                    data['tool_name'][:100],  # Truncate to fit schema
                    data['alert_type'][:100],
                    data['severity'],
                    data.get('description', '')[:1000],  # Limit description length
                    json.dumps(data.get('raw_data', {}))[:5000],  # Limit raw data
                    client_ip
                )
            )
            conn.commit()
            logger.info(f"Alert {alert_id} stored successfully")
            
        except Exception as e:
            logger.error(f"Database error storing alert: {e}")
            return jsonify({'error': 'Database error'}), 500
        finally:
            conn.close()
        
        return jsonify({'id': alert_id, 'status': 'received'}), 201
        
    except Exception as e:
        logger.error(f"Error processing alert: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/logs')
def get_logs():
    conn = MySQLdb.connect(**db_config)
    c = conn.cursor(MySQLdb.cursors.DictCursor)  # Use dictionary cursor
    c.execute("SELECT * FROM network_attacks ORDER BY timestamp DESC")
    logs = c.fetchall()
    conn.close()
    return jsonify(logs)

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
    conn = MySQLdb.connect(**db_config)
    c = conn.cursor()
    c.execute(
        "INSERT INTO gps_data VALUES (%s, %s, %s, %s, %s)",
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
    query = "SELECT * FROM alerts WHERE timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)"
    params = [hours]
    
    if tool_name:
        query += " AND tool_name = %s"
        params.append(tool_name)
    
    if severity:
        query += " AND severity = %s"
        params.append(severity)
    
    query += " ORDER BY timestamp DESC"
    
    # Execute query
    conn = MySQLdb.connect(**db_config)
    c = conn.cursor(MySQLdb.cursors.DictCursor)  # Use dictionary cursor
    c.execute(query, params)
    
    # Convert results to list of dictionaries
    alerts = c.fetchall()
    conn.close()
    
    return jsonify(alerts)

# Endpoint to get GPS data
@app.route('/api/gps', methods=['GET'])
def get_gps():
    # Get query parameters
    device_id = request.args.get('device_id')
    hours = request.args.get('hours', 24, type=int)
    
    # Build query
    query = "SELECT * FROM gps_data WHERE timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)"
    params = [hours]
    
    if device_id:
        query += " AND device_id = %s"
        params.append(device_id)
    
    query += " ORDER BY timestamp DESC"
    
    # Execute query
    conn = MySQLdb.connect(**db_config)
    c = conn.cursor(MySQLdb.cursors.DictCursor)
    c.execute(query, params)
    
    # Convert results to list of dictionaries
    gps_data = c.fetchall()
    conn.close()
    
    return jsonify(gps_data)

# Endpoint to get summary statistics
@app.route('/api/stats', methods=['GET'])
def get_stats():
    hours = request.args.get('hours', 24, type=int)
    
    conn = MySQLdb.connect(**db_config)
    c = conn.cursor()
    
    # Get total alerts per tool
    c.execute("""
    SELECT tool_name, COUNT(*) as count 
    FROM alerts 
    WHERE timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
    GROUP BY tool_name
    """, [hours])
    tools_stats = {row[0]: row[1] for row in c.fetchall()}
    
    # Get alerts by severity
    c.execute("""
    SELECT severity, COUNT(*) as count 
    FROM alerts 
    WHERE timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
    GROUP BY severity
    """, [hours])
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
    conn = MySQLdb.connect(**db_config)
    c = conn.cursor(MySQLdb.cursors.DictCursor)
    c.execute("SELECT * FROM network_attacks ORDER BY timestamp DESC")
    logs = c.fetchall()
    conn.close()
    return jsonify(logs)

@app.route('/api/deauth_logs', methods=['POST'])
def add_deauth_log():
    data = request.json
    
    # Generate unique ID
    attack_id = str(uuid.uuid4())
    
    # Add timestamp if missing
    if 'timestamp' not in data:
        data['timestamp'] = datetime.datetime.now().isoformat()
    
    # Store in database
    conn = MySQLdb.connect(**db_config)
    c = conn.cursor()
    
    try:
        c.execute(
            """
            INSERT INTO network_attacks 
            (id, timestamp, alert_type, attacker_bssid, attacker_ssid, 
            destination_bssid, destination_ssid, attack_count)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                attack_id,
                data.get('timestamp'),
                data.get('alert_type', 'Deauth Attack'),
                data.get('attacker_bssid', 'Unknown'),
                data.get('attacker_ssid', 'Unknown'),
                data.get('destination_bssid', 'Unknown'),
                data.get('destination_ssid', 'Unknown'),
                data.get('attack_count', 0)
            )
        )
        conn.commit()
        conn.close()
        return jsonify({'id': attack_id, 'timestamp': data.get('timestamp')}), 201
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/deauth_logs/clear', methods=['DELETE'])
def clear_deauth_logs():
    try:
        conn = MySQLdb.connect(**db_config)
        c = conn.cursor()
        c.execute("DELETE FROM network_attacks")
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'All deauthentication logs cleared'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/gps/clear', methods=['POST'])
def clear_gps_data():
    """Clear all GPS data from the database"""
    try:
        conn = MySQLdb.connect(**db_config)
        c = conn.cursor()
        
        # Delete all records from the gps_data table
        c.execute("DELETE FROM gps_data")
        
        # Get count of deleted rows
        deleted_count = c.rowcount
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Successfully cleared {deleted_count} GPS records',
            'deleted_count': deleted_count
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/network-discovery', methods=['POST'])
def network_discovery():
    """Execute netdiscover.py script and return results"""
    try:
        import subprocess
        import os
        
        # Path to the netdiscover.py script
        script_path = os.path.join(os.path.dirname(__file__), 'netdiscover.py')
        
        # Check if script exists
        if not os.path.exists(script_path):
            return jsonify({
                'success': False,
                'error': 'netdiscover.py script not found'
            }), 404
        
        # Execute the netdiscover.py script with timeout
        result = subprocess.run(
            ['python3', script_path],
            capture_output=True,
            text=True,
            timeout=60,  # Increased to 60 seconds
            cwd=os.path.dirname(__file__)  # Set working directory
        )
        
        if result.returncode == 0:
            # Script executed successfully
            output = result.stdout.strip()
            error_output = result.stderr.strip()
            
            if not output and not error_output:
                return jsonify({
                    'success': True,
                    'data': [],
                    'message': 'No network devices found',
                    'raw_output': 'No output from network scan'
                })
            
            # Parse the output to extract device information
            devices = []
            lines = output.split('\n')
            
            # Look for JSON output from the script
            json_start = None
            json_end = None
            for i, line in enumerate(lines):
                if '[JSON_START]' in line:
                    json_start = i
                elif '[JSON_END]' in line:
                    json_end = i
                    break
            
            if json_start is not None and json_end is not None:
                # Extract JSON data
                try:
                    json_line = lines[json_start]
                    json_data = json_line.replace('[JSON_START]', '').replace('[JSON_END]', '')
                    devices = json.loads(json_data)
                except json.JSONDecodeError:
                    pass
            
            # If no JSON found, try to parse text output
            if not devices:
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('[') and ('IP:' in line or '|' in line):
                        # Try to parse device info from the formatted output
                        try:
                            # Look for IP and MAC patterns
                            import re
                            ip_pattern = r'(\d+\.\d+\.\d+\.\d+)'
                            mac_pattern = r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})'
                            
                            ip_match = re.search(ip_pattern, line)
                            mac_match = re.search(mac_pattern, line)
                            
                            if ip_match:
                                device_info = {
                                    'ip': ip_match.group(),
                                    'mac': mac_match.group() if mac_match else 'N/A',
                                    'info': line
                                }
                                devices.append(device_info)
                        except:
                            # If parsing fails, just add the line as is
                            if line and not line.startswith('['):
                                devices.append({'info': line})
            
            return jsonify({
                'success': True,
                'data': devices,
                'raw_output': output,
                'device_count': len(devices),
                'message': f'Found {len(devices)} network devices'
            })
        else:
            # Script failed
            error_output = result.stderr.strip() or result.stdout.strip()
            return jsonify({
                'success': False,
                'error': f'Network scan failed: {error_output or "Unknown error"}',
                'raw_output': error_output
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'Network scan timed out (60 seconds). Please try again.',
            'timeout': True
        }), 408
    except FileNotFoundError:
        return jsonify({
            'success': False,
            'error': 'Python3 not found. Please ensure Python is installed.',
        }), 500
    except Exception as e:
        logger.error(f"Network discovery error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Unexpected error during network scan: {str(e)}'
        }), 500

@app.route('/api/test-subprocess', methods=['GET'])
def test_subprocess():
    """Test subprocess execution"""
    try:
        result = subprocess.run(['echo', 'Hello from subprocess'], capture_output=True, text=True, timeout=5)
        return jsonify({
            'success': True,
            'output': result.stdout.strip(),
            'returncode': result.returncode
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

# Main routes for pages
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/<page>.html')
def render_page(page):
    try:
        return render_template(f"{page}.html")
    except:
        return "Page not found", 404

@app.route('/index')
def index_alt():
    return render_template('index.html')

# Create application instance for WSGI
application = app

if __name__ == '__main__':
    # Only for development - use gunicorn for production
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))