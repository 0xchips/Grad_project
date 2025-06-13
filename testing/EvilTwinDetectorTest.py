from scapy.all import *
from termcolor import colored
import time
import uuid
import datetime
import requests
import json
import os
from dotenv import load_dotenv

# Database import with fallback
try:
    import MySQLdb
except ImportError:
    try:
        import pymysql
        pymysql.install_as_MySQLdb()
        import MySQLdb
    except ImportError:
        print(colored("[ERROR] No MySQL connector available. Install mysqlclient or pymysql.", "red"))
        MySQLdb = None

ap_list = {}
WHITELIST_BSSIDS = {
    "dc:8d:8a:b9:13:36", 
    "20:9a:7d:5c:83:a0",
    "cc:d4:2e:88:77:b6"
}

# Debug mode - set to True for verbose output
DEBUG_MODE = True

# Load environment variables
load_dotenv()

# Database configuration (matching the Flask app)
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'dashboard'),
    'passwd': os.getenv('DB_PASSWORD', 'securepass'),
    'db': os.getenv('DB_NAME', 'security_dashboard'),
}

# Flask server configuration
FLASK_SERVER_URL = "http://localhost:5053"

def get_db_connection():
    """Get database connection with error handling"""
    if MySQLdb is None:
        print(colored("[ERROR] No MySQL connector available", "red"))
        return None
    try:
        return MySQLdb.connect(**db_config)
    except Exception as e:
        print(colored(f"[ERROR] Database connection failed: {e}", "red"))
        return None

def send_evil_twin_alert(ssid, evil_bssid, legitimate_bssid, channel):
    """Send evil twin detection to database and Flask server"""
    try:
        # Generate unique ID for this detection
        alert_id = str(uuid.uuid4())
        current_timestamp = datetime.datetime.now()
        
        # Store in database
        conn = get_db_connection()
        if conn:
            try:
                c = conn.cursor()
                c.execute(
                    """
                    INSERT INTO network_attacks 
                    (id, timestamp, alert_type, type, attacker_bssid, attacker_ssid, 
                    destination_bssid, destination_ssid, attack_count)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        alert_id,
                        current_timestamp,
                        'Evil Twin Detected',
                        'evil-twin',
                        evil_bssid,
                        ssid,
                        legitimate_bssid,
                        ssid,
                        1
                    )
                )
                conn.commit()
                conn.close()
                print(colored(f"[+] Evil twin alert stored in database with ID: {alert_id}", "green"))
            except Exception as e:
                print(colored(f"[ERROR] Failed to store in database: {e}", "red"))
                if conn:
                    conn.close()
        
        # Send to Flask server (for real-time updates to deauth.html)
        try:
            payload = {
                'alert_type': 'Evil Twin Detected',
                'type': 'evil-twin',
                'attacker_bssid': evil_bssid,
                'attacker_ssid': ssid,
                'destination_bssid': legitimate_bssid,
                'destination_ssid': ssid,
                'attack_count': 1,
                'channel': channel,
                'event': 'evil_twin_detected'
            }
            
            response = requests.post(
                f"{FLASK_SERVER_URL}/api/deauth_logs",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            
            if response.status_code == 201:
                print(colored(f"[+] Evil twin alert sent to Flask server successfully", "green"))
            else:
                print(colored(f"[WARNING] Flask server responded with status: {response.status_code}", "yellow"))
                
        except requests.exceptions.RequestException as e:
            print(colored(f"[WARNING] Failed to send alert to Flask server: {e}", "yellow"))
            print(colored("[*] Alert stored in database but Flask server notification failed", "cyan"))
            
    except Exception as e:
        print(colored(f"[ERROR] Failed to send evil twin alert: {e}", "red"))

def analyze_evil_twin_risk(ssid, bssid_data):
    """Analyze if multiple BSSIDs represent a genuine evil twin threat"""
    if len(bssid_data) < 2:
        return False
    
    # MORE AGGRESSIVE DETECTION - Any duplicate SSID with different BSSID is suspicious
    # unless ALL BSSIDs are whitelisted
    
    if DEBUG_MODE:
        print(colored(f"[DEBUG] Analyzing '{ssid}' with {len(bssid_data)} BSSIDs:", "cyan"))
        for bssid, channel, timestamp in bssid_data:
            is_whitelisted = bssid.lower() in [wb.lower() for wb in WHITELIST_BSSIDS]
            print(colored(f"  - {bssid} (Ch: {channel}) {'[WHITELISTED]' if is_whitelisted else '[NOT WHITELISTED]'}", "cyan"))
    
    # Check if ALL BSSIDs are whitelisted - if so, it's likely legitimate
    all_whitelisted = all(bssid.lower() in [wb.lower() for wb in WHITELIST_BSSIDS] for bssid, _, _ in bssid_data)
    if all_whitelisted:
        if DEBUG_MODE:
            print(colored(f"[DEBUG] All BSSIDs for '{ssid}' are whitelisted - marking as legitimate", "blue"))
        return False
    
    # If we have ANY non-whitelisted BSSID mixed with others, flag as suspicious
    non_whitelisted_count = sum(1 for bssid, _, _ in bssid_data 
                               if bssid.lower() not in [wb.lower() for wb in WHITELIST_BSSIDS])
    
    if non_whitelisted_count >= 1 and len(bssid_data) > 1:
        if DEBUG_MODE:
            print(colored(f"[DEBUG] Found {non_whitelisted_count} non-whitelisted BSSIDs for '{ssid}' - SUSPICIOUS!", "red"))
        return True
    
    # Default to suspicious for multiple BSSIDs (more aggressive)
    return len(bssid_data) >= 2

def packet_handler(pkt):
    if pkt.haslayer(Dot11Beacon):
        try:
            # Handle empty or malformed SSIDs
            ssid_info = pkt[Dot11Elt].info
            if len(ssid_info) == 0:
                ssid = "<Hidden SSID>"
            else:
                ssid = ssid_info.decode('utf-8', errors='ignore')
            
            bssid = pkt[Dot11].addr2
            current_time = time.time()
            
            # Get channel information if available
            channel = None
            if pkt.haslayer(Dot11Elt):
                elt = pkt[Dot11Elt]
                while elt:
                    if elt.ID == 3:  # DS Parameter Set (Channel)
                        channel = ord(elt.info) if len(elt.info) > 0 else None
                        break
                    elt = elt.payload if hasattr(elt, 'payload') and isinstance(elt.payload, Dot11Elt) else None
            
            # Skip empty SSIDs for evil twin detection
            if ssid == "<Hidden SSID>" or ssid.strip() == "":
                return
            
            # Debug: Show all detected beacons
            if DEBUG_MODE:
                is_whitelisted = bssid.lower() in [wb.lower() for wb in WHITELIST_BSSIDS]
                # print(colored(f"[BEACON] '{ssid}' - {bssid} (Ch: {channel}) {'[WHITELISTED]' if is_whitelisted else ''}", "white"))
            
            if ssid not in ap_list:
                ap_list[ssid] = [(bssid, channel, current_time)]
                if bssid.lower() in [wb.lower() for wb in WHITELIST_BSSIDS]:
                    print(colored(f"[+] Whitelisted BSSID detected: '{ssid}' with BSSID {bssid}", "blue"))
                else:
                    print(colored(f"[+] New SSID detected: '{ssid}' with BSSID {bssid}", "green"))
            else:
                # Check if this BSSID is already known for this SSID
                existing_bssids = [entry[0] for entry in ap_list[ssid]]
                if bssid not in existing_bssids:
                    ap_list[ssid].append((bssid, channel, current_time))
                    
                    print(colored(f"[!] DUPLICATE SSID DETECTED: '{ssid}' now has multiple BSSIDs!", "yellow"))
                    
                    # Always show the current BSSID list for this SSID
                    print(colored(f"    Current BSSIDs for '{ssid}':", "yellow"))
                    for i, (b, c, t) in enumerate(ap_list[ssid], 1):
                        is_whitelisted = b.lower() in [wb.lower() for wb in WHITELIST_BSSIDS]
                        status = "[WHITELISTED]" if is_whitelisted else "[Evil-Twin]"
                        print(colored(f"      {i}. {b} (Ch: {c}) {status}", "yellow"))
                    
                    # Analyze if this is a genuine evil twin threat
                    if analyze_evil_twin_risk(ssid, ap_list[ssid]):
                        # Check if the new BSSID is whitelisted
                        if bssid.lower() not in [wb.lower() for wb in WHITELIST_BSSIDS]:
                            print(colored(f"[!!!] EVIL TWIN DETECTED: New BSSID {bssid} (Ch: {channel}) for SSID '{ssid}'", "red"))
                            print(colored(f"[!!!] THIS IS LIKELY A MALICIOUS ACCESS POINT!", "red"))
                            
                            # Find the legitimate (whitelisted) BSSID for comparison
                            legitimate_bssid = None
                            for b, c, t in ap_list[ssid]:
                                if b.lower() in [wb.lower() for wb in WHITELIST_BSSIDS]:
                                    legitimate_bssid = b
                                    break
                            
                            # Send alert to database and Flask server
                            send_evil_twin_alert(ssid, bssid, legitimate_bssid or "Unknown", channel)
                            
                        else:
                            print(colored(f"[+] New whitelisted BSSID detected: '{ssid}' with BSSID {bssid}", "blue"))
                    else:
                        print(colored(f"[~] Multiple BSSIDs for '{ssid}' detected but marked as legitimate", "yellow"))
                    
        except Exception as e:
            print(colored(f"[ERROR] Failed to process packet: {e}", "red"))
            if DEBUG_MODE:
                import traceback
                traceback.print_exc()

print(colored("[*] Starting Evil Twin AP Scanner...", "cyan"))
print(colored("[*] Make sure your interface is in monitor mode: sudo airmon-ng start wlan0", "cyan"))
print(colored(f"[*] Whitelisted BSSIDs: {list(WHITELIST_BSSIDS)}", "blue"))
print(colored(f"[*] Debug mode: {'ON' if DEBUG_MODE else 'OFF'}", "cyan"))
print(colored(f"[*] Flask server: {FLASK_SERVER_URL}", "cyan"))
print(colored("[*] This detector will flag ANY duplicate SSID with different BSSIDs as suspicious", "yellow"))
print(colored("[*] unless ALL BSSIDs for that SSID are whitelisted", "yellow"))

# Test database connection
print(colored("[*] Testing database connection...", "cyan"))
test_conn = get_db_connection()
if test_conn:
    test_conn.close()
    print(colored("[+] Database connection successful", "green"))
else:
    print(colored("[WARNING] Database connection failed - alerts will only be sent to Flask server", "yellow"))

# Test Flask server connection
print(colored("[*] Testing Flask server connection...", "cyan"))
try:
    response = requests.get(f"{FLASK_SERVER_URL}/", timeout=3)
    if response.status_code == 200:
        print(colored("[+] Flask server is accessible", "green"))
    else:
        print(colored(f"[WARNING] Flask server returned status: {response.status_code}", "yellow"))
except Exception as e:
    print(colored(f"[WARNING] Flask server not accessible: {e}", "yellow"))

print(colored(f"[*] Starting scan on interface deauth for 120 seconds...", "green"))

# Add a small delay and interface check
import subprocess
# try:
#     result = subprocess.run(['iwconfig', 'deauth'], capture_output=True, text=True, timeout=5)
#     if 'Mode:Monitor' in result.stdout:
#         print(colored("[+] Interface wlan0mon is in monitor mode - good!", "green"))
#     else:
#         print(colored("[WARNING] Interface wlan0mon may not be in monitor mode!", "yellow"))
# except:
#     print(colored("[WARNING] Could not verify interface status", "yellow"))
try:
    sniff(prn=packet_handler, iface="deauth", timeout=120, store=0)
except Exception as e:
    print(colored(f"[ERROR] Sniffing failed: {e}", "red"))
    print(colored("[*] Make sure wlan0mon interface exists and is in monitor mode", "yellow"))

print(colored(f"[*] Scan completed. Found {len(ap_list)} unique SSIDs", "cyan"))
