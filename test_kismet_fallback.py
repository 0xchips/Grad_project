#!/usr/bin/env python3

import subprocess
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_kismet_fallback():
    """Test the Kismet fallback logic"""
    
    # Check for wireless interface
    interface = "wlx1cbfcece3103"
    
    print(f"Testing Kismet fallback with interface: {interface}")
    
    # Check if Kismet is available
    try:
        subprocess.run(['which', 'kismet'], check=True, capture_output=True)
        print("✓ Kismet is available")
        kismet_available = True
    except subprocess.CalledProcessError:
        print("✗ Kismet is NOT available")
        kismet_available = False
    
    # Check if airodump-ng is available
    try:
        subprocess.run(['which', 'airodump-ng'], check=True, capture_output=True)
        print("✓ airodump-ng is available")
        airodump_available = True
    except subprocess.CalledProcessError:
        print("✗ airodump-ng is NOT available")
        airodump_available = False
    
    # Check if interface exists
    if os.path.exists(f"/sys/class/net/{interface}"):
        print(f"✓ Interface {interface} exists")
    else:
        print(f"✗ Interface {interface} does not exist")
        return
    
    # Test the fallback logic
    if kismet_available:
        cmd = ['sudo', 'kismet', '--version']
        tool = "Kismet"
    else:
        cmd = ['sudo', 'airodump-ng', '--help']
        tool = "airodump-ng"
    
    print(f"Would use: {tool}")
    print(f"Command would be: {' '.join(cmd)}")
    
    # Test the actual command (non-destructive)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        print(f"✓ {tool} test successful")
        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"Output: {result.stdout[:200]}...")
    except Exception as e:
        print(f"✗ {tool} test failed: {e}")

if __name__ == "__main__":
    test_kismet_fallback()
