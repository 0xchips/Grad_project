#!/usr/bin/env python3
"""
Demonstration of BSSID to SSID mapping functionality
This shows how the Flask app processes Kismet data to create the "BSSID (SSID)" format
"""

import requests
import json

def demonstrate_bssid_mapping():
    """Demonstrate the BSSID mapping process"""
    try:
        print("🔍 BSSID to SSID Mapping Demonstration")
        print("=" * 60)
        
        # Get devices from Kismet
        print("📡 Fetching devices from Kismet...")
        response = requests.get(
            'http://localhost:2501/devices/last-time/0/devices.json',
            auth=('kali', 'kali'),
            timeout=5
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to get Kismet data: HTTP {response.status_code}")
            return
        
        devices = response.json()
        print(f"✅ Retrieved {len(devices)} devices from Kismet")
        
        # Step 1: Build BSSID to SSID mapping (First Pass)
        print("\n📋 Step 1: Building BSSID to SSID mapping...")
        bssid_to_ssid = {}
        access_points = []
        
        for device in devices:
            device_type = device.get('kismet.device.base.type', '')
            if 'AP' in device_type or 'Access Point' in device_type:
                bssid = device.get('kismet.device.base.macaddr', '')
                ssid = 'Unknown SSID'
                
                # Try to extract SSID
                dot11_device = device.get('dot11.device', {})
                if dot11_device:
                    # Try advertised SSID map
                    advertised_ssid_map = dot11_device.get('dot11.device.advertised_ssid_map', {})
                    if isinstance(advertised_ssid_map, dict):
                        for ssid_key, ssid_data in advertised_ssid_map.items():
                            if isinstance(ssid_data, dict):
                                extracted_ssid = ssid_data.get('dot11.advertisedssid.ssid', '')
                                if extracted_ssid:
                                    ssid = extracted_ssid
                                    break
                
                if bssid and ssid:
                    bssid_to_ssid[bssid] = ssid
                    access_points.append({
                        'bssid': bssid,
                        'ssid': ssid,
                        'name': device.get('kismet.device.base.name', 'Unknown')
                    })
        
        print(f"✅ Found {len(access_points)} Access Points:")
        for ap in access_points[:5]:  # Show first 5
            print(f"   📡 {ap['bssid']} → {ap['ssid']} ({ap['name']})")
        
        # Step 2: Process client devices (Second Pass)
        print(f"\n📋 Step 2: Processing client devices...")
        client_devices = []
        
        for device in devices:
            device_type = device.get('kismet.device.base.type', '')
            if 'Client' in device_type:
                mac = device.get('kismet.device.base.macaddr', '')
                name = device.get('kismet.device.base.name', '') or f"Device_{mac[-8:]}"
                
                # Try to find connected AP
                connected_ap = 'N/A'
                connected_ssid = 'N/A'
                
                dot11_device = device.get('dot11.device', {})
                if dot11_device:
                    # Look for associated AP
                    associated_ap = dot11_device.get('dot11.device.associated_client_map', {})
                    if associated_ap and isinstance(associated_ap, dict):
                        for ap_mac in associated_ap.keys():
                            ssid_name = bssid_to_ssid.get(ap_mac, 'Unknown SSID')
                            connected_ap = f"{ap_mac} ({ssid_name})"
                            connected_ssid = ssid_name
                            break
                    
                    # Alternative: check last BSSID
                    if connected_ap == 'N/A':
                        last_bssid = dot11_device.get('dot11.device.last_bssid', None)
                        if last_bssid and last_bssid != mac:
                            ssid_name = bssid_to_ssid.get(last_bssid, 'Unknown SSID')
                            connected_ap = f"{last_bssid} ({ssid_name})"
                            connected_ssid = ssid_name
                
                client_devices.append({
                    'mac': mac,
                    'name': name,
                    'connected_ap': connected_ap,
                    'connected_ssid': connected_ssid
                })
        
        print(f"✅ Found {len(client_devices)} Client Devices:")
        
        # Show connected clients with BSSID (SSID) format
        connected_clients = [c for c in client_devices if c['connected_ap'] != 'N/A']
        
        if connected_clients:
            print(f"\n🔗 Connected Clients (showing BSSID (SSID) format):")
            for client in connected_clients[:5]:  # Show first 5
                print(f"   📱 {client['name']} ({client['mac']})")
                print(f"      → Connected to: {client['connected_ap']}")
                print(f"      → SSID only: {client['connected_ssid']}")
                print()
        else:
            print("⚠️  No connected clients found (they may not have association data yet)")
        
        # Show all clients for completeness
        print(f"\n📱 All Client Devices:")
        for client in client_devices[:10]:  # Show first 10
            status = "🔗 Connected" if client['connected_ap'] != 'N/A' else "📊 Detected"
            print(f"   {status}: {client['name']} ({client['mac']})")
        
        print(f"\n✅ BSSID Mapping Demonstration Complete!")
        print(f"📊 Summary:")
        print(f"   • Access Points: {len(access_points)}")
        print(f"   • Client Devices: {len(client_devices)}")
        print(f"   • Connected Clients: {len(connected_clients)}")
        print(f"   • BSSID Mappings: {len(bssid_to_ssid)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    demonstrate_bssid_mapping()
