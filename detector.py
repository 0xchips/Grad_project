from scapy.all import *
from datetime import datetime, timedelta
import uuid
import MySQLdb
import time

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
    'host': 'localhost',
    'user': 'dashboard',
    'passwd': 'securepass',
    'db': 'security_dashboard',
}

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
        
        conn = MySQLdb.connect(**db_config)
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
    except Exception as e:
        print(f"[!] Database error: {str(e)}")
        return False

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

        # Extract addresses from deauth frame
        # addr1: receiver (target being deauth'd)  
        # addr2: transmitter (source sending deauth)
        # addr3: BSSID (access point)
        receiver_mac = pkt[Dot11].addr1  # Target/victim
        transmitter_mac = pkt[Dot11].addr2  # Attacker
        bssid_mac = pkt[Dot11].addr3  # Access Point BSSID
        
        # Try to get SSIDs - prioritize BSSID for network identification
        receiver_ssid = ssid_map.get(receiver_mac, "Unknown")
        transmitter_ssid = ssid_map.get(transmitter_mac, "Unknown")
        bssid_ssid = ssid_map.get(bssid_mac, "Unknown")
        
        # Use BSSID SSID if available, fallback to other addresses
        if bssid_ssid != "Unknown":
            network_ssid = bssid_ssid
            network_bssid = bssid_mac
        elif receiver_ssid != "Unknown":
            network_ssid = receiver_ssid
            network_bssid = receiver_mac
        elif transmitter_ssid != "Unknown":
            network_ssid = transmitter_ssid
            network_bssid = transmitter_mac
        else:
            network_ssid = "Unknown"
            network_bssid = bssid_mac if bssid_mac else receiver_mac

        print(f"[!] Deauth detected at {now.strftime('%H:%M:%S')}")
        print(f"    → Transmitter: {transmitter_mac} ({transmitter_ssid})")
        print(f"    → Receiver:    {receiver_mac} ({receiver_ssid})")
        print(f"    → Network:     {network_bssid} ({network_ssid})")
        print(f"    → Total in window: {len(deauth_times)}\n")

        # Always log every deauth packet (if above threshold)
        if len(deauth_times) >= threshold:
            print("\n[!!!] ALERT: Possible deauthentication attack detected!\n")

            # Prepare the log entry as a dictionary
            log_entry = {
                "timestamp": now.strftime('%Y-%m-%d %H:%M:%S'),
                "alert_type": "Deauth Attack",
                "count": len(deauth_times),
                "attacker_bssid": transmitter_mac,
                "attacker_ssid": transmitter_ssid,
                "destination_bssid": network_bssid,
                "destination_ssid": network_ssid
            }

            # Save attack data to MySQL database
            save_to_database(log_entry)
        
        # Even if we haven't hit threshold yet, log single packets sometimes
        # This helps make threat visualization more interesting
        elif len(deauth_times) > 1 and len(deauth_times) % 5 == 0:
            # Log every 5th packet even before threshold
            log_entry = {
                "timestamp": now.strftime('%Y-%m-%d %H:%M:%S'),
                "alert_type": "Deauth Packet",  # Different name to distinguish from attack
                "count": len(deauth_times),
                "attacker_bssid": transmitter_mac,
                "attacker_ssid": transmitter_ssid,
                "destination_bssid": network_bssid,
                "destination_ssid": network_ssid
            }
            save_to_database(log_entry)


print(f"[*] Sniffing on {iface}... Looking for deauth frames and SSIDs.")
print(f"[*] Attacks will be logged directly to MySQL database in real-time.")
print(f"[*] Attack threshold is {threshold} deauth packets within {time_window} seconds.")
sniff(iface=iface, prn=packet_handler, store=0)