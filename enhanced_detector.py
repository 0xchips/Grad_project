#!/usr/bin/env python3
"""
Enhanced Wireless Attack Detector
Integrates deauth and evil-twin detection capabilities with proper attack classification
"""

from scapy.all import *
from datetime import datetime, timedelta
import uuid
import requests
import time
import json
import sys
from termcolor import colored
import threading
import signal

# Configuration
INTERFACE = "wlan1"
DEAUTH_THRESHOLD = 5
TIME_WINDOW = 5
DASHBOARD_URL = "http://localhost:5053"

# API Endpoints
DEAUTH_API_ENDPOINT = f"{DASHBOARD_URL}/api/deauth_logs"
EVIL_TWIN_API_ENDPOINT = f"{DASHBOARD_URL}/api/evil_twin_logs"

# Whitelisted BSSIDs (known legitimate access points)
WHITELIST_BSSIDS = [
    # Add known legitimate BSSIDs here
    # "aa:bb:cc:dd:ee:ff",
]

# Global tracking variables
deauth_times = []
last_saved_attack = None
ssid_map = {}  # BSSID -> SSID mapping
ap_list = {}   # SSID -> [(BSSID, channel, timestamp), ...]
evil_twin_count = 0
deauth_count = 0
monitoring_active = True

def signal_handler(signum, frame):
    """Handle graceful shutdown"""
    global monitoring_active
    print(colored("\n[!] Received shutdown signal. Stopping detector...", "yellow"))
    monitoring_active = False
    print(colored(f"[*] Session Summary:", "cyan"))
    print(colored(f"    Deauth attacks detected: {deauth_count}", "cyan"))
    print(colored(f"    Evil twin attacks detected: {evil_twin_count}", "cyan"))
    print(colored(f"    Total networks monitored: {len(ap_list)}", "cyan"))
    sys.exit(0)

def send_deauth_log(attack_data):
    """Send deauth attack data to dashboard API"""
    global deauth_count
    try:
        # Format data for deauth API
        api_data = {
            "timestamp": attack_data["timestamp"],
            "alert_type": attack_data["alert_type"],
            "attacker_bssid": attack_data["attacker_bssid"],
            "attacker_ssid": attack_data["attacker_ssid"],
            "destination_bssid": attack_data["destination_bssid"],
            "destination_ssid": attack_data["destination_ssid"],
            "attack_count": attack_data["count"]
        }
        
        response = requests.post(DEAUTH_API_ENDPOINT, json=api_data, timeout=5)
        if response.status_code in [200, 201]:
            deauth_count += 1
            print(colored(f"[+] Deauth attack logged to dashboard: {attack_data['attacker_bssid']} -> {attack_data['destination_bssid']}", "green"))
            return True
        else:
            print(colored(f"[WARNING] Failed to send deauth log: HTTP {response.status_code}", "yellow"))
            return False
            
    except Exception as e:
        print(colored(f"[ERROR] Failed to send deauth log: {e}", "red"))
        return False

def send_evil_twin_log(ssid, legitimate_bssid, suspicious_bssid):
    """Send evil twin detection to dashboard API"""
    global evil_twin_count
    try:
        data = {
            "ssid": ssid,
            "suspicious_bssid": suspicious_bssid,
            "legitimate_bssid": legitimate_bssid,
            "reason": f"Evil Twin detected - Legitimate: {legitimate_bssid}, Suspicious: {suspicious_bssid}",
            "type": "evil-twin",
            "timestamp": datetime.now().isoformat()
        }
        
        response = requests.post(EVIL_TWIN_API_ENDPOINT, json=data, timeout=5)
        if response.status_code in [200, 201]:
            evil_twin_count += 1
            print(colored(f"[+] Evil Twin logged to dashboard: {ssid} - Suspicious BSSID: {suspicious_bssid}", "green"))
            return True
        else:
            print(colored(f"[WARNING] Failed to send evil twin log: HTTP {response.status_code}", "yellow"))
            return False
            
    except Exception as e:
        print(colored(f"[ERROR] Failed to send evil twin log: {e}", "red"))
        return False

def analyze_evil_twin_risk(ssid, bssid_data):
    """Analyze if multiple BSSIDs represent a genuine evil twin threat"""
    if len(bssid_data) < 2:
        return False
    
    # Check if there are any non-whitelisted BSSIDs
    has_non_whitelisted = any(bssid.lower() not in [wb.lower() for wb in WHITELIST_BSSIDS] 
                             for bssid, _, _ in bssid_data)
    
    # If there are non-whitelisted BSSIDs mixed with whitelisted ones, it's suspicious
    if has_non_whitelisted and len(bssid_data) > 1:
        return True
    
    # Check if all BSSIDs are whitelisted
    all_whitelisted = all(bssid.lower() in [wb.lower() for wb in WHITELIST_BSSIDS] 
                         for bssid, _, _ in bssid_data)
    if all_whitelisted:
        return False
    
    # Additional heuristics for evil twin detection
    # Check for significant signal strength differences
    signal_strengths = [strength for _, _, strength in bssid_data if strength is not None]
    if len(signal_strengths) >= 2:
        signal_diff = max(signal_strengths) - min(signal_strengths)
        if signal_diff > 30:  # More than 30dB difference might indicate proximity attack
            return True
    
    # If we have multiple non-whitelisted BSSIDs, it's likely an attack
    non_whitelisted_count = sum(1 for bssid, _, _ in bssid_data 
                               if bssid.lower() not in [wb.lower() for wb in WHITELIST_BSSIDS])
    return non_whitelisted_count >= 2

def is_duplicate_attack(attack_data):
    """Check if this is a duplicate of the last attack to avoid spam"""
    global last_saved_attack
    
    if not last_saved_attack:
        return False
    
    try:
        last_time = datetime.strptime(last_saved_attack["timestamp"], '%Y-%m-%d %H:%M:%S')
        current_time = datetime.strptime(attack_data["timestamp"], '%Y-%m-%d %H:%M:%S')
        time_diff = (current_time - last_time).total_seconds()
        
        # Check for duplicate within 2 seconds with same source/destination
        if (time_diff < 2 and 
            attack_data["attacker_bssid"] == last_saved_attack["attacker_bssid"] and 
            attack_data["destination_bssid"] == last_saved_attack["destination_bssid"]):
            return True
    except:
        pass
    
    return False

def process_beacon_probe(pkt):
    """Process beacon and probe response frames for evil twin detection"""
    try:
        if not (pkt.haslayer(Dot11Beacon) or pkt.haslayer(Dot11ProbeResp)):
            return
        
        bssid = pkt[Dot11].addr2
        if not bssid:
            return
        
        # Extract SSID
        ssid = None
        if pkt.haslayer(Dot11Elt):
            ssid = pkt[Dot11Elt].info.decode(errors="ignore")
        
        if not ssid or ssid.strip() == "" or ssid == "<Hidden SSID>":
            return
        
        # Update SSID mapping
        ssid_map[bssid] = ssid
        
        # Extract channel and signal strength
        channel = None
        signal_strength = None
        
        if hasattr(pkt, 'dBm_AntSignal'):
            signal_strength = pkt.dBm_AntSignal
        
        # Try to extract channel from RadioTap
        if pkt.haslayer(RadioTap):
            if hasattr(pkt[RadioTap], 'Channel'):
                channel = pkt[RadioTap].Channel
        
        current_time = datetime.now()
        
        # Track access points
        if ssid not in ap_list:
            ap_list[ssid] = [(bssid, channel, current_time)]
            if bssid.lower() in [wb.lower() for wb in WHITELIST_BSSIDS]:
                print(colored(f"[+] Whitelisted AP: '{ssid}' ({bssid})", "blue"))
            else:
                print(colored(f"[+] New AP: '{ssid}' ({bssid})", "green"))
        else:
            # Check if this BSSID is already known for this SSID
            existing_bssids = [entry[0] for entry in ap_list[ssid]]
            if bssid not in existing_bssids:
                ap_list[ssid].append((bssid, channel, current_time))
                
                # Skip evil twin detection if this BSSID is whitelisted
                if bssid.lower() in [wb.lower() for wb in WHITELIST_BSSIDS]:
                    print(colored(f"[+] Whitelisted AP: '{ssid}' ({bssid})", "blue"))
                else:
                    # Analyze for evil twin threat
                    if analyze_evil_twin_risk(ssid, ap_list[ssid]):
                        print(colored(f"[!] EVIL TWIN DETECTED: '{ssid}' - Suspicious BSSID: {bssid}", "red"))
                        
                        # Find legitimate BSSID (prefer whitelisted, otherwise first detected)
                        legitimate_bssid = ap_list[ssid][0][0]
                        for entry in ap_list[ssid]:
                            if entry[0].lower() in [wb.lower() for wb in WHITELIST_BSSIDS]:
                                legitimate_bssid = entry[0]
                                break
                        
                        # Send evil twin alert
                        send_evil_twin_log(ssid, legitimate_bssid, bssid)
                    else:
                        print(colored(f"[~] Multiple APs for '{ssid}' (likely legitimate)", "yellow"))
                        
    except Exception as e:
        print(colored(f"[ERROR] Error processing beacon/probe: {e}", "red"))

def process_deauth(pkt):
    """Process deauthentication frames for attack detection"""
    global deauth_times, last_saved_attack
    
    try:
        if not pkt.haslayer(Dot11Deauth):
            return
        
        now = datetime.now()
        deauth_times.append(now)
        
        # Clean up old timestamps outside time window
        deauth_times = [t for t in deauth_times if now - t < timedelta(seconds=TIME_WINDOW)]
        
        # Extract MAC addresses
        src_mac = pkt[Dot11].addr1  # Attacker BSSID  
        dst_mac = pkt[Dot11].addr2  # Target BSSID
        
        if not src_mac or not dst_mac:
            return
        
        # Get SSID information
        attacker_ssid = ssid_map.get(src_mac, "Unknown")
        dest_ssid = ssid_map.get(dst_mac, "Unknown")
        
        print(colored(f"[!] Deauth: {src_mac} ({attacker_ssid}) -> {dst_mac} ({dest_ssid}) [Window: {len(deauth_times)}]", "yellow"))
        
        # Check if threshold reached for attack classification
        if len(deauth_times) >= DEAUTH_THRESHOLD:
            print(colored(f"[!!!] DEAUTH ATTACK DETECTED! Threshold reached: {len(deauth_times)} packets", "red"))
            
            # Prepare attack data
            attack_data = {
                "timestamp": now.strftime('%Y-%m-%d %H:%M:%S'),
                "alert_type": "Deauth Attack",
                "count": len(deauth_times),
                "attacker_bssid": src_mac,
                "attacker_ssid": attacker_ssid,
                "destination_bssid": dst_mac,
                "destination_ssid": dest_ssid
            }
            
            # Check for duplicates and send
            if not is_duplicate_attack(attack_data):
                if send_deauth_log(attack_data):
                    last_saved_attack = attack_data
        
        # Log individual packets for analysis (every 5th packet before threshold)
        elif len(deauth_times) > 1 and len(deauth_times) % 5 == 0:
            attack_data = {
                "timestamp": now.strftime('%Y-%m-%d %H:%M:%S'),
                "alert_type": "Deauth Packet",
                "count": len(deauth_times),
                "attacker_bssid": src_mac,
                "attacker_ssid": attacker_ssid,
                "destination_bssid": dst_mac,
                "destination_ssid": dest_ssid
            }
            
            if not is_duplicate_attack(attack_data):
                if send_deauth_log(attack_data):
                    last_saved_attack = attack_data
                    
    except Exception as e:
        print(colored(f"[ERROR] Error processing deauth: {e}", "red"))

def packet_handler(pkt):
    """Unified packet handler for both deauth and evil twin detection"""
    if not monitoring_active:
        return
        
    try:
        # Process beacon/probe frames for evil twin detection
        if pkt.haslayer(Dot11Beacon) or pkt.haslayer(Dot11ProbeResp):
            process_beacon_probe(pkt)
        
        # Process deauth frames for deauth attack detection
        elif pkt.haslayer(Dot11Deauth):
            process_deauth(pkt)
            
    except Exception as e:
        print(colored(f"[ERROR] Packet processing error: {e}", "red"))

def status_monitor():
    """Background thread to show monitoring status"""
    while monitoring_active:
        time.sleep(30)  # Update every 30 seconds
        if monitoring_active:
            print(colored(f"[*] Status - Networks: {len(ap_list)}, Deauth: {deauth_count}, Evil twins: {evil_twin_count}", "cyan"))

def main():
    """Main detector function"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print(colored("="*70, "cyan"))
    print(colored("🛡️  Enhanced Wireless Attack Detector", "cyan"))
    print(colored("="*70, "cyan"))
    print(colored(f"Interface: {INTERFACE}", "white"))
    print(colored(f"Deauth Threshold: {DEAUTH_THRESHOLD} packets in {TIME_WINDOW}s", "white"))
    print(colored(f"Dashboard: {DASHBOARD_URL}", "white"))
    print(colored(f"Whitelist: {len(WHITELIST_BSSIDS)} BSSIDs", "white"))
    print(colored("="*70, "cyan"))
    print(colored("Monitoring for:", "white"))
    print(colored("  • Deauthentication attacks", "yellow"))
    print(colored("  • Evil twin access points", "yellow"))
    print(colored("="*70, "cyan"))
    
    # Start status monitoring thread
    status_thread = threading.Thread(target=status_monitor, daemon=True)
    status_thread.start()
    
    try:
        # Start packet capture
        print(colored(f"[*] Starting packet capture on {INTERFACE}...", "green"))
        sniff(iface=INTERFACE, prn=packet_handler, store=0)
        
    except PermissionError:
        print(colored("[ERROR] Permission denied. Run as root or with CAP_NET_RAW capability.", "red"))
        sys.exit(1)
    except Exception as e:
        print(colored(f"[ERROR] Failed to start packet capture: {e}", "red"))
        sys.exit(1)

if __name__ == "__main__":
    main()
