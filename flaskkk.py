from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import MySQLdb
import MySQLdb.cursors
import datetime
import uuid
import threading
import time
import os
import json
import logging
import subprocess
import re
import signal
import ipaddress
import functools
from contextlib import contextmanager
from typing import Optional, Dict, Any, List, Tuple
from dotenv import load_dotenv
import secrets
import psutil

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
    'charset': 'utf8mb4',
    'autocommit': True
}

# Database connection pool configuration
class DatabasePool:
    """Simple database connection pool"""
    def __init__(self, max_connections=10):
        self.max_connections = max_connections
        self.pool = []
        self.lock = threading.Lock()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            with self.lock:
                if self.pool:
                    conn = self.pool.pop()
                else:
                    conn = MySQLdb.connect(**db_config)
            yield conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            if conn:
                try:
                    conn.close()
                except:
                    pass
            conn = None
            raise
        finally:
            if conn:
                try:
                    with self.lock:
                        if len(self.pool) < self.max_connections:
                            self.pool.append(conn)
                        else:
                            conn.close()
                except:
                    try:
                        conn.close()
                    except:
                        pass

# Global database pool
db_pool = DatabasePool()

def get_db_connection():
    """Get database connection with error handling - DEPRECATED: Use db_pool.get_connection() instead"""
    try:
        conn = MySQLdb.connect(**db_config)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

def validate_input(data: Dict[str, Any], required_fields: List[str]) -> Tuple[bool, str]:
    """Enhanced input validation with type checking and sanitization"""
    if not isinstance(data, dict):
        return False, "Invalid JSON data"
    
    for field in required_fields:
        if field not in data or data[field] is None:
            return False, f"Missing required field: {field}"
        
        # Additional validation based on field type
        if field.endswith('_id') and not isinstance(data[field], str):
            return False, f"Field {field} must be a string"
        
        if field in ['latitude', 'longitude'] and not isinstance(data[field], (int, float)):
            return False, f"Field {field} must be a number"
            
        if field.endswith('_ip'):
            try:
                ipaddress.ip_address(data[field])
            except ValueError:
                return False, f"Field {field} must be a valid IP address"
    
    return True, "Valid"

def sanitize_string(value: str, max_length: int = 255) -> str:
    """Sanitize string input to prevent XSS and limit length"""
    if not isinstance(value, str):
        return str(value)[:max_length]
    
    # Remove potential script tags and limit length
    sanitized = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.IGNORECASE | re.DOTALL)
    sanitized = re.sub(r'[<>"\']', '', sanitized)
    return sanitized[:max_length]

def validate_ip_address(ip: str) -> bool:
    """Validate IP address format"""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

# Database setup
def init_db():
    """Initialize database with improved error handling and connection pooling"""
    try:
        with db_pool.get_connection() as conn:
            c = conn.cursor()
            
            # Create tables with proper schema
            tables = [
                # Alerts table with improved schema
                '''
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
                    INDEX idx_tool_name (tool_name),
                    INDEX idx_source_ip (source_ip)
                )
                ''',
                
                # GPS data table with enhanced schema
                '''
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
                ''',
                
                # Network attacks table with proper indexing
                '''
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
                    INDEX idx_attacker_bssid (attacker_bssid),
                    INDEX idx_source_ip (source_ip)
                )
                ''',
                
                # NIDS alerts table
                '''
                CREATE TABLE IF NOT EXISTS nids_alerts (
                    id VARCHAR(36) PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    source_ip VARCHAR(45) NOT NULL,
                    dest_ip VARCHAR(45) NOT NULL,
                    source_port INT,
                    dest_port INT,
                    protocol VARCHAR(10),
                    alert_type VARCHAR(100) NOT NULL,
                    severity ENUM('low', 'medium', 'high', 'critical') NOT NULL DEFAULT 'medium',
                    description TEXT,
                    raw_data TEXT,
                    threat_type VARCHAR(50),
                    INDEX idx_timestamp (timestamp),
                    INDEX idx_source_ip (source_ip),
                    INDEX idx_dest_ip (dest_ip),
                    INDEX idx_alert_type (alert_type),
                    INDEX idx_severity (severity),
                    INDEX idx_threat_type (threat_type)
                )
                ''',
                
                # GeoIP information table
                '''
                CREATE TABLE IF NOT EXISTS geoip_info (
                    id VARCHAR(36) PRIMARY KEY,
                    ip_address VARCHAR(45) NOT NULL UNIQUE,
                    country VARCHAR(100),
                    region VARCHAR(100),
                    city VARCHAR(100),
                    zip_code VARCHAR(20),
                    latitude DECIMAL(10,8),
                    longitude DECIMAL(11,8),
                    timezone VARCHAR(50),
                    isp VARCHAR(100),
                    organization VARCHAR(100),
                    asn VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_ip_address (ip_address),
                    INDEX idx_country (country)
                )
                '''
            ]
            
            # Execute table creation
            for table_sql in tables:
                try:
                    c.execute(table_sql)
                    logger.debug(f"Table created/verified successfully")
                except Exception as table_error:
                    logger.error(f"Failed to create table: {table_error}")
                    # Continue with other tables
                    continue
            
            conn.commit()
            logger.info("Database initialized successfully")
            
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

# Initialize database on startup
init_db()

@app.route('/api/health', methods=['GET'])
def health_check():
    return "OK"

# Request middleware for logging
@app.before_request
def before_request():
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    
    # Log request
    logger.info(f"Request from {client_ip}: {request.method} {request.path}")

@app.route('/api/alerts', methods=['POST'])
def receive_alert():
    """Enhanced alert endpoint with improved validation and error handling"""
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
        
        # Sanitize inputs
        tool_name = sanitize_string(data['tool_name'], 100)
        alert_type = sanitize_string(data['alert_type'], 100)
        description = sanitize_string(data.get('description', ''), 1000)
        
        # Store in database using connection pool
        try:
            with db_pool.get_connection() as conn:
                c = conn.cursor()
                c.execute(
                    """INSERT INTO alerts 
                       (id, tool_name, alert_type, severity, description, raw_data, source_ip)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (
                        alert_id,
                        tool_name,
                        alert_type,
                        data['severity'],
                        description,
                        json.dumps(data.get('raw_data', {}))[:5000],  # Limit raw data
                        client_ip
                    )
                )
                conn.commit()
                logger.info(f"Alert {alert_id} stored successfully")
                
        except Exception as e:
            logger.error(f"Database error storing alert: {e}")
            return jsonify({'error': 'Database error'}), 500
        
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
    """Enhanced deauth log endpoint with validation and sanitization"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Generate unique ID
        attack_id = str(uuid.uuid4())
        
        # Always use current server time for timestamp
        current_timestamp = datetime.datetime.now().isoformat()
        
        # Sanitize and validate inputs
        alert_type = sanitize_string(data.get('alert_type', 'Deauth Attack'), 100)
        attacker_bssid = sanitize_string(data.get('attacker_bssid', data.get('attacker_mac', 'Unknown')), 17)
        attacker_ssid = sanitize_string(data.get('attacker_ssid', 'Unknown'), 255)
        destination_bssid = sanitize_string(data.get('destination_bssid', data.get('target_bssid', 'Unknown')), 17)
        destination_ssid = sanitize_string(data.get('destination_ssid', data.get('target_ssid', 'Unknown')), 255)
        
        # Validate attack count
        try:
            attack_count = int(data.get('attack_count', 1))
            if attack_count < 0:
                attack_count = 1
        except (ValueError, TypeError):
            attack_count = 1
        
        # Store in database using connection pool
        try:
            with db_pool.get_connection() as conn:
                c = conn.cursor()
                c.execute(
                    """
                    INSERT INTO network_attacks 
                    (id, timestamp, alert_type, attacker_bssid, attacker_ssid, 
                    destination_bssid, destination_ssid, attack_count)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        attack_id,
                        current_timestamp,
                        alert_type,
                        attacker_bssid,
                        attacker_ssid,
                        destination_bssid,
                        destination_ssid,
                        attack_count
                    )
                )
                conn.commit()
                logger.info(f"Deauth attack {attack_id} logged successfully")
                
        except Exception as e:
            logger.error(f"Database error storing deauth log: {e}")
            return jsonify({'error': 'Database error'}), 500
        
        return jsonify({
            'status': 'success',
            'id': attack_id, 
            'timestamp': current_timestamp,
            'event': data.get('event', 'unknown')
        }), 201
        
    except Exception as e:
        logger.error(f"Error processing deauth log: {e}")
        return jsonify({'error': 'Internal server error'}), 500
    
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

@app.route('/api/system-resources', methods=['GET'])
def get_system_resources():
    """Get real-time system resource usage"""
    try:
        # Get CPU usage (percentage)
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Get memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used = round(memory.used / (1024**3), 2)  # GB
        memory_total = round(memory.total / (1024**3), 2)  # GB
        
        # Get network I/O statistics
        network_io = psutil.net_io_counters()
        
        # Calculate network usage (bytes per second)
        network_sent = network_io.bytes_sent
        network_recv = network_io.bytes_recv
        
        # Get disk I/O for context
        disk_io = psutil.disk_io_counters()
        disk_usage = psutil.disk_usage('/')
        
        return jsonify({
            'cpu': {
                'percent': round(cpu_percent, 1),
                'cores': psutil.cpu_count()
            },
            'memory': {
                'percent': round(memory_percent, 1),
                'used_gb': memory_used,
                'total_gb': memory_total,
                'available_gb': round(memory.available / (1024**3), 2)
            },
            'network': {
                'bytes_sent': network_sent,
                'bytes_recv': network_recv,
                'packets_sent': network_io.packets_sent,
                'packets_recv': network_io.packets_recv
            },
            'disk': {
                'total_gb': round(disk_usage.total / (1024**3), 2),
                'used_gb': round(disk_usage.used / (1024**3), 2),
                'free_gb': round(disk_usage.free / (1024**3), 2),
                'percent': round((disk_usage.used / disk_usage.total) * 100, 1)
            },
            'timestamp': time.time()
        })
        
    except Exception as e:
        logger.error(f"Error getting system resources: {str(e)}")
        return jsonify({'error': f'Failed to get system resources: {str(e)}'}), 500

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
            'error': result.stderr.strip(),
            'returncode': result.returncode
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Main dashboard routes
@app.route('/')
def index():
    """Render the main dashboard page"""
    return render_template('index.html')

@app.route('/index.html')
def index_html():
    """Render the main dashboard page"""
    return render_template('index.html')

@app.route('/network.html')
def network_dashboard():
    """Render the network dashboard page"""
    return render_template('network.html')

@app.route('/deauth.html')
def deauth_dashboard():
    """Render the deauth dashboard page"""
    return render_template('deauth.html')

@app.route('/gps.html')
def gps_dashboard():
    """Render the GPS dashboard page"""
    return render_template('gps.html')

@app.route('/bluetooth.html')
def bluetooth_dashboard():
    """Render the Bluetooth dashboard page"""
    return render_template('bluetooth.html')

# NIDS Dashboard Route Handler
@app.route('/nids.html')
def nids_dashboard():
    """Render the NIDS dashboard page"""
    return render_template('nids.html')

# ============== NIDS API ENDPOINTS ==============

@app.route('/api/nids-stats', methods=['GET'])
def get_nids_stats():
    """Get NIDS dashboard statistics"""
    try:
        hours = request.args.get('hours', 24, type=int)
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        try:
            c = conn.cursor(MySQLdb.cursors.DictCursor)
            
            # Get total alerts in timeframe
            c.execute("""
                SELECT COUNT(*) as total_alerts
                FROM nids_alerts 
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
            """, [hours])
            result = c.fetchone()
            total_alerts = result['total_alerts'] if result else 0
            
            # Get alerts by severity
            c.execute("""
                SELECT alert_severity, COUNT(*) as count 
                FROM nids_alerts 
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
                GROUP BY alert_severity
            """, [hours])
            by_severity = {row['alert_severity']: row['count'] for row in c.fetchall()}
            
            # Get alerts by category
            c.execute("""
                SELECT category, COUNT(*) as count 
                FROM nids_alerts 
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
                GROUP BY category
            """, [hours])
            by_category = {row['category']: row['count'] for row in c.fetchall()}
            
            # Get alerts by protocol
            c.execute("""
                SELECT protocol, COUNT(*) as count 
                FROM nids_alerts 
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
                GROUP BY protocol
            """, [hours])
            by_protocol = {row['protocol']: row['count'] for row in c.fetchall()}
            
            # Get top source IPs
            c.execute("""
                SELECT source_ip, COUNT(*) as count 
                FROM nids_alerts 
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR) 
                AND source_ip IS NOT NULL
                GROUP BY source_ip 
                ORDER BY count DESC 
                LIMIT 10
            """, [hours])
            top_source_ips = [{'ip': row['source_ip'], 'count': row['count']} for row in c.fetchall()]
            
            # Get top destination IPs
            c.execute("""
                SELECT destination_ip, COUNT(*) as count 
                FROM nids_alerts 
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR) 
                AND destination_ip IS NOT NULL
                GROUP BY destination_ip 
                ORDER BY count DESC 
                LIMIT 10
            """, [hours])
            top_destination_ips = [{'ip': row['destination_ip'], 'count': row['count']} for row in c.fetchall()]
            
            # Get hourly trend
            c.execute("""
                SELECT DATE_FORMAT(timestamp, '%%Y-%%m-%%d %%H:00:00') as hour, COUNT(*) as count
                FROM nids_alerts 
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
                GROUP BY hour 
                ORDER BY hour
            """, [hours])
            hourly_trend = [{'hour': row['hour'], 'count': row['count']} for row in c.fetchall()]
            
            return jsonify({
                'total_alerts': total_alerts,
                'by_severity': by_severity,
                'by_category': by_category,
                'by_protocol': by_protocol,
                'top_source_ips': top_source_ips,
                'top_destination_ips': top_destination_ips,
                'hourly_trend': hourly_trend,
                'timeframe_hours': hours
            })
            
        except Exception as e:
            logger.error(f"Database error in NIDS stats: {str(e)}")
            return jsonify({'error': 'Database query failed'}), 500
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Error getting NIDS stats: {str(e)}")
        return jsonify({'error': 'Failed to get NIDS statistics'}), 500

@app.route('/api/nids-alerts', methods=['GET'])
def get_nids_alerts():
    """Get NIDS alerts with filtering options"""
    try:
        # Get query parameters
        hours = request.args.get('hours', 24, type=int)
        limit = request.args.get('limit', 100, type=int)
        severity = request.args.get('severity')
        category = request.args.get('category')
        protocol = request.args.get('protocol')
        source_ip = request.args.get('source_ip')
        destination_ip = request.args.get('destination_ip')
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        try:
            c = conn.cursor(MySQLdb.cursors.DictCursor)
            
            # Build query with filters
            query = """
                SELECT id, timestamp, alert_severity, category, protocol, 
                       source_ip, destination_ip
                FROM nids_alerts 
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
            """
            params = [hours]
            
            if severity:
                query += " AND alert_severity = %s"
                params.append(severity)
            
            if category:
                query += " AND category = %s"
                params.append(category)
            
            if protocol:
                query += " AND protocol = %s"
                params.append(protocol)
            
            if source_ip:
                query += " AND source_ip = %s"
                params.append(source_ip)
            
            if destination_ip:
                query += " AND destination_ip = %s"
                params.append(destination_ip)
            
            query += " ORDER BY timestamp DESC LIMIT %s"
            params.append(limit)
            
            c.execute(query, params)
            alerts = c.fetchall()
            
            return jsonify({
                'alerts': alerts,
                'count': len(alerts),
                'filters': {
                    'hours': hours,
                    'severity': severity,
                    'category': category,
                    'protocol': protocol,
                    'source_ip': source_ip,
                    'destination_ip': destination_ip
                }
            })
            
        except Exception as e:
            logger.error(f"Database error in NIDS alerts: {str(e)}")
            return jsonify({'error': 'Database query failed'}), 500
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Error getting NIDS alerts: {str(e)}")
        return jsonify({'error': 'Failed to get NIDS alerts'}), 500

@app.route('/api/nids-dns', methods=['GET'])
def get_nids_dns():
    """Get DNS logs with filtering options"""
    try:
        # Get query parameters
        hours = request.args.get('hours', 24, type=int)
        limit = request.args.get('limit', 50, type=int)
        suspicious_only = request.args.get('suspicious_only', 'true').lower() == 'true'
        threat_type = request.args.get('threat_type')
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        try:
            c = conn.cursor(MySQLdb.cursors.DictCursor)
            
            # Build query
            query = """
                SELECT id, timestamp, query_name, query_type, response_code,
                       is_suspicious, threat_type, source_ip, destination_ip,
                       confidence_score, raw_log
                FROM dns_logs 
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
            """
            params = [hours]
            
            if suspicious_only:
                query += " AND is_suspicious = 1"
            
            if threat_type:
                query += " AND threat_type = %s"
                params.append(threat_type)
            
            query += " ORDER BY timestamp DESC LIMIT %s"
            params.append(limit)
            
            c.execute(query, params)
            dns_logs = c.fetchall()
            
            return jsonify({
                'dns_logs': dns_logs,
                'count': len(dns_logs),
                'filters': {
                    'hours': hours,
                    'suspicious_only': suspicious_only,
                    'threat_type': threat_type
                }
            })
            
        except Exception as e:
            logger.error(f"Database error in NIDS DNS: {str(e)}")
            return jsonify({'error': 'Database query failed'}), 500
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Error getting NIDS DNS logs: {str(e)}")
        return jsonify({'error': 'Failed to get DNS logs'}), 500

@app.route('/api/nids-geoip/<ip>', methods=['GET'])
def get_nids_geoip(ip):
    """Get geographic IP information"""
    try:
        # Validate IP format
        if not validate_ip_address(ip):
            return jsonify({'error': 'Invalid IP address format'}), 400
        
        try:
            with db_pool.get_connection() as conn:
                c = conn.cursor(MySQLdb.cursors.DictCursor)
                
                c.execute("""
                    SELECT ip_address, country, region, city, country_code,
                           latitude, longitude, timezone, isp, organization, asn
                    FROM geoip_info 
                    WHERE ip_address = %s
                """, [ip])
                
                result = c.fetchone()
                
                if result:
                    return jsonify({
                        'found': True,
                        'geoip': result
                    })
                else:
                    return jsonify({
                        'found': False,
                        'message': f'No geographic information found for IP {ip}'
                    })
                    
        except Exception as e:
            logger.error(f"Database error in NIDS GeoIP: {str(e)}")
            return jsonify({'error': 'Database query failed'}), 500
            
    except Exception as e:
        logger.error(f"Error getting NIDS GeoIP: {str(e)}")
        return jsonify({'error': 'Failed to get GeoIP information'}), 500

@app.route('/api/nids-status', methods=['GET'])
def get_nids_status():
    """Get NIDS system status"""
    try:
        # Check if Suricata is running
        suricata_running = False
        try:
            result = subprocess.run(['pgrep', 'suricata'], capture_output=True, text=True)
            suricata_running = result.returncode == 0
        except:
            pass
        
        # Check database connectivity
        db_connected = False
        total_alerts = 0
        total_dns_logs = 0
        
        conn = get_db_connection()
        if conn:
            try:
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM nids_alerts")
                total_alerts = c.fetchone()[0]
                
                c.execute("SELECT COUNT(*) FROM dns_logs")
                total_dns_logs = c.fetchone()[0]
                
                db_connected = True
            except:
                pass
            finally:
                conn.close()
        
        return jsonify({
            'suricata_running': suricata_running,
            'database_connected': db_connected,
            'total_alerts': total_alerts,
            'total_dns_logs': total_dns_logs,
            'last_updated': datetime.datetime.now().isoformat(),
            'status': 'operational' if db_connected else 'degraded'
        })
        
    except Exception as e:
        logger.error(f"Error getting NIDS status: {str(e)}")
        return jsonify({'error': 'Failed to get NIDS status'}), 500

# ============== END NIDS API ENDPOINTS ==============

# Global Kismet process variable
kismet_process = None
kismet_config_file = None
KISMET_API_KEY = "4EB980F446769D0164739F9301A5C793"
KISMET_HOST = "localhost"
KISMET_PORT = 2501

@app.route('/api/kismet/start', methods=['POST'])
def start_kismet():
    """Start Kismet wireless monitoring"""
    global kismet_process, kismet_config_file
    try:
        # Check if Kismet is already running
        if kismet_process and kismet_process.poll() is None:
            return jsonify({
                'success': False,
                'message': 'Kismet is already running'
            }), 400
        
        # Determine best interface to use
        requested_interface = request.json.get('interface') if request.json else None
        
        # Check for available wireless interfaces
        available_interfaces = []
        try:
            result = subprocess.run(['ip', 'link', 'show'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if 'wlan' in line and ':' in line:
                    interface_name = line.split(':')[1].strip().split('@')[0]
                    available_interfaces.append(interface_name)
        except:
            pass
        
        # Prefer monitor interfaces, then requested interface, then wlan0
        interface = None
        if requested_interface and requested_interface in available_interfaces:
            interface = requested_interface
        elif 'wlan0mon' in available_interfaces:
            interface = 'wlan0mon'
        elif 'wlan1mon' in available_interfaces:
            interface = 'wlan1mon'
        elif 'wlan0' in available_interfaces:
            interface = 'wlan0'
        elif available_interfaces:
            interface = available_interfaces[0]
        else:
            interface = 'wlan0'  # fallback
        
        logger.info(f"Starting Kismet on interface {interface} (available: {available_interfaces})")
        
        # Build Kismet command with sudo (required for monitor mode)
        kismet_cmd = ['sudo', 'kismet', '-c', interface]
        
        logger.info(f"Running command: {' '.join(kismet_cmd)}")
        
        # Start Kismet process
        kismet_process = subprocess.Popen(
            kismet_cmd,
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid if hasattr(os, 'setsid') else None
        )
        
        # Give it a moment to start
        time.sleep(3)
        
        # Check if process started successfully
        if kismet_process.poll() is not None:
            # Process has already terminated, get error output
            stdout, stderr = kismet_process.communicate()
            error_msg = stderr.decode('utf-8') if stderr else stdout.decode('utf-8')
            logger.error(f"Kismet failed to start: {error_msg}")
            return jsonify({
                'success': False,
                'message': f'Kismet failed to start: {error_msg[:200]}...' if len(error_msg) > 200 else error_msg,
                'interface': interface,
                'command_used': ' '.join(kismet_cmd)
            }), 500
        
        # Check if process is still running
        if kismet_process.poll() is None:
            return jsonify({
                'success': True,
                'message': f'Kismet started successfully on interface {interface}',
                'interface': interface,
                'pid': kismet_process.pid
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to start Kismet - check interface and permissions'
            }), 500
            
    except Exception as e:
        logger.error(f"Error starting Kismet: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to start Kismet: {str(e)}'
        }), 500

@app.route('/api/kismet/stop', methods=['POST'])
def stop_kismet():
    """Stop Kismet wireless monitoring"""
    global kismet_process, kismet_config_file
    try:
        if kismet_process and kismet_process.poll() is None:
            try:
                # Try graceful termination first
                kismet_process.terminate()
                kismet_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if necessary
                try:
                    if hasattr(os, 'killpg'):
                        os.killpg(os.getpgid(kismet_process.pid), signal.SIGKILL)
                    else:
                        kismet_process.kill()
                    kismet_process.wait(timeout=5)
                except:
                    # Last resort - use sudo pkill
                    try:
                        subprocess.run(['sudo', '-n', 'pkill', '-f', 'kismet'], timeout=5)
                    except:
                        pass
            
            kismet_process = None
            
            logger.info("Kismet stopped successfully")
            return jsonify({
                'success': True,
                'message': 'Kismet stopped successfully'
            })
        else:
            # Check if Kismet is running outside our process control
            try:
                result = subprocess.run(['pgrep', '-f', 'kismet'], capture_output=True, text=True)
                if result.stdout.strip():
                    # Kismet is running but not under our control
                    try:
                        subprocess.run(['sudo', '-n', 'pkill', '-f', 'kismet'], timeout=5)
                        return jsonify({
                            'success': True,
                            'message': 'External Kismet process stopped'
                        })
                    except:
                        return jsonify({
                            'success': False,
                            'message': 'Kismet is running but cannot be stopped (permission denied)'
                        }), 400
                else:
                    return jsonify({
                        'success': False,
                        'message': 'Kismet is not running'
                    }), 400
            except:
                return jsonify({
                    'success': False,
                    'message': 'Kismet is not running'
                }), 400
            
    except Exception as e:
        logger.error(f"Error stopping Kismet: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to stop Kismet: {str(e)}'
        }), 500

@app.route('/api/kismet/status', methods=['GET'])
def get_kismet_status():
    """Get Kismet status and basic statistics"""
    global kismet_process
    try:
        is_running = kismet_process and kismet_process.poll() is None
        
        # Also check if Kismet is running outside our process control
        if not is_running:
            try:
                result = subprocess.run(['pgrep', '-f', '^kismet'], capture_output=True, text=True)
                external_pids = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
                if external_pids:
                    # Filter out grep processes
                    valid_pids = []
                    for pid in external_pids:
                        try:
                            # Check the actual command line
                            cmd_result = subprocess.run(['ps', '-p', pid, '-o', 'cmd='], 
                                                      capture_output=True, text=True)
                            if cmd_result.returncode == 0 and 'kismet' in cmd_result.stdout and 'grep' not in cmd_result.stdout:
                                valid_pids.append(pid)
                        except:
                            pass
                    is_running = len(valid_pids) > 0
            except:
                pass
        
        status_data = {
            'running': bool(is_running),
            'pid': kismet_process.pid if is_running and kismet_process else None
        }
        
        # If Kismet is running, try to get data from its REST API
        if is_running:
            try:
                import requests
                # Try to get basic system status from Kismet
                response = requests.get(
                    f'http://{KISMET_HOST}:{KISMET_PORT}/system/status.json',
                    auth=('kali', 'kali'),
                    timeout=5
                )
                if response.status_code == 200:
                    kismet_data = response.json()
                    status_data.update({
                        'kismet_version': kismet_data.get('kismet.system.version', 'Unknown'),
                        'uptime': kismet_data.get('kismet.system.uptime', 0),
                        'memory': kismet_data.get('kismet.system.memory', {})
                    })
                
                # Get device count
                devices_response = requests.get(
                    f'http://{KISMET_HOST}:{KISMET_PORT}/devices/last-time/0/devices.json',
                    auth=('kali', 'kali'),
                    timeout=5
                )
                if devices_response.status_code == 200:
                    devices_data = devices_response.json()
                    status_data['device_count'] = len(devices_data)
                
            except Exception as api_error:
                logger.warning(f"Could not connect to Kismet API: {api_error}")
                status_data['api_error'] = str(api_error)
        
        return jsonify(status_data)
        
    except Exception as e:
        logger.error(f"Error getting Kismet status: {str(e)}")
        return jsonify({
            'error': f'Failed to get Kismet status: {str(e)}'
        }), 500

@app.route('/api/kismet/devices', methods=['GET'])
def get_kismet_devices():
    """Get detected devices from Kismet"""
    try:
        # Check if Kismet is running - simplified check with timeout
        kismet_running = False
        
        # First check our own process
        if kismet_process and kismet_process.poll() is None:
            kismet_running = True
        else:
            # Quick check for external Kismet processes
            try:
                result = subprocess.run(['pgrep', 'kismet'], capture_output=True, text=True, timeout=2)
                if result.returncode == 0 and result.stdout.strip():
                    kismet_running = True
            except subprocess.TimeoutExpired:
                logger.warning("Process check timed out")
            except:
                pass
        
        if not kismet_running:
            return jsonify({
                'success': False,
                'message': 'Kismet is not running'
            }), 400
        
        try:
            import requests
            # Get devices from Kismet API with longer timeout
            response = requests.get(
                f'http://{KISMET_HOST}:{KISMET_PORT}/devices/last-time/0/devices.json',
                auth=('kali', 'kali'),
                timeout=15
            )
            
            if response.status_code == 200:
                devices_data = response.json()
                
                # First pass: Create BSSID to SSID mapping from Access Points (optimized)
                bssid_to_ssid = {}
                logger.info(f"Processing {len(devices_data)} devices for BSSID mapping")
                
                try:
                    ap_count = 0
                    for device in devices_data:
                        device_type = device.get('kismet.device.base.type', 'Unknown')
                        if 'AP' in device_type:
                            ap_count += 1
                            bssid = device.get('kismet.device.base.macaddr', '')
                            dot11_device = device.get('dot11.device', {})
                            if dot11_device and bssid:
                                # Get the SSID from advertised SSID map (simplified)
                                ssid = None
                                advertised_ssid_map = dot11_device.get('dot11.device.advertised_ssid_map', {})
                                
                                if isinstance(advertised_ssid_map, list) and len(advertised_ssid_map) > 0:
                                    ssid = advertised_ssid_map[0].get('dot11.advertisedssid.ssid', '')
                                elif isinstance(advertised_ssid_map, dict):
                                    for ssid_data in advertised_ssid_map.values():
                                        if isinstance(ssid_data, dict):
                                            ssid = ssid_data.get('dot11.advertisedssid.ssid', '')
                                            if ssid:
                                                break
                                
                                # Store mapping if we found a valid SSID
                                if ssid:
                                    bssid_to_ssid[bssid] = ssid
                    
                    logger.info(f"Processed {ap_count} APs, found {len(bssid_to_ssid)} with SSIDs")
                
                except Exception as mapping_error:
                    logger.warning(f"Error building BSSID to SSID mapping: {mapping_error}")
                    # Continue with empty mapping if there's an error
                
                # Second pass: Process and simplify device data (optimized)
                processed_devices = []
                client_count = 0
                ap_count = 0
                
                try:
                    for device in devices_data:
                        try:
                            # Extract basic device information
                            mac = device.get('kismet.device.base.macaddr', 'Unknown')
                            device_type = device.get('kismet.device.base.type', 'Unknown')
                            device_name = device.get('kismet.device.base.name', 'Unknown Device')
                            
                            # Initialize connection info
                            connected_ap = 'N/A'
                            connected_ssid = 'N/A'
                            
                            # Handle client devices
                            if 'Client' in device_type:
                                client_count += 1
                                dot11_device = device.get('dot11.device', {})
                                if dot11_device:
                                    # Check for last connected BSSID
                                    last_bssid = dot11_device.get('dot11.device.last_bssid', '')
                                    if last_bssid and last_bssid in bssid_to_ssid:
                                        connected_ssid = bssid_to_ssid[last_bssid]
                                        connected_ap = f"{last_bssid} ({connected_ssid})"
                            
                            # Handle access points
                            elif 'AP' in device_type:
                                ap_count += 1
                                connected_ssid = bssid_to_ssid.get(mac, 'Unknown SSID')
                                connected_ap = f"{mac} (Self - {connected_ssid})"
                            
                            # Create simplified device object
                            processed_device = {
                                'mac': mac,
                                'name': device_name,
                                'type': device_type,
                                'manufacturer': device.get('kismet.device.base.manuf', 'Unknown'),
                                'first_seen': device.get('kismet.device.base.first_time', 0),
                                'last_seen': device.get('kismet.device.base.last_time', 0),
                                'packets': device.get('kismet.device.base.packets.total', 0),
                                'signal': device.get('kismet.device.base.signal', {}).get('kismet.common.signal.last_signal', 0),
                                'connected_ap': connected_ap,
                                'connected_ssid': connected_ssid
                            }
                            processed_devices.append(processed_device)
                            
                        except Exception as device_error:
                            logger.warning(f"Error processing device {device.get('kismet.device.base.macaddr', 'Unknown')}: {device_error}")
                            continue
                
                    logger.info(f"Processed {len(processed_devices)} devices ({ap_count} APs, {client_count} clients)")
                
                except Exception as processing_error:
                    logger.error(f"Error processing devices: {processing_error}")
                    # Return what we have so far
                
                return jsonify({
                    'success': True,
                    'devices': processed_devices,
                    'count': len(processed_devices),
                    'bssid_mappings': bssid_to_ssid
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f'Kismet API returned status {response.status_code}'
                }), 500
                
        except Exception as api_error:
            logger.error(f"Kismet API error: {api_error}")
            return jsonify({
                'success': False,
                'error': f'Failed to connect to Kismet API: {str(api_error)}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error getting Kismet devices: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to get devices: {str(e)}'
        }), 500

# Simple caching system for performance improvement
class SimpleCache:
    """Simple in-memory cache with TTL support"""
    
    def __init__(self, default_ttl=300):  # 5 minutes default
        self.cache = {}
        self.default_ttl = default_ttl
        self.lock = threading.Lock()
    
    def get(self, key):
        """Get value from cache if not expired"""
        with self.lock:
            if key in self.cache:
                value, expiry = self.cache[key]
                if time.time() < expiry:
                    return value
                else:
                    del self.cache[key]
            return None
    
    def set(self, key, value, ttl=None):
        """Set value in cache with TTL"""
        if ttl is None:
            ttl = self.default_ttl
        
        with self.lock:
            expiry = time.time() + ttl
            self.cache[key] = (value, expiry)
    
    def clear(self):
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
    
    def cleanup_expired(self):
        """Remove expired entries"""
        current_time = time.time()
        with self.lock:
            expired_keys = [
                key for key, (_, expiry) in self.cache.items() 
                if current_time >= expiry
            ]
            for key in expired_keys:
                del self.cache[key]

# Global cache instance
app_cache = SimpleCache()

# Cache cleanup thread
def cache_cleanup_worker():
    """Background thread to clean up expired cache entries"""
    while True:
        try:
            app_cache.cleanup_expired()
            time.sleep(60)  # Clean up every minute
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")
            time.sleep(60)

# Start cache cleanup thread
cleanup_thread = threading.Thread(target=cache_cleanup_worker, daemon=True)
cleanup_thread.start()

# Performance monitoring and error handling decorators
def monitor_performance(func):
    """Decorator to monitor endpoint performance"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"{func.__name__} completed in {duration:.3f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"{func.__name__} failed after {duration:.3f}s: {str(e)}")
            raise
    return wrapper

def handle_db_errors(func):
    """Decorator to handle database errors consistently"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except MySQLdb.Error as e:
            logger.error(f"Database error in {func.__name__}: {str(e)}")
            return jsonify({'error': 'Database operation failed'}), 500
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    return wrapper

# Configuration management
class Config:
    """Centralized configuration management"""
    
    @staticmethod
    def validate_db_config():
        """Validate database configuration"""
        required_keys = ['host', 'user', 'passwd', 'db']
        for key in required_keys:
            if not db_config.get(key):
                raise ValueError(f"Missing database configuration: {key}")
    
    @staticmethod
    def get_rate_limit():
        """Get rate limiting configuration"""
        return int(os.getenv('RATE_LIMIT', 100))
    
    @staticmethod
    def get_max_connections():
        """Get maximum database connections"""
        return int(os.getenv('MAX_DB_CONNECTIONS', 10))

# Validate configuration on startup
try:
    Config.validate_db_config()
    logger.info("Configuration validation passed")
except ValueError as e:
    logger.error(f"Configuration error: {e}")
    raise

# Start the Flask application when this file is run directly
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5053))  # Changed to 5053
    app.run(host='0.0.0.0', port=port, debug=True)
    logger.info(f"Server started on port {port}")