from scapy.all import *
from datetime import datetime, timedelta
import json
import os

# Configuration
iface = "wlan1"
threshold = 10
time_window = 10
deauth_times = []

# Dictionary: BSSID (MAC) → SSID
ssid_map = {}

# Log file setup (JSON format)
log_file = "deauth_log.json"

# Initialize or load existing log file
def load_logs():
    if os.path.exists(log_file):
        try:
            with open(log_file, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            # If file exists but is not valid JSON, initialize with empty list
            return []
    else:
        return []

def save_logs(logs):
    with open(log_file, "w") as f:
        json.dump(logs, f, indent=2)

def packet_handler(pkt):
    global deauth_times, ssid_map

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

            # Load existing logs
            logs = load_logs()
            
            # Append new log entry
            logs.append(log_entry)
            
            # Save all logs back to file
            save_logs(logs)


# Initialize the log file if it doesn't exist
if not os.path.exists(log_file):
    save_logs([])

print(f"[*] Sniffing on {iface}... Looking for deauth frames and SSIDs.")
sniff(iface=iface, prn=packet_handler, store=0)