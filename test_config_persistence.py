#!/usr/bin/env python3
"""
Test script to verify configuration persistence
Simulates the user scenario: configure adapters -> navigate to another page -> return to config page
"""

import requests
import json
import time

BASE_URL = "http://localhost:5053"

def test_wireless_adapters():
    """Test wireless adapters endpoint"""
    print("🔍 Testing wireless adapters endpoint...")
    response = requests.get(f"{BASE_URL}/api/wireless-adapters")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['count']} wireless adapters:")
        for adapter in data['adapters']:
            print(f"   - {adapter['name']}: {adapter['description']} ({adapter['mode']})")
        return data['adapters']
    else:
        print(f"❌ Failed to get wireless adapters: {response.status_code}")
        return []

def test_get_configuration():
    """Test getting current configuration"""
    print("\n📖 Testing configuration retrieval...")
    response = requests.get(f"{BASE_URL}/api/configurations")
    if response.status_code == 200:
        data = response.json()
        print("✅ Current configuration:")
        print(json.dumps(data['configuration'], indent=2))
        return data['configuration']
    else:
        print(f"❌ Failed to get configuration: {response.status_code}")
        return {}

def test_save_configuration(config):
    """Test saving configuration"""
    print("\n💾 Testing configuration saving...")
    response = requests.post(
        f"{BASE_URL}/api/configurations",
        headers={'Content-Type': 'application/json'},
        data=json.dumps(config)
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Configuration saved: {data['message']}")
        return True
    else:
        print(f"❌ Failed to save configuration: {response.status_code}")
        print(response.text)
        return False

def simulate_page_navigation():
    """Simulate navigating to another page and back"""
    print("\n🔄 Simulating page navigation...")
    
    # Navigate to index page
    response = requests.get(f"{BASE_URL}/index.html")
    if response.status_code == 200:
        print("✅ Navigated to index page")
    else:
        print("❌ Failed to navigate to index page")
    
    time.sleep(1)
    
    # Navigate back to configurations page
    response = requests.get(f"{BASE_URL}/configurations.html")
    if response.status_code == 200:
        print("✅ Navigated back to configurations page")
    else:
        print("❌ Failed to navigate back to configurations page")

def main():
    print("🧪 Testing Configuration Persistence")
    print("=" * 50)
    
    # Step 1: Get available adapters
    adapters = test_wireless_adapters()
    if not adapters:
        print("❌ No adapters found, cannot continue test")
        return
    
    # Step 2: Get current configuration
    current_config = test_get_configuration()
    
    # Step 3: Create a test configuration
    test_config = {
        'realtime_monitoring': adapters[0]['name'] if len(adapters) > 0 else '',
        'network_devices': adapters[1]['name'] if len(adapters) > 1 else adapters[0]['name'],
        'kismet_monitoring': adapters[2]['name'] if len(adapters) > 2 else adapters[0]['name']
    }
    
    print(f"\n🎯 Test configuration to save:")
    print(json.dumps(test_config, indent=2))
    
    # Step 4: Save the test configuration
    if not test_save_configuration(test_config):
        print("❌ Failed to save configuration, stopping test")
        return
    
    # Step 5: Simulate page navigation
    simulate_page_navigation()
    
    # Step 6: Verify configuration is still saved
    print("\n🔍 Verifying configuration persistence after navigation...")
    saved_config = test_get_configuration()
    
    # Step 7: Compare configurations
    if saved_config == test_config:
        print("✅ SUCCESS: Configuration persisted correctly!")
    else:
        print("❌ FAILURE: Configuration was not persisted!")
        print("Expected:")
        print(json.dumps(test_config, indent=2))
        print("Actually got:")
        print(json.dumps(saved_config, indent=2))
    
    print("\n" + "=" * 50)
    print("🧪 Test completed")

if __name__ == "__main__":
    main()
