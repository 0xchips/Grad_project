#!/usr/bin/env python3
"""
Test script to verify the BSSID to SSID mapping functionality works as expected.
This script directly tests the Flask API endpoint and demonstrates the "BSSID (SSID)" format.
"""

import requests
import json
import time

def test_flask_api():
    """Test the Flask API endpoint for BSSID mapping"""
    try:
        print("=== Testing Flask API BSSID Mapping ===")
        
        # Test the API endpoint
        response = requests.get('http://localhost:5050/api/kismet/devices', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                devices = data.get('devices', [])
                bssid_mappings = data.get('bssid_mappings', {})
                
                print(f"✅ API Success: {len(devices)} devices found")
                print(f"✅ BSSID Mappings: {len(bssid_mappings)} mappings")
                
                # Show BSSID mappings
                if bssid_mappings:
                    print("\n📍 BSSID to SSID Mappings:")
                    for bssid, ssid in list(bssid_mappings.items())[:5]:  # Show first 5
                        print(f"  {bssid} → {ssid}")
                
                # Find client devices with BSSID (SSID) format
                client_devices = [d for d in devices if 'Client' in d.get('type', '')]
                
                print(f"\n📱 Client Devices: {len(client_devices)} found")
                
                # Show clients with connected APs in "BSSID (SSID)" format
                connected_clients = [d for d in client_devices if d.get('connected_ap') != 'N/A']
                
                if connected_clients:
                    print(f"✅ Connected Clients with BSSID (SSID) format:")
                    for client in connected_clients[:5]:  # Show first 5
                        print(f"  📱 {client.get('name')} ({client.get('mac')})")
                        print(f"      → Connected to: {client.get('connected_ap')}")
                        print(f"      → SSID: {client.get('connected_ssid')}")
                        print()
                else:
                    print("⚠️  No connected clients found")
                
                # Show access points
                access_points = [d for d in devices if 'AP' in d.get('type', '') or 'Access Point' in d.get('type', '')]
                print(f"\n📡 Access Points: {len(access_points)} found")
                
                if access_points:
                    print("✅ Sample Access Points:")
                    for ap in access_points[:3]:  # Show first 3
                        print(f"  📡 {ap.get('name')} ({ap.get('mac')})")
                        print(f"      → SSID: {ap.get('connected_ssid', 'Unknown')}")
                        print()
                
                return True
                
            else:
                print(f"❌ API Error: {data.get('error', 'Unknown error')}")
                return False
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return False

def simulate_expected_output():
    """Show what the expected output should look like"""
    print("\n" + "="*60)
    print("📋 EXPECTED OUTPUT EXAMPLE")
    print("="*60)
    
    print("When working correctly, client devices should show:")
    print("📱 Client Device: Samsung_Galaxy_S21 (A4:C3:F0:12:34:56)")
    print("    → Connected to: DC:8D:8A:B9:13:36 (PotatoChips-2323@2.4GH)")
    print()
    print("📱 Client Device: iPhone_13_Pro (B2:F1:C4:67:89:AB)")
    print("    → Connected to: E1:2B:3C:4D:5E:6F (Home_WiFi_5G)")
    print()
    print("📱 Client Device: Dell_Laptop (C5:A8:2D:98:76:54)")
    print("    → Connected to: 6A:7B:8C:9D:E1:F2 (Office_Network)")
    
    print("\n" + "="*60)

def main():
    """Main test function"""
    print("🔍 Testing BSSID to SSID Mapping Implementation")
    print("=" * 60)
    
    # Test multiple times to catch any issues
    for attempt in range(3):
        print(f"\n🔄 Test Attempt {attempt + 1}")
        
        success = test_flask_api()
        
        if success:
            print("✅ Test completed successfully!")
            break
        else:
            print("❌ Test failed, retrying...")
            time.sleep(2)
    
    # Show expected output
    simulate_expected_output()
    
    print("\n💡 Key Points:")
    print("1. The 'connected_ap' field should show: 'BSSID (SSID)'")
    print("2. The 'connected_ssid' field should show just the SSID name")
    print("3. BSSID mappings dictionary helps translate MAC addresses to readable names")

if __name__ == "__main__":
    main()
