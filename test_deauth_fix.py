#!/usr/bin/env python3
"""
Test script to verify deauth detection fixes
This script simulates deauth packet processing to test our SSID mapping improvements
"""

from scapy.all import *
from datetime import datetime
import sys

# Simulate the SSID mapping like in the detectors
ssid_map = {
    "aa:bb:cc:dd:ee:01": "TestNetwork1",
    "aa:bb:cc:dd:ee:02": "TestNetwork2", 
    "aa:bb:cc:dd:ee:03": "TestAP",
    "ff:ff:ff:ff:ff:ff": "BroadcastSSID"
}

def test_deauth_processing():
    """Test the improved deauth packet processing logic"""
    print("=== Testing Deauth Detection Fix ===\n")
    
    # Simulate different deauth scenarios
    test_cases = [
        {
            "name": "AP to Client Deauth",
            "addr1": "aa:bb:cc:dd:ee:99",  # Client (receiver)
            "addr2": "aa:bb:cc:dd:ee:01",  # AP (transmitter) 
            "addr3": "aa:bb:cc:dd:ee:01",  # BSSID (same as AP)
        },
        {
            "name": "Client to AP Deauth", 
            "addr1": "aa:bb:cc:dd:ee:01",  # AP (receiver)
            "addr2": "aa:bb:cc:dd:ee:99",  # Client (transmitter)
            "addr3": "aa:bb:cc:dd:ee:01",  # BSSID (AP)
        },
        {
            "name": "Unknown Network Deauth",
            "addr1": "xx:xx:xx:xx:xx:01",  # Unknown receiver
            "addr2": "xx:xx:xx:xx:xx:02",  # Unknown transmitter  
            "addr3": "xx:xx:xx:xx:xx:03",  # Unknown BSSID
        },
        {
            "name": "Mixed Known/Unknown Deauth",
            "addr1": "aa:bb:cc:dd:ee:01",  # Known AP as receiver
            "addr2": "xx:xx:xx:xx:xx:99",  # Unknown client as transmitter
            "addr3": "aa:bb:cc:dd:ee:01",  # Known BSSID
        }
    ]
    
    for test_case in test_cases:
        print(f"--- {test_case['name']} ---")
        
        # Extract addresses (simulating packet processing)
        receiver_mac = test_case['addr1']
        transmitter_mac = test_case['addr2'] 
        bssid_mac = test_case['addr3']
        
        # Get SSID information using our improved logic
        receiver_ssid = ssid_map.get(receiver_mac, "Unknown")
        transmitter_ssid = ssid_map.get(transmitter_mac, "Unknown")
        bssid_ssid = ssid_map.get(bssid_mac, "Unknown") if bssid_mac else "Unknown"
        
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
            
        # Display results
        print(f"  Transmitter: {transmitter_mac} ({transmitter_ssid})")
        print(f"  Receiver:    {receiver_mac} ({receiver_ssid})")
        print(f"  Network:     {network_bssid} ({network_ssid})")
        
        # Show what would be logged
        log_entry = {
            "attacker_bssid": transmitter_mac,
            "attacker_ssid": transmitter_ssid,
            "destination_bssid": network_bssid,
            "destination_ssid": network_ssid
        }
        
        print(f"  Would log: Attacker={log_entry['attacker_bssid']} ({log_entry['attacker_ssid']}) -> Target={log_entry['destination_bssid']} ({log_entry['destination_ssid']})")
        print()

if __name__ == "__main__":
    test_deauth_processing()
    print("Test completed. The fixes should now show proper BSSID/SSID information instead of 'Unknown Unknown Unknown'")
