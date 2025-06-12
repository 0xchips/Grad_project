#!/usr/bin/env python3

print("=== Testing Deauth Detection Fix ===")

# Simulate the SSID mapping like in the detectors
ssid_map = {
    "aa:bb:cc:dd:ee:01": "TestNetwork1",
    "aa:bb:cc:dd:ee:02": "TestNetwork2", 
    "aa:bb:cc:dd:ee:03": "TestAP",
}

# Test case: AP to Client Deauth
receiver_mac = "aa:bb:cc:dd:ee:99"  # Client (receiver)
transmitter_mac = "aa:bb:cc:dd:ee:01"  # AP (transmitter) 
bssid_mac = "aa:bb:cc:dd:ee:01"  # BSSID (same as AP)

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

print(f"Transmitter: {transmitter_mac} ({transmitter_ssid})")
print(f"Receiver:    {receiver_mac} ({receiver_ssid})")
print(f"Network:     {network_bssid} ({network_ssid})")

print("✓ Test completed - This should show actual SSIDs instead of 'Unknown Unknown Unknown'")
