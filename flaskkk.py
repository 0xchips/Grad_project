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
import signal
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

# Import Nessus scanner
try:
    from nessus_scanner import NessusScanner
    NESSUS_AVAILABLE = True
except ImportError:
    NESSUS_AVAILABLE = False
    logger.warning("Nessus scanner module not available")

# Global Nessus scanner instance
nessus_scanner = None
if NESSUS_AVAILABLE:
    nessus_scanner = NessusScanner(host='localhost', port=8834, username='chips', password='chips')

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

@app.route('/api/nessus/scan/start', methods=['POST'])
def start_nessus_scan():
    """Start a Nessus vulnerability scan"""
    try:
        # Rate limiting
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if not rate_limit_check(client_ip):
            logger.warning(f"Rate limited request from {client_ip}")
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
        if not NESSUS_AVAILABLE or not nessus_scanner:
            return jsonify({
                'error': 'Scanner not available',
                'message': 'Scanner module not properly configured'
            }), 500

        data = request.get_json() or {}
        targets = data.get('targets', '192.168.1.0/24')
        scan_name = data.get('scan_name', f'CyberShield_Scan_{int(time.time())}')
        
        logger.info(f"Starting security scan for targets: {targets}")
        
        # Start the scan and get initial result
        initial_result = nessus_scanner.run_full_scan(targets)
        
        if initial_result.get('success'):
            scanner_type = initial_result.get('scanner_type', 'unknown')
            if scanner_type == 'fallback':
                message = f'Security scan initiated using built-in Kali tools for targets: {targets}'
                scan_info = f'Using: {", ".join(initial_result.get("tools_available", {}).keys())}'
            else:
                message = f'Professional vulnerability scan initiated for targets: {targets}'
                scan_info = 'Using: Nessus Professional Scanner'
        else:
            message = initial_result.get('message', 'Scan initiation failed')
            scan_info = initial_result.get('error', 'Unknown error')
        
        return jsonify({
            'success': initial_result.get('success', False),
            'message': message,
            'targets': targets,
            'scan_name': scan_name,
            'status': 'starting',
            'scanner_type': initial_result.get('scanner_type', 'unknown'),
            'scan_info': scan_info,
            'tools_available': initial_result.get('tools_available', {})
        })
        
    except Exception as e:
        logger.error(f"Error starting Nessus scan: {str(e)}")
        return jsonify({
            'error': 'Failed to start scan',
            'message': str(e)
        }), 500

@app.route('/api/nessus/scan/status', methods=['GET'])
def get_nessus_scan_status():
    """Get current scan status (Nessus or fallback scanner)"""
    try:
        # Rate limiting
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if not rate_limit_check(client_ip):
            logger.warning(f"Rate limited request from {client_ip}")
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
        if not nessus_scanner:
            return jsonify({
                'error': 'Scanner not available'
            }), 500

        scan_id = request.args.get('scan_id')
        
        if scan_id:
            try:
                scan_id = int(scan_id)
                status = nessus_scanner.get_scan_status(scan_id)
            except ValueError:
                return jsonify({'error': 'Invalid scan ID'}), 400
        else:
            status = nessus_scanner.get_scan_status()
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting scan status: {str(e)}")
        return jsonify({
            'error': 'Failed to get scan status',
            'message': str(e)
        }), 500

@app.route('/api/nessus/scan/results', methods=['GET'])
def get_nessus_scan_results():
    """Get scan results (Nessus or fallback scanner)"""
    try:
        # Rate limiting
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if not rate_limit_check(client_ip):
            logger.warning(f"Rate limited request from {client_ip}")
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
        if not nessus_scanner:
            return jsonify({
                'error': 'Scanner not available'
            }), 500

        scan_id = request.args.get('scan_id')
        
        if scan_id:
            try:
                scan_id = int(scan_id)
                results = nessus_scanner.get_scan_results(scan_id)
            except ValueError:
                return jsonify({'error': 'Invalid scan ID'}), 400
        else:
            results = nessus_scanner.get_scan_results()
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error getting Nessus scan results: {str(e)}")
        return jsonify({
            'error': 'Failed to get scan results',
            'message': str(e)
        }), 500

@app.route('/api/nessus/scan/report', methods=['GET'])
def export_nessus_report():
    """Export scan report (Nessus or fallback scanner)"""
    try:
        # Rate limiting
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if not rate_limit_check(client_ip):
            logger.warning(f"Rate limited request from {client_ip}")
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
        if not nessus_scanner:
            return jsonify({
                'error': 'Scanner not available'
            }), 500

        scan_id = request.args.get('scan_id')
        format_type = request.args.get('format', 'pdf')
        
        if scan_id:
            try:
                scan_id = int(scan_id)
            except ValueError:
                return jsonify({'error': 'Invalid scan ID'}), 400
        
        report_path = nessus_scanner.export_scan_report(scan_id, format_type)
        
        if report_path and os.path.exists(report_path):
            return jsonify({
                'success': True,
                'report_path': report_path,
                'message': f'Report exported successfully'
            })
        else:
            return jsonify({
                'error': 'Failed to export report'
            }), 500
        
    except Exception as e:
        logger.error(f"Error exporting Nessus report: {str(e)}")
        return jsonify({
            'error': 'Failed to export report',
            'message': str(e)
        }), 500

@app.route('/api/nessus/setup', methods=['POST'])
def setup_nessus():
    """Setup and configure Nessus scanner"""
    try:
        # Rate limiting
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if not rate_limit_check(client_ip):
            logger.warning(f"Rate limited request from {client_ip}")
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
        if not NESSUS_AVAILABLE:
            return jsonify({
                'error': 'Nessus scanner module not available',
                'message': 'Please ensure nessus_scanner.py is in the dashboard directory'
            }), 500

        logger.info("Starting Nessus setup process...")
        
        # Run setup in background thread
        def run_setup():
            try:
                global nessus_scanner
                if not nessus_scanner:
                    nessus_scanner = NessusScanner(host='localhost', port=8834, username='chips', password='chips')
                
                success = nessus_scanner.setup_nessus()
                logger.info(f"Nessus setup completed: {success}")
            except Exception as e:
                logger.error(f"Nessus setup error: {str(e)}")
        
        setup_thread = threading.Thread(target=run_setup)
        setup_thread.daemon = True
        setup_thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Nessus setup initiated. This may take several minutes...',
            'status': 'setting_up'
        })
        
    except Exception as e:
        logger.error(f"Error setting up Nessus: {str(e)}")
        return jsonify({
            'error': 'Failed to setup Nessus',
            'message': str(e)
        }), 500

@app.route('/api/nessus/scan/stop', methods=['POST'])
def stop_nessus_scan():
    """Stop any running vulnerability scan (Nessus or fallback)"""
    try:
        # Rate limiting
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if not rate_limit_check(client_ip):
            logger.warning(f"Rate limited request from {client_ip}")
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
        if not nessus_scanner:
            return jsonify({
                'error': 'Scanner not available'
            }), 500

        # Stop the scan
        result = nessus_scanner.stop_scan()
        
        # Log the action
        logger.info(f"Scan stop requested by {client_ip}: {result}")
        
        return jsonify({
            'success': True,
            'message': result.get('message', 'Scan stop requested'),
        })
        
    except Exception as e:
        logger.error(f"Error stopping scan: {str(e)}")
        return jsonify({
            'error': 'Failed to stop scan',
            'message': str(e)
        }), 500

@app.route('/api/nessus/full-scan-with-discovery', methods=['POST'])
def start_full_scan_with_discovery():
    """Start a complete scan: first discover network devices, then run Nessus scan on discovered IPs"""
    try:
        # Rate limiting
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if not rate_limit_check(client_ip):
            logger.warning(f"Rate limited request from {client_ip}")
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
        logger.info("Starting full scan with network discovery...")
        
        # Step 1: Network Discovery using netdiscover.py
        try:
            logger.info("Running network discovery...")
            result = subprocess.run(['python3', 'netdiscover.py'], 
                                  capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                logger.warning(f"Network discovery failed: {result.stderr}")
                # Fall back to default network range
                discovered_ips = []
                target_range = "192.168.1.0/24"
            else:
                # Parse the JSON output from netdiscover.py
                output = result.stdout
                json_start = output.find('[JSON_START]')
                json_end = output.find('[JSON_END]')
                
                if json_start != -1 and json_end != -1:
                    json_data = output[json_start + 12:json_end]  # +12 to skip '[JSON_START]'
                    try:
                        devices = json.loads(json_data)
                        discovered_ips = [device['ip'] for device in devices if device.get('ip')]
                        logger.info(f"Discovered {len(discovered_ips)} network devices")
                        
                        # Create target string from discovered IPs
                        if discovered_ips:
                            target_range = ','.join(discovered_ips)
                        else:
                            target_range = "192.168.1.0/24"  # Fallback
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse network discovery JSON")
                        discovered_ips = []
                        target_range = "192.168.1.0/24"
                else:
                    logger.warning("No JSON output found from network discovery")
                    discovered_ips = []
                    target_range = "192.168.1.0/24"
                    
        except subprocess.TimeoutExpired:
            logger.warning("Network discovery timed out")
            discovered_ips = []
            target_range = "192.168.1.0/24"
        except Exception as e:
            logger.error(f"Network discovery error: {str(e)}")
            discovered_ips = []
            target_range = "192.168.1.0/24"
        
        # Step 2: Start Nessus scan on discovered targets
        if not NESSUS_AVAILABLE or not nessus_scanner:
            return jsonify({
                'error': 'Scanner not available',
                'message': 'Nessus scanner module not properly configured'
            }), 500

        data = request.get_json() or {}
        scan_name = data.get('scan_name', f'CyberShield_Full_Discovery_Scan_{int(time.time())}')
        
        logger.info(f"Starting Nessus scan for discovered targets: {target_range}")
        
        # Start the scan
        initial_result = nessus_scanner.run_full_scan(target_range)
        
        if initial_result.get('success'):
            scanner_type = initial_result.get('scanner_type', 'unknown')
            if scanner_type == 'fallback':
                message = f'Full security scan initiated (discovered {len(discovered_ips)} devices) using built-in tools'
                scan_info = f'Network Discovery + Security Tools: {", ".join(initial_result.get("tools_available", {}).keys())}'
            else:
                message = f'Full vulnerability scan initiated (discovered {len(discovered_ips)} devices) using Nessus'
                scan_info = 'Network Discovery + Nessus Professional Scanner'
        else:
            message = initial_result.get('message', 'Scan initiation failed')
            scan_info = initial_result.get('error', 'Unknown error')
        
        return jsonify({
            'success': initial_result.get('success', False),
            'message': message,
            'targets': target_range,
            'discovered_devices': len(discovered_ips),
            'discovered_ips': discovered_ips[:10],  # Limit to first 10 for response size
            'scan_name': scan_name,
            'status': 'starting',
            'scanner_type': initial_result.get('scanner_type', 'unknown'),
            'scan_info': scan_info,
            'tools_available': initial_result.get('tools_available', {})
        })
        
    except Exception as e:
        logger.error(f"Error in full scan with discovery: {str(e)}")
        return jsonify({
            'error': 'Failed to start full scan',
            'message': str(e)
        }), 500

@app.route('/download-report', methods=['GET'])
def download_report():
    """Download generated scan report"""
    try:
        # Rate limiting
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if not rate_limit_check(client_ip):
            logger.warning(f"Rate limited request from {client_ip}")
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
        report_path = request.args.get('path')
        if not report_path:
            return jsonify({'error': 'No report path specified'}), 400
        
        # Security check: ensure the path is in /tmp and is a valid report file
        if not report_path.startswith('/tmp/cybershield_scan_report_'):
            return jsonify({'error': 'Invalid report path'}), 403
        
        if not os.path.exists(report_path):
            return jsonify({'error': 'Report file not found'}), 404
        
        from flask import send_file
        return send_file(report_path, as_attachment=True)
        
    except Exception as e:
        logger.error(f"Error downloading report: {str(e)}")
        return jsonify({'error': 'Failed to download report'}), 500

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
        # Rate limiting
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if not rate_limit_check(client_ip):
            logger.warning(f"Rate limited request from {client_ip}")
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
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
        # Rate limiting
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if not rate_limit_check(client_ip):
            logger.warning(f"Rate limited request from {client_ip}")
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
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
        # Rate limiting
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if not rate_limit_check(client_ip):
            logger.warning(f"Rate limited request from {client_ip}")
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
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
        # Rate limiting
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if not rate_limit_check(client_ip):
            logger.warning(f"Rate limited request from {client_ip}")
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
        # Check if Kismet is running
        if not (kismet_process and kismet_process.poll() is None):
            return jsonify({
                'success': False,
                'message': 'Kismet is not running'
            }), 400
        
        try:
            import requests
            # Get devices from Kismet API
            response = requests.get(
                f'http://{KISMET_HOST}:{KISMET_PORT}/devices/last-time/0/devices.json',
                auth=('kali', 'kali'),
                timeout=10
            )
            
            if response.status_code == 200:
                devices_data = response.json()
                
                # First pass: Create BSSID to SSID mapping from Access Points
                bssid_to_ssid = {}
                for device in devices_data:
                    device_type = device.get('kismet.device.base.type', 'Unknown')
                    if 'AP' in device_type or 'Access Point' in device_type:
                        bssid = device.get('kismet.device.base.macaddr', '')
                        dot11_device = device.get('dot11.device', {})
                        if dot11_device:
                            # Get the SSID from various possible locations
                            ssid = None
                            
                            # Try to get advertised SSID map
                            advertised_ssid_map = dot11_device.get('dot11.device.advertised_ssid_map', {})
                            if advertised_ssid_map:
                                for ssid_key, ssid_data in advertised_ssid_map.items():
                                    if isinstance(ssid_data, dict):
                                        ssid = ssid_data.get('dot11.advertisedssid.ssid', '')
                                        if ssid:
                                            break
                            
                            # Fallback: try to get from responded SSID map
                            if not ssid:
                                responded_ssid_map = dot11_device.get('dot11.device.responded_ssid_map', {})
                                if responded_ssid_map:
                                    for ssid_key, ssid_data in responded_ssid_map.items():
                                        if isinstance(ssid_data, dict):
                                            ssid = ssid_data.get('dot11.respondedssid.ssid', '')
                                            if ssid:
                                                break
                            
                            # Store BSSID to SSID mapping
                            if bssid and ssid:
                                bssid_to_ssid[bssid] = ssid
                
                # Second pass: Process and simplify device data
                processed_devices = []
                for device in devices_data:
                    # Extract AP association information
                    connected_ap = 'N/A'
                    connected_ssid = 'N/A'
                    device_type = device.get('kismet.device.base.type', 'Unknown')
                    
                    # For client devices, try to find associated AP
                    if device_type == 'Wi-Fi Client' or 'client' in device_type.lower():
                        # Check for associated access point
                        dot11_device = device.get('dot11.device', {})
                        if dot11_device:
                            associated_ap = dot11_device.get('dot11.device.associated_client_map', {})
                            if associated_ap:
                                # Get first associated AP BSSID
                                for ap_mac in associated_ap.keys():
                                    connected_ap = ap_mac
                                    # Map BSSID to SSID if available
                                    connected_ssid = bssid_to_ssid.get(ap_mac, 'Unknown SSID')
                                    break
                            
                            # Alternative: check if this is a client and get the AP BSSID
                            if connected_ap == 'N/A':
                                client_map = dot11_device.get('dot11.device.client_map', {})
                                if not client_map:
                                    # Try another approach - look for BSSID in last SSID records
                                    last_bssid = dot11_device.get('dot11.device.last_bssid', None)
                                    if last_bssid and last_bssid != device.get('kismet.device.base.macaddr'):
                                        connected_ap = last_bssid
                                        connected_ssid = bssid_to_ssid.get(last_bssid, 'Unknown SSID')
                    
                    # For Access Points, get their own SSID
                    elif 'AP' in device_type or 'Access Point' in device_type:
                        bssid = device.get('kismet.device.base.macaddr', '')
                        connected_ssid = bssid_to_ssid.get(bssid, 'Unknown SSID')
                    
                    processed_device = {
                        'mac': device.get('kismet.device.base.macaddr', 'Unknown'),
                        'name': device.get('kismet.device.base.name', 'Unknown Device'),
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

# Start the Flask application when this file is run directly
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5050))
    app.run(host='0.0.0.0', port=port, debug=True)
    logger.info(f"Server started on port {port}")