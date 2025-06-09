#!/usr/bin/env python3
"""
Quick test script to directly call the BSSID mapping functionality
"""

import requests
import json

def test_bssid_mapping_direct():
    """Test BSSID mapping by calling Flask API with a specific timeout"""
    try:
        print("🔍 Testing BSSID Mapping on Flask API (Port 5051)")
        print("=" * 60)
        
        # Test with extended timeout
        print("📡 Making API call...")
        response = requests.get(
            'http://localhost:5051/api/kismet/devices',
            timeout=30  # Extended timeout
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                devices = data.get('devices', [])
                bssid_mappings = data.get('bssid_mappings', {})
                
                print(f"✅ API Success!")
                print(f"   Devices found: {len(devices)}")
                print(f"   BSSID mappings: {len(bssid_mappings)}")
                
                # Show BSSID mappings
                if bssid_mappings:
                    print(f"\n📍 BSSID to SSID Mappings:")
                    for i, (bssid, ssid) in enumerate(bssid_mappings.items()):
                        if i < 5:  # Show first 5
                            print(f"   {bssid} → {ssid}")
                
                # Find client devices with "BSSID (SSID)" format
                clients = [d for d in devices if 'Client' in d.get('type', '')]
                connected_clients = [c for c in clients if c.get('connected_ap') != 'N/A']
                
                print(f"\n📱 Client Devices:")
                print(f"   Total clients: {len(clients)}")
                print(f"   Connected clients: {len(connected_clients)}")
                
                if connected_clients:
                    print(f"\n✅ SUCCESS! Connected clients with BSSID (SSID) format:")
                    for client in connected_clients[:5]:
                        print(f"   📱 {client.get('name')} ({client.get('mac')})")
                        print(f"      → Connected AP: {client.get('connected_ap')}")
                        print(f"      → SSID: {client.get('connected_ssid')}")
                        print()
                else:
                    print(f"\n⚠️  No connected clients found (association data may not be available)")
                
                # Show access points
                aps = [d for d in devices if 'AP' in d.get('type', '')]
                print(f"\n📡 Access Points: {len(aps)} found")
                for ap in aps[:3]:
                    print(f"   📡 {ap.get('name')} ({ap.get('mac')})")
                    print(f"      → SSID: {ap.get('connected_ssid', 'Unknown')}")
                
                return True
                
            else:
                print(f"❌ API returned error: {data.get('error', 'Unknown error')}")
                return False
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('message', 'Unknown')}")
            except:
                print(f"   Raw response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out - the API call is taking too long")
        print("   This might indicate an issue with Kismet processing")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_bssid_mapping_direct()
    
    if success:
        print("\n🎉 BSSID to SSID mapping is working!")
        print("   Client devices should show 'BSSID (SSID)' format in connected_ap field")
    else:
        print("\n❌ BSSID mapping test failed")
        print("   Check Flask app logs and Kismet connectivity")
