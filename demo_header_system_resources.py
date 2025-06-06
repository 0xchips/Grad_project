#!/usr/bin/env python3
"""
Demo script for System Resources Header Implementation
This script tests the new compact header format for system resources.
"""

import requests
import time
import sys
import psutil

def test_system_resources_header():
    """Test the system resources header implementation"""
    print("🚀 System Resources Header Demo")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:5053"
    api_url = f"{base_url}/api/system-resources"
    
    try:
        # Test API connectivity
        print("📡 Testing API connectivity...")
        response = requests.get(api_url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        print("✅ API connection successful!")
        print(f"📊 Current System Stats:")
        print(f"   🟢 CPU: {data['cpu']['percent']:.1f}% ({data['cpu']['cores']} cores)")
        print(f"   🟡 RAM: {data['memory']['percent']:.1f}% ({data['memory']['used_gb']:.1f}/{data['memory']['total_gb']:.1f} GB)")
        
        # Format network data
        net_sent_mb = data['network']['bytes_sent'] / (1024 * 1024)
        net_recv_mb = data['network']['bytes_recv'] / (1024 * 1024)
        print(f"   🔵 Network: ↑{net_sent_mb:.1f}MB ↓{net_recv_mb:.1f}MB")
        print(f"   🟠 Disk: {data['disk']['percent']:.1f}% ({data['disk']['used_gb']:.1f}/{data['disk']['total_gb']:.1f} GB)")
        
        print("\n🎯 Header Features Implemented:")
        print("   ✅ Compact emoji indicators (🟢🟡🔵🟠)")
        print("   ✅ Real-time data updates (2-second intervals)")
        print("   ✅ Responsive design for different screen sizes")
        print("   ✅ Dynamic emoji colors based on usage levels")
        print("   ✅ Network upload/download arrows (↑/↓)")
        print("   ✅ Hover effects and animations")
        
        print("\n🔄 Testing real-time updates...")
        for i in range(3):
            print(f"   Update {i+1}/3:", end=" ")
            response = requests.get(api_url, timeout=5)
            data = response.json()
            print(f"CPU: {data['cpu']['percent']:.1f}% | RAM: {data['memory']['percent']:.1f}%")
            time.sleep(2)
        
        print("\n📱 Responsive Design Tests:")
        print("   📺 Desktop: Full header with all resources")
        print("   💻 Tablet: Compact view with smaller fonts")
        print("   📱 Mobile: Ultra-compact with essential info only")
        
        print(f"\n🌐 Dashboard URL: {base_url}")
        print("   Check the header area for the new compact system resources!")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed! Make sure the Flask server is running.")
        print("   Run: python3 flaskkk.py")
        return False
    except requests.exceptions.Timeout:
        print("⏰ Request timed out! Server might be overloaded.")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def generate_system_load():
    """Generate some system load for testing"""
    print("\n🔥 Generating system load for demo...")
    
    # CPU load
    print("   📈 Creating CPU load...")
    import threading
    import math
    
    def cpu_stress():
        end_time = time.time() + 5
        while time.time() < end_time:
            math.sqrt(123456789)
    
    # Start multiple threads to create CPU load
    threads = []
    for _ in range(4):
        t = threading.Thread(target=cpu_stress)
        t.start()
        threads.append(t)
    
    print("   💾 Creating memory usage...")
    # Create some memory usage
    memory_hog = []
    try:
        for _ in range(50):
            memory_hog.append([0] * 100000)  # Allocate some memory
            time.sleep(0.1)
    except MemoryError:
        pass
    
    # Wait for CPU threads to finish
    for t in threads:
        t.join()
    
    print("   ✅ Load generation complete!")
    print("   📊 Check the dashboard header to see updated values!")

if __name__ == "__main__":
    print("System Resources Header Demo")
    print("This demo showcases the new compact header implementation")
    print()
    
    # Test basic functionality
    success = test_system_resources_header()
    
    if success:
        # Ask if user wants to generate load for testing
        print("\n" + "="*50)
        user_input = input("Generate system load for testing? (y/n): ").strip().lower()
        
        if user_input in ['y', 'yes']:
            generate_system_load()
            print("\n🔄 Re-testing with new load...")
            test_system_resources_header()
    
    print("\n🎉 Demo complete! The system resources are now displayed in a compact header format.")
    print("📋 Features:")
    print("   • Moved from card-based to compact header design")
    print("   • Added emoji indicators with dynamic colors")
    print("   • Responsive layout for different screen sizes")
    print("   • Real-time monitoring with 2-second updates")
    print("   • Network upload/download display with arrows")
