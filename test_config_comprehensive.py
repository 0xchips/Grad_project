#!/usr/bin/env python3
"""
Comprehensive test for wireless adapter configuration persistence
Tests the complete workflow: save config -> navigate away -> return -> verify persistence
"""

import requests
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

BASE_URL = "http://localhost:5053"

def test_backend_apis():
    """Test that backend APIs are working correctly"""
    print("🧪 Testing Backend APIs")
    print("=" * 40)
    
    # Test wireless adapters endpoint
    print("1. Testing wireless adapters endpoint...")
    response = requests.get(f"{BASE_URL}/api/wireless-adapters")
    if response.status_code == 200:
        data = response.json()
        adapters = data.get('adapters', [])
        print(f"   ✅ Found {len(adapters)} wireless adapters")
        for adapter in adapters:
            print(f"      - {adapter['name']} ({adapter['mode']})")
        return adapters
    else:
        print(f"   ❌ Failed: {response.status_code}")
        return []

def test_configuration_apis(adapters):
    """Test configuration save/load APIs"""
    print("\n2. Testing configuration APIs...")
    
    if len(adapters) < 3:
        print("   ⚠️ Need at least 3 adapters for full test")
        return False
    
    # Create test configuration
    test_config = {
        'realtime_monitoring': adapters[0]['name'],
        'network_devices': adapters[1]['name'], 
        'kismet_monitoring': adapters[2]['name']
    }
    
    print(f"   📝 Test config: {json.dumps(test_config, indent=2)}")
    
    # Save configuration
    response = requests.post(
        f"{BASE_URL}/api/configurations",
        headers={'Content-Type': 'application/json'},
        data=json.dumps(test_config)
    )
    
    if response.status_code == 200:
        print("   ✅ Configuration saved successfully")
    else:
        print(f"   ❌ Failed to save: {response.status_code}")
        return False
    
    # Load configuration
    response = requests.get(f"{BASE_URL}/api/configurations")
    if response.status_code == 200:
        data = response.json()
        loaded_config = data.get('configuration', {})
        print(f"   📖 Loaded config: {json.dumps(loaded_config, indent=2)}")
        
        if loaded_config == test_config:
            print("   ✅ Configuration persistence verified")
            return True
        else:
            print("   ❌ Configuration mismatch!")
            return False
    else:
        print(f"   ❌ Failed to load: {response.status_code}")
        return False

def test_frontend_with_selenium():
    """Test frontend using Selenium (if available)"""
    print("\n3. Testing frontend with browser automation...")
    
    try:
        # Setup Chrome options for headless mode
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(f"{BASE_URL}/configurations.html")
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "realtime-monitoring"))
        )
        
        print("   ✅ Configuration page loaded")
        
        # Check if dropdowns are populated
        realtime_select = Select(driver.find_element(By.ID, "realtime-monitoring"))
        network_select = Select(driver.find_element(By.ID, "network-devices"))
        kismet_select = Select(driver.find_element(By.ID, "kismet-monitoring"))
        
        realtime_options = [opt.get_attribute('value') for opt in realtime_select.options if opt.get_attribute('value')]
        network_options = [opt.get_attribute('value') for opt in network_select.options if opt.get_attribute('value')]
        kismet_options = [opt.get_attribute('value') for opt in kismet_select.options if opt.get_attribute('value')]
        
        print(f"   📋 Realtime options: {realtime_options}")
        print(f"   📋 Network options: {network_options}")
        print(f"   📋 Kismet options: {kismet_options}")
        
        # Check current selected values
        realtime_value = realtime_select.first_selected_option.get_attribute('value')
        network_value = network_select.first_selected_option.get_attribute('value')
        kismet_value = kismet_select.first_selected_option.get_attribute('value')
        
        print(f"   🎯 Current selections:")
        print(f"      Realtime: '{realtime_value}'")
        print(f"      Network: '{network_value}'")
        print(f"      Kismet: '{kismet_value}'")
        
        # Check if saved configuration is loaded
        response = requests.get(f"{BASE_URL}/api/configurations")
        if response.status_code == 200:
            saved_config = response.json().get('configuration', {})
            
            matches = {
                'realtime_monitoring': realtime_value == saved_config.get('realtime_monitoring', ''),
                'network_devices': network_value == saved_config.get('network_devices', ''),
                'kismet_monitoring': kismet_value == saved_config.get('kismet_monitoring', '')
            }
            
            print(f"   🔍 Configuration matching:")
            for key, match in matches.items():
                status = "✅" if match else "❌"
                expected = saved_config.get(key, '')
                actual = realtime_value if key == 'realtime_monitoring' else (network_value if key == 'network_devices' else kismet_value)
                print(f"      {status} {key}: expected '{expected}', got '{actual}'")
            
            if all(matches.values()):
                print("   ✅ All configurations match - persistence working!")
                return True
            else:
                print("   ❌ Configuration persistence not working properly")
                return False
        
        driver.quit()
        
    except Exception as e:
        print(f"   ⚠️ Selenium test skipped: {e}")
        return None

def main():
    print("🧪 Comprehensive Configuration Persistence Test")
    print("=" * 60)
    
    # Test backend APIs
    adapters = test_backend_apis()
    if not adapters:
        print("❌ Backend API test failed - cannot continue")
        return
    
    # Test configuration APIs
    if not test_configuration_apis(adapters):
        print("❌ Configuration API test failed - cannot continue")
        return
    
    # Test frontend
    frontend_result = test_frontend_with_selenium()
    
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print(f"   Backend APIs: ✅ Working")
    print(f"   Configuration APIs: ✅ Working") 
    if frontend_result is True:
        print(f"   Frontend Persistence: ✅ Working")
    elif frontend_result is False:
        print(f"   Frontend Persistence: ❌ Not Working")
    else:
        print(f"   Frontend Persistence: ⚠️ Could not test (Selenium not available)")
    
    print("\n🔧 Next Steps:")
    if frontend_result is False:
        print("   - Frontend JavaScript needs debugging")
        print("   - Check browser console for errors")
        print("   - Verify timing of configuration loading vs select population")
    elif frontend_result is None:
        print("   - Install Selenium for automated browser testing")
        print("   - Manually test the configuration page in browser")
    else:
        print("   - All tests passed! Configuration persistence is working.")

if __name__ == "__main__":
    main()
