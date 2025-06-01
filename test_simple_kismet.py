#!/usr/bin/env python3

"""
Simple test script to verify Kismet API access directly
"""

import requests
import json

def test_kismet_direct():
    """Test direct Kismet API access"""
    try:
        print("Testing direct Kismet API access...")
        
        # Test system status
        print("\n1. Testing system status:")
        response = requests.get(
            'http://localhost:2501/system/status.json',
            auth=('kali', 'kali'),
            timeout=10
        )
        print(f"Status response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Kismet version: {data.get('kismet.system.version', 'Unknown')}")
            print(f"Uptime: {data.get('kismet.system.uptime', 0)} seconds")
        
        # Test device list (small sample)
        print("\n2. Testing device list:")
        response = requests.get(
            'http://localhost:2501/devices/last-time/0/devices.json',
            auth=('kali', 'kali'),
            timeout=10
        )
        print(f"Devices response: {response.status_code}")
        if response.status_code == 200:
            devices_data = response.json()
            print(f"Found {len(devices_data)} devices")
            
            # Show first few devices
            for i, device in enumerate(devices_data[:3]):
                mac = device.get('kismet.device.base.macaddr', 'Unknown')
                device_type = device.get('kismet.device.base.type', 'Unknown')
                name = device.get('kismet.device.base.name', 'Unknown')
                print(f"  Device {i+1}: {mac} - {device_type} - {name}")
                
                # For access points, try to get SSID
                if 'AP' in device_type:
                    dot11_device = device.get('dot11.device', {})
                    if dot11_device:
                        advertised_ssid_map = dot11_device.get('dot11.device.advertised_ssid_map', {})
                        if advertised_ssid_map:
                            if isinstance(advertised_ssid_map, list) and len(advertised_ssid_map) > 0:
                                ssid = advertised_ssid_map[0].get('dot11.advertisedssid.ssid', 'Unknown')
                                print(f"    SSID: {ssid}")
                            elif isinstance(advertised_ssid_map, dict):
                                for ssid_data in advertised_ssid_map.values():
                                    if isinstance(ssid_data, dict):
                                        ssid = ssid_data.get('dot11.advertisedssid.ssid', 'Unknown')
                                        print(f"    SSID: {ssid}")
                                        break
        
        # Test BSSID mapping concept
        print("\n3. Testing BSSID to SSID mapping:")
        bssid_to_ssid = {}
        client_devices = []
        
        if response.status_code == 200:
            # First pass: collect access points
            for device in devices_data:
                device_type = device.get('kismet.device.base.type', 'Unknown')
                if 'AP' in device_type:
                    bssid = device.get('kismet.device.base.macaddr', '')
                    dot11_device = device.get('dot11.device', {})
                    if dot11_device:
                        advertised_ssid_map = dot11_device.get('dot11.device.advertised_ssid_map', {})
                        if advertised_ssid_map:
                            if isinstance(advertised_ssid_map, list) and len(advertised_ssid_map) > 0:
                                ssid = advertised_ssid_map[0].get('dot11.advertisedssid.ssid', '')
                                if ssid and bssid:
                                    bssid_to_ssid[bssid] = ssid
                            elif isinstance(advertised_ssid_map, dict):
                                for ssid_data in advertised_ssid_map.values():
                                    if isinstance(ssid_data, dict):
                                        ssid = ssid_data.get('dot11.advertisedssid.ssid', '')
                                        if ssid and bssid:
                                            bssid_to_ssid[bssid] = ssid
                                            break
            
            print(f"Found {len(bssid_to_ssid)} access points with SSIDs:")
            for bssid, ssid in list(bssid_to_ssid.items())[:5]:
                print(f"  {bssid} -> {ssid}")
            
            # Second pass: find clients with connected APs
            for device in devices_data:
                device_type = device.get('kismet.device.base.type', 'Unknown')
                if 'Client' in device_type:
                    mac = device.get('kismet.device.base.macaddr', '')
                    dot11_device = device.get('dot11.device', {})
                    if dot11_device:
                        last_bssid = dot11_device.get('dot11.device.last_bssid', '')
                        if last_bssid and last_bssid in bssid_to_ssid:
                            connected_ap = f"{last_bssid} ({bssid_to_ssid[last_bssid]})"
                            client_devices.append({
                                'mac': mac,
                                'connected_ap': connected_ap
                            })
            
            print(f"\nFound {len(client_devices)} clients with known connected APs:")
            for client in client_devices[:5]:
                print(f"  {client['mac']} -> {client['connected_ap']}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_kismet_direct()
