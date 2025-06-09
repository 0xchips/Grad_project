#!/usr/bin/env python3
"""
Real-time WiFi monitoring script for Evil Twin and Deauth detection
Integrates with the Flask dashboard API
"""

import sys
import os
import signal
import json
import time
import requests
import threading
from datetime import datetime
import logging
from scapy.all import *
from scapy.layers.dot11 import Dot11, Dot11Beacon, Dot11Deauth, Dot11Elt
from termcolor import colored

# Set up logging
log_file = '/home/kali/latest/dashboard/logs/monitoring.log'
os.makedirs(os.path.dirname(log_file), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

# Configuration
DASHBOARD_URL = "http://127.0.0.1:5053"
DEAUTH_API_ENDPOINT = f"{DASHBOARD_URL}/api/deauth_logs"
EVIL_TWIN_API_ENDPOINT = f"{DASHBOARD_URL}/api/evil_twin_logs"

# Global variables
ap_list = {}
monitoring_active = True
deauth_count = 0
evil_twin_count = 0

# Default whitelist - can be extended via API
WHITELIST_BSSIDS = {
    "dc:8d:8a:b9:13:36", 
    "20:9a:7d:5c:83:a0",
    "cc:d4:2e:88:77:b6"
}

def load_whitelist():
    """Load whitelist from dashboard API if available"""
    global WHITELIST_BSSIDS
    try:
        # In a real implementation, this would fetch from the API
        # For now, we use the default whitelist
        print(colored(f"[*] Using default whitelist: {list(WHITELIST_BSSIDS)}", "blue"))
    except Exception as e:
        print(colored(f"[WARNING] Could not load whitelist from API: {e}", "yellow"))

def send_deauth_log(ssid, bssid, victim_mac, reason="Deauth packet detected"):
    """Send deauth attack log to dashboard"""
    global deauth_count
    try:
        data = {
            "ssid": ssid,
            "bssid": bssid,
            "victim_mac": victim_mac,
            "reason": reason,
            "type": "deauth",
            "timestamp": datetime.now().isoformat()
        }
        
        response = requests.post(DEAUTH_API_ENDPOINT, json=data, timeout=5)
        if response.status_code in [200, 201]:
            deauth_count += 1
            print(colored(f"[+] Deauth log sent to dashboard: {ssid} -> {victim_mac}", "green"))
        else:
            print(colored(f"[WARNING] Failed to send deauth log: {response.status_code}", "yellow"))
            
    except Exception as e:
        print(colored(f"[ERROR] Failed to send deauth log: {e}", "red"))

def send_evil_twin_log(ssid, legitimate_bssid, suspicious_bssid):
    """Send evil twin detection to dashboard"""
    global evil_twin_count
    try:
        data = {
            "ssid": ssid,
            "suspicious_bssid": suspicious_bssid,  # Will be mapped to attacker_bssid
            "legitimate_bssid": "-",  # Set target as "-" per requirements
            "reason": f"Evil Twin detected - Legitimate: {legitimate_bssid}, Suspicious: {suspicious_bssid}",
            "type": "evil-twin",
            "timestamp": datetime.now().isoformat()
        }
        
        response = requests.post(EVIL_TWIN_API_ENDPOINT, json=data, timeout=5)
        if response.status_code in [200, 201]:
            evil_twin_count += 1
            print(colored(f"[+] Evil Twin log sent to dashboard: {ssid} - Suspicious BSSID: {suspicious_bssid}", "green"))
        else:
            print(colored(f"[WARNING] Failed to send evil twin log: {response.status_code}", "yellow"))
            
    except Exception as e:
        print(colored(f"[ERROR] Failed to send evil twin log: {e}", "red"))

def analyze_evil_twin_risk(ssid, bssid_data):
    """Analyze if multiple BSSIDs represent a genuine evil twin threat"""
    if len(bssid_data) < 2:
        return False
    
    # Check if there are any non-whitelisted BSSIDs
    has_non_whitelisted = any(bssid.lower() not in [wb.lower() for wb in WHITELIST_BSSIDS] for bssid, _, _ in bssid_data)
    
    # If there are non-whitelisted BSSIDs mixed with whitelisted ones, it's suspicious
    if has_non_whitelisted and len(bssid_data) > 1:
        return True
    
    # Check if all BSSIDs are whitelisted
    all_whitelisted = all(bssid.lower() in [wb.lower() for wb in WHITELIST_BSSIDS] for bssid, _, _ in bssid_data)
    if all_whitelisted:
        return False
    
    # Check timing - evil twins often appear suddenly
    current_time = time.time()
    recent_additions = sum(1 for _, _, timestamp in bssid_data if current_time - timestamp < 30)
    
    # If multiple BSSIDs appeared recently, higher suspicion
    if recent_additions >= 2:
        return True
        
    return True  # Default to suspicious for multiple BSSIDs

def handle_deauth_packet(pkt):
    """Handle deauthentication packets"""
    try:
        if pkt.haslayer(Dot11Deauth):
            # Extract addresses from deauth frame correctly
            # addr1: receiver (target being deauth'd)  
            # addr2: transmitter (source sending deauth)
            # addr3: BSSID (access point)
            receiver_mac = pkt[Dot11].addr1  # Target/victim
            transmitter_mac = pkt[Dot11].addr2  # Attacker
            bssid_mac = pkt[Dot11].addr3  # Access Point BSSID
            reason = pkt[Dot11Deauth].reason
            
            # Try to find SSID using improved logic
            # Priority: BSSID > receiver > transmitter
            network_ssid = "Unknown"
            network_bssid = bssid_mac
            
            # First try to find SSID using BSSID (most reliable)
            if bssid_mac:
                for ssid, bssid_list in ap_list.items():
                    if any(entry[0] == bssid_mac for entry in bssid_list):
                        network_ssid = ssid
                        network_bssid = bssid_mac
                        break
            
            # If BSSID lookup failed, try receiver address
            if network_ssid == "Unknown":
                for ssid, bssid_list in ap_list.items():
                    if any(entry[0] == receiver_mac for entry in bssid_list):
                        network_ssid = ssid
                        network_bssid = receiver_mac
                        break
            
            # If still unknown, try transmitter address
            if network_ssid == "Unknown":
                for ssid, bssid_list in ap_list.items():
                    if any(entry[0] == transmitter_mac for entry in bssid_list):
                        network_ssid = ssid
                        network_bssid = transmitter_mac
                        break
            
            # If still unknown, use BSSID as fallback
            if network_ssid == "Unknown":
                network_bssid = bssid_mac if bssid_mac else receiver_mac
            
            print(colored(f"[!] DEAUTH DETECTED: {network_ssid} ({network_bssid}) | Transmitter: {transmitter_mac} -> Receiver: {receiver_mac} (Reason: {reason})", "red"))
            send_deauth_log(network_ssid, network_bssid, receiver_mac, f"Deauth reason: {reason}")
            
    except Exception as e:
        print(colored(f"[ERROR] Failed to process deauth packet: {e}", "red"))

def handle_beacon_packet(pkt):
    """Handle beacon packets for evil twin detection"""
    try:
        if pkt.haslayer(Dot11Beacon):
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
                        channel = ord(elt.info)
                        break
                    elt = elt.payload if hasattr(elt, 'payload') and isinstance(elt.payload, Dot11Elt) else None
            
            # Skip empty SSIDs for evil twin detection
            if ssid == "<Hidden SSID>" or ssid.strip() == "":
                return
            
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
                    
                    # Skip evil twin detection if this BSSID is whitelisted
                    if bssid.lower() in [wb.lower() for wb in WHITELIST_BSSIDS]:
                        print(colored(f"[+] Whitelisted BSSID detected: '{ssid}' with BSSID {bssid}", "blue"))
                    else:
                        # Analyze if this is a genuine evil twin threat
                        if analyze_evil_twin_risk(ssid, ap_list[ssid]):
                            if bssid.lower() not in [wb.lower() for wb in WHITELIST_BSSIDS]:
                                print(colored(f"[!] EVIL TWIN DETECTED: New BSSID {bssid} (Ch: {channel}) for SSID '{ssid}'", "red"))
                                
                                # Find the legitimate BSSID (usually the first one or whitelisted one)
                                legitimate_bssid = ap_list[ssid][0][0]  # First detected BSSID
                                for entry in ap_list[ssid]:
                                    if entry[0].lower() in [wb.lower() for wb in WHITELIST_BSSIDS]:
                                        legitimate_bssid = entry[0]
                                        break
                                
                                send_evil_twin_log(ssid, legitimate_bssid, bssid)
                            else:
                                print(colored(f"[+] Whitelisted BSSID detected: '{ssid}' with BSSID {bssid}", "blue"))
                        else:
                            if bssid.lower() in [wb.lower() for wb in WHITELIST_BSSIDS]:
                                print(colored(f"[+] Whitelisted BSSID detected: '{ssid}' with BSSID {bssid}", "blue"))
                            else:
                                print(colored(f"[~] Multiple BSSIDs for '{ssid}' detected but likely legitimate", "yellow"))
                                bssid_list = [f"{entry[0]} (Ch: {entry[1]})" for entry in ap_list[ssid]]
                                print(colored(f"    BSSIDs: {bssid_list}", "yellow"))
                    
    except Exception as e:
        print(colored(f"[ERROR] Failed to process beacon packet: {e}", "red"))

def packet_handler(pkt):
    """Main packet handler for all WiFi packets"""
    if not monitoring_active:
        return
        
    try:
        # Handle different packet types
        if pkt.haslayer(Dot11Deauth):
            handle_deauth_packet(pkt)
        elif pkt.haslayer(Dot11Beacon):
            handle_beacon_packet(pkt)
            
    except Exception as e:
        print(colored(f"[ERROR] Failed to process packet: {e}", "red"))

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global monitoring_active
    print(colored("\n[*] Shutdown signal received, stopping monitoring...", "cyan"))
    monitoring_active = False
    print(colored(f"[*] Session stats - Deauth attacks: {deauth_count}, Evil twins: {evil_twin_count}", "cyan"))
    sys.exit(0)

def status_reporter():
    """Report monitoring status periodically"""
    while monitoring_active:
        time.sleep(30)  # Report every 30 seconds
        if monitoring_active:
            print(colored(f"[*] Monitoring active - Networks: {len(ap_list)}, Deauth: {deauth_count}, Evil twins: {evil_twin_count}", "cyan"))

def main():
    global monitoring_active
    
    logging.info("Starting Real-time WiFi Monitor...")
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check command line arguments
    interface = "wlan0mon"
    if len(sys.argv) > 1:
        interface = sys.argv[1]
    
    logging.info(f"Using interface: {interface}")
    print(colored("[*] Starting Real-time WiFi Monitor...", "cyan"))
    print(colored(f"[*] Interface: {interface}", "cyan"))
    print(colored(f"[*] Dashboard: {DASHBOARD_URL}", "cyan"))
    
    # Load whitelist
    load_whitelist()
    
    # Start status reporter thread
    status_thread = threading.Thread(target=status_reporter, daemon=True)
    status_thread.start()
    
    try:
        logging.info("Starting packet capture...")
        print(colored("[*] Starting packet capture...", "green"))
        print(colored("[*] Press Ctrl+C to stop monitoring", "yellow"))
        
        # Start packet sniffing
        sniff(prn=packet_handler, iface=interface, store=0)
        
    except PermissionError:
        error_msg = "Permission denied. Run as root: sudo python3 real_time_monitor.py"
        logging.error(error_msg)
        print(colored(f"[ERROR] {error_msg}", "red"))
        sys.exit(1)
    except OSError as e:
        error_msg = f"Interface error: {e}"
        logging.error(error_msg)
        print(colored(f"[ERROR] Interface error: {e}", "red"))
        print(colored(f"[*] Make sure {interface} interface exists and is in monitor mode", "yellow"))
        print(colored(f"[*] Try: sudo airmon-ng start wlan0", "yellow"))
        sys.exit(1)
    except Exception as e:
        error_msg = f"Monitoring failed: {e}"
        logging.error(error_msg)
        print(colored(f"[ERROR] Monitoring failed: {e}", "red"))
        sys.exit(1)

if __name__ == "__main__":
    main()
