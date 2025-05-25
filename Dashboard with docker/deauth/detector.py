from scapy.all import *
from datetime import datetime, timedelta
import uuid
import MySQLdb
import time
import subprocess
import sys

# Function to check and start MySQL service if needed
def ensure_mysql_is_running():
    """Check if MySQL service is running and try to start it if not"""
    try:
        # Check if MySQL service is running
        result = subprocess.run(['systemctl', 'is-active', 'mysql'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE,
                              text=True)
        
        # If not active, try to start it
        if result.stdout.strip() != "active":
            print("[!] MySQL service is not running")
            print("[*] Attempting to start MySQL service...")
            
            # Try to start the service
            start_result = subprocess.run(['sudo', 'systemctl', 'start', 'mysql'], 
                                        stdout=subprocess.PIPE, 
                                        stderr=subprocess.PIPE,
                                        text=True)
            
            # Check if start was successful
            if start_result.returncode == 0:
                print("[+] MySQL service started successfully")
                return True
            else:
                print(f"[!] Failed to start MySQL service: {start_result.stderr.strip()}")
                return False
        else:
            return True
    except Exception as e:
        print(f"[!] Error checking MySQL service: {str(e)}")
        return False

# Configuration
iface = "wlan1"
threshold = 5
time_window = 5
deauth_times = []
last_saved_attack = None  # Track the last saved attack to avoid duplicates

# Dictionary: BSSID (MAC) → SSID
ssid_map = {}

# MySQL database configuration
db_config = {
    'host': '127.0.0.1',  # Use IP instead of 'localhost' to force TCP connection
    'port': 3306,         # Explicit TCP port
    'user': 'dashboard',
    'passwd': 'securepass',
    'db': 'security_dashboard',
    'connect_timeout': 5
}

# Connection retry settings
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

def verify_database_connection():
    """Verify database connection and create table if needed"""
    print("[*] Verifying database connection...")
    
    for attempt in range(MAX_RETRIES):
        try:
            conn = MySQLdb.connect(**db_config)
            cursor = conn.cursor()
            
            # Check if the table exists
            cursor.execute("SHOW TABLES LIKE 'network_attacks'")
            if not cursor.fetchone():
                print("[*] Creating network_attacks table...")
                cursor.execute("""
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
                """)
                conn.commit()
                print("[+] Table created successfully")
            
            conn.close()
            print("[+] Database connection verified successfully")
            return True
            
        except MySQLdb.Error as e:
            print(f"[!] Database connection attempt {attempt+1} failed: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                print(f"[*] Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                print("[!] Failed to connect to database after multiple attempts")
                print("[!] Make sure MySQL server is running and accessible")
                print("[!] Continuing without database logging...")
                return False

def save_to_database(attack_data):
    """Save attack data to MySQL database"""
    global last_saved_attack
    
    try:
        # Check if this is a duplicate of the last attack (within 2 seconds)
        if last_saved_attack:
            last_time = datetime.strptime(last_saved_attack["timestamp"], '%Y-%m-%d %H:%M:%S')
            current_time = datetime.strptime(attack_data["timestamp"], '%Y-%m-%d %H:%M:%S')
            time_diff = (current_time - last_time).total_seconds()
            
            if (time_diff < 2 and 
                attack_data["attacker_bssid"] == last_saved_attack["attacker_bssid"] and 
                attack_data["destination_bssid"] == last_saved_attack["destination_bssid"]):
                # Duplicate attack (same source/dest within 2 seconds), skip logging
                return True
        
        # Attempt connection with retries
        conn = None
        for attempt in range(MAX_RETRIES):
            try:
                conn = MySQLdb.connect(**db_config)
                break
            except MySQLdb.OperationalError as e:
                if attempt < MAX_RETRIES - 1:
                    print(f"[!] Database connection attempt {attempt+1} failed: {str(e)}")
                    print(f"[*] Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    raise
        
        if not conn:
            raise Exception("Failed to connect to database after multiple attempts")
            
        cursor = conn.cursor()
        
        # Generate a unique ID for this attack
        attack_id = str(uuid.uuid4())
        
        # Insert the attack record into the network_attacks table
        cursor.execute(
            """
            INSERT INTO network_attacks
            (id, timestamp, alert_type, attacker_bssid, attacker_ssid, 
             destination_bssid, destination_ssid, attack_count)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                attack_id,
                attack_data["timestamp"],
                attack_data["alert_type"],
                attack_data["attacker_bssid"],
                attack_data["attacker_ssid"],
                attack_data["destination_bssid"],
                attack_data["destination_ssid"],
                attack_data["count"]
            )
        )
        
        conn.commit()
        conn.close()
        print(f"[+] Attack data saved to database with ID: {attack_id}")
        
        # Remember this attack to avoid duplicates
        last_saved_attack = attack_data
        return True
    except MySQLdb.OperationalError as e:
        print(f"[!] Database connection error: {str(e)}")
        print("[*] Make sure MySQL server is running and accessible")
        return False
    except Exception as e:
        print(f"[!] Database error: {str(e)}")
        return False

def packet_handler(pkt):
    global deauth_times, ssid_map, db_connected

    # Record SSIDs from beacons/probes
    if pkt.haslayer(Dot11Beacon) or pkt.haslayer(Dot11ProbeResp):
        bssid = pkt[Dot11].addr2
        ssid = pkt[Dot11Elt].info.decode(errors="ignore")
        if ssid:
            ssid_map[bssid] = ssid

    # Detect deauth packets
    if pkt.haslayer(Dot11Deauth):
        now = datetime.now()
        deauth_times.append(now)

        # Clean up old timestamps
        deauth_times = [t for t in deauth_times if now - t < timedelta(seconds=time_window)]

        src_mac = pkt[Dot11].addr1  # Attacker BSSID
        dst_mac = pkt[Dot11].addr2  # Victim/Target BSSID

        attacker_ssid = ssid_map.get(src_mac, "Unknown")
        dest_ssid = ssid_map.get(dst_mac, "Unknown")

        print(f"[!] Deauth detected at {now.strftime('%H:%M:%S')}")
        print(f"    → Attacker: {src_mac} ({attacker_ssid})")
        print(f"    → Target:   {dst_mac} ({dest_ssid})")
        print(f"    → Total in window: {len(deauth_times)}\n")

        # Always log every deauth packet (if above threshold)
        if len(deauth_times) >= threshold:
            print("\n[!!!] ALERT: Possible deauthentication attack detected!\n")

            # Prepare the log entry as a dictionary
            log_entry = {
                "timestamp": now.strftime('%Y-%m-%d %H:%M:%S'),
                "alert_type": "Deauth Attack",
                "count": len(deauth_times),
                "attacker_bssid": src_mac,
                "attacker_ssid": attacker_ssid,
                "destination_bssid": dst_mac,
                "destination_ssid": dest_ssid
            }

            # Save attack data to MySQL database only if connected
            if db_connected:
                save_result = save_to_database(log_entry)
                # If save failed, try to reconnect
                if not save_result:
                    db_connected = verify_database_connection()
            else:
                print("[!] Attack detected but not saved to database (database connection issues)")
        
        # Even if we haven't hit threshold yet, log single packets sometimes
        # This helps make threat visualization more interesting
        elif len(deauth_times) > 1 and len(deauth_times) % 5 == 0 and db_connected:
            # Log every 5th packet even before threshold
            log_entry = {
                "timestamp": now.strftime('%Y-%m-%d %H:%M:%S'),
                "alert_type": "Deauth Packet",  # Different name to distinguish from attack
                "count": len(deauth_times),
                "attacker_bssid": src_mac,
                "attacker_ssid": attacker_ssid,
                "destination_bssid": dst_mac,
                "destination_ssid": dest_ssid
            }
            save_to_database(log_entry)


# Main execution
print(f"[*] Starting deauth detector on interface: {iface}")

# Try to ensure MySQL is running
mysql_check = ensure_mysql_is_running()
if not mysql_check:
    print("[!] Warning: Could not verify MySQL service status")
    print("[*] Will attempt to connect anyway...")

# Verify database connection
db_connected = verify_database_connection()
if db_connected:
    print(f"[*] Attacks will be logged directly to MySQL database in real-time.")
else:
    print(f"[*] WARNING: Database logging is disabled due to connection issues.")
    print(f"[*] Attack detections will only be displayed in console output.")

print(f"[*] Attack threshold is {threshold} deauth packets within {time_window} seconds.")
print(f"[*] Starting packet capture. Press Ctrl+C to stop.")

try:
    sniff(iface=iface, prn=packet_handler, store=0)
except KeyboardInterrupt:
    print("\n[*] Detector stopped by user.")
except Exception as e:
    print(f"\n[!] Error: {str(e)}")
    print("[*] Detector stopped due to an error.")