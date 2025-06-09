from scapy.all import *
from termcolor import colored
import time

ap_list = {}
WHITELIST_BSSIDS = {
    "dc:8d:8a:b9:13:36", 
    "20:9a:7d:5c:83:a0",
    "cc:d4:2e:88:77:b6"
    
    
}

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
            print(colored(f"[ERROR] Failed to process packet: {e}", "red"))

print(colored("[*] Starting Evil Twin AP Scanner...", "cyan"))
print(colored("[*] Make sure your interface is in monitor mode: sudo airmon-ng start wlan0", "cyan"))
print(colored(f"[*] Whitelisted BSSIDs: {list(WHITELIST_BSSIDS)}", "blue"))
try:
    sniff(prn=packet_handler, iface="wlan0mon", timeout=120, store=0)
except Exception as e:
    print(colored(f"[ERROR] Sniffing failed: {e}", "red"))
    print(colored("[*] Make sure wlan0mon interface exists and is in monitor mode", "yellow"))

print(colored(f"[*] Scan completed. Found {len(ap_list)} unique SSIDs", "cyan"))
