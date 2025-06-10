#!/usr/bin/env python3
"""
Suricata Log Parser for NIDS Dashboard
Parses Suricata EVE JSON logs and inserts alerts and DNS events into MySQL database
"""

import json
import time
import uuid
import MySQLdb
import logging
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import sys
import threading
import signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('suricata_parser.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SuricataParser")

# MySQL Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'dashboard',
    'passwd': 'securepass',
    'db': 'security_dashboard',
}

# Suricata log file path
SURICATA_LOG_PATH = '/var/log/suricata/eve.json'

# Global variables
running = True
last_position = 0

def get_db_connection():
    """Get MySQL database connection"""
    try:
        conn = MySQLdb.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

def parse_timestamp(ts_str):
    """Parse Suricata timestamp to MySQL format"""
    try:
        # Remove timezone info for MySQL compatibility
        if '+' in ts_str:
            ts_str = ts_str.split('+')[0]
        elif '-' in ts_str and ts_str.count('-') > 2:
            # Handle negative timezone offset
            parts = ts_str.rsplit('-', 1)
            ts_str = parts[0]
        
        # Parse the timestamp
        dt = datetime.fromisoformat(ts_str.replace('T', ' '))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        logger.error(f"Error parsing timestamp {ts_str}: {e}")
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def classify_alert_severity(signature, sid):
    """Classify alert severity based on signature and SID"""
    signature_lower = signature.lower()
    
    # Critical threats
    if any(keyword in signature_lower for keyword in [
        'malware', 'trojan', 'backdoor', 'botnet', 'ransomware',
        'exploit kit', 'shellcode', 'command and control'
    ]):
        return 'critical'
    
    # High severity
    if any(keyword in signature_lower for keyword in [
        'exploit', 'attack', 'intrusion', 'scan', 'probe',
        'suspicious', 'policy violation', 'attempted'
    ]):
        return 'high'
    
    # Medium severity 
    if any(keyword in signature_lower for keyword in [
        'info', 'notice', 'warning', 'potential'
    ]):
        return 'medium'
    
    # Default to medium
    return 'medium'

def detect_suspicious_dns(query_name, query_type):
    """Simple suspicious DNS detection"""
    query_lower = query_name.lower()
    
    # Check for suspicious patterns
    suspicious_patterns = [
        # Domain generation algorithms
        r'[a-z0-9]{10,}\.com',
        r'[a-z0-9]{8,}\.net',
        # Suspicious TLDs
        '.tk', '.ml', '.ga', '.cf',
        # Tor hidden services (if somehow leaked)
        '.onion',
        # Suspicious subdomains
        'dga.', 'botnet.', 'malware.',
        # Mining pools
        'pool.', 'mining.',
    ]
    
    threat_type = None
    confidence = 0.0
    
    # Check for long random strings (DGA)
    if len(query_name) > 20 and query_name.count('.') <= 2:
        import re
        if re.match(r'^[a-z0-9]{12,}\.', query_lower):
            threat_type = 'domain_generation_algorithm'
            confidence = 0.8
    
    # Check suspicious TLDs
    for pattern in ['.tk', '.ml', '.ga', '.cf']:
        if pattern in query_lower:
            threat_type = 'suspicious_tld'
            confidence = 0.6
            break
    
    # Check for mining-related domains
    if any(keyword in query_lower for keyword in ['pool', 'mining', 'crypto']):
        threat_type = 'cryptomining'
        confidence = 0.7
    
    return threat_type, confidence

def insert_alert(conn, event_data):
    """Insert alert event into database"""
    try:
        c = conn.cursor()
        
        alert_data = event_data.get('alert', {})
        
        # Generate unique ID
        alert_id = str(uuid.uuid4())
        
        # Extract alert information
        timestamp = parse_timestamp(event_data.get('timestamp', ''))
        signature = alert_data.get('signature', 'Unknown Alert')
        severity = classify_alert_severity(signature, alert_data.get('signature_id', 0))
        source_ip = event_data.get('src_ip', '')
        destination_ip = event_data.get('dest_ip', '')
        source_port = event_data.get('src_port')
        destination_port = event_data.get('dest_port')
        protocol = event_data.get('proto', '')
        action = alert_data.get('action', 'alert')
        category = alert_data.get('category', '')
        signature_id = alert_data.get('signature_id')
        classification = alert_data.get('classification')
        flow_id = event_data.get('flow_id')
        
        # Insert into database
        c.execute("""
            INSERT INTO nids_alerts 
            (id, timestamp, alert_signature, alert_severity, source_ip, destination_ip,
             source_port, destination_port, protocol, action, category, signature_id,
             classification, flow_id, raw_log, nids_engine)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            alert_id, timestamp, signature, severity, source_ip, destination_ip,
            source_port, destination_port, protocol, action, category, signature_id,
            classification, flow_id, json.dumps(event_data), 'suricata'
        ))
        
        conn.commit()
        logger.info(f"Alert inserted: {signature} from {source_ip}")
        
    except Exception as e:
        logger.error(f"Error inserting alert: {e}")
        conn.rollback()

def insert_dns_event(conn, event_data):
    """Insert DNS event into database"""
    try:
        c = conn.cursor()
        
        dns_data = event_data.get('dns', {})
        
        # Generate unique ID
        dns_id = str(uuid.uuid4())
        
        # Extract DNS information
        timestamp = parse_timestamp(event_data.get('timestamp', ''))
        query_name = dns_data.get('rrname', '')
        query_type = dns_data.get('rrtype', '')
        response_code = dns_data.get('rcode', '')
        source_ip = event_data.get('src_ip', '')
        destination_ip = event_data.get('dest_ip', '')
        
        # Detect suspicious patterns
        threat_type, confidence = detect_suspicious_dns(query_name, query_type)
        is_suspicious = threat_type is not None
        
        # Insert into database
        c.execute("""
            INSERT INTO dns_logs 
            (id, timestamp, query_name, query_type, response_code, source_ip, destination_ip,
             is_suspicious, threat_type, confidence_score, raw_log)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            dns_id, timestamp, query_name, query_type, response_code, source_ip, destination_ip,
            is_suspicious, threat_type, confidence, json.dumps(event_data)
        ))
        
        conn.commit()
        
        if is_suspicious:
            logger.info(f"Suspicious DNS: {query_name} ({threat_type}) from {source_ip}")
        
    except Exception as e:
        logger.error(f"Error inserting DNS event: {e}")
        conn.rollback()

def process_log_line(line):
    """Process a single log line"""
    try:
        event_data = json.loads(line.strip())
        event_type = event_data.get('event_type')
        
        conn = get_db_connection()
        if not conn:
            return
        
        try:
            if event_type == 'alert':
                insert_alert(conn, event_data)
            elif event_type == 'dns':
                insert_dns_event(conn, event_data)
            # Add more event types as needed
            
        finally:
            conn.close()
            
    except json.JSONDecodeError:
        # Skip invalid JSON lines
        pass
    except Exception as e:
        logger.error(f"Error processing log line: {e}")

def read_existing_logs():
    """Read existing logs from the current position"""
    global last_position
    
    try:
        if not os.path.exists(SURICATA_LOG_PATH):
            logger.warning(f"Suricata log file not found: {SURICATA_LOG_PATH}")
            return
        
        with open(SURICATA_LOG_PATH, 'r') as f:
            # Seek to last position or start from end if first run
            if last_position == 0:
                f.seek(0, 2)  # Seek to end
                last_position = f.tell()
                logger.info("Starting from end of log file")
            else:
                f.seek(last_position)
            
            # Process new lines
            processed_lines = 0
            for line in f:
                if not running:
                    break
                process_log_line(line)
                processed_lines += 1
            
            # Update position
            last_position = f.tell()
            
            if processed_lines > 0:
                logger.info(f"Processed {processed_lines} new log entries")
                
    except Exception as e:
        logger.error(f"Error reading log file: {e}")

class LogFileHandler(FileSystemEventHandler):
    """Handle file system events for log file changes"""
    
    def on_modified(self, event):
        if not event.is_directory and event.src_path == SURICATA_LOG_PATH:
            read_existing_logs()

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global running
    logger.info("Received shutdown signal, stopping...")
    running = False

def main():
    """Main function"""
    global running
    
    logger.info("Starting Suricata log parser...")
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Test database connection
    conn = get_db_connection()
    if not conn:
        logger.error("Cannot connect to database, exiting")
        sys.exit(1)
    conn.close()
    
    # Read existing logs
    read_existing_logs()
    
    # Set up file watcher
    event_handler = LogFileHandler()
    observer = Observer()
    observer.schedule(event_handler, os.path.dirname(SURICATA_LOG_PATH), recursive=False)
    observer.start()
    
    logger.info("Log parser started, monitoring for new events...")
    
    try:
        while running:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        observer.stop()
        observer.join()
        logger.info("Suricata log parser stopped")

if __name__ == "__main__":
    main()
