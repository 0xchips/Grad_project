#!/usr/bin/env python3
"""
Demo script for Updated Memory Display Format
Tests the new memory format: "Memory: 81.2% (3.56GB/4.8GB)"
"""

import requests
import time

def test_memory_format():
    """Test the updated memory display format"""
    print("🔧 Testing Updated Memory Display Format")
    print("=" * 50)
    
    try:
        response = requests.get('http://127.0.0.1:5053/api/system-resources', timeout=5)
        data = response.json()
        
        memory = data['memory']
        cpu = data['cpu']
        network = data['network']
        disk = data['disk']
        
        print("📊 Current System Resources:")
        print(f"   🟢 CPU: {cpu['percent']:.1f}%")
        print(f"   🟡 Memory: {memory['percent']:.1f}% ({memory['used_gb']:.2f}GB/{memory['total_gb']:.1f}GB)")
        
        # Network formatting
        net_sent_mb = network['bytes_sent'] / (1024 * 1024)
        net_recv_mb = network['bytes_recv'] / (1024 * 1024)
        
        if net_sent_mb < 1:
            sent_str = f"{(net_sent_mb * 1024):.0f}K"
        elif net_sent_mb < 1024:
            sent_str = f"{net_sent_mb:.1f}M"
        else:
            sent_str = f"{(net_sent_mb / 1024):.1f}G"
            
        if net_recv_mb < 1:
            recv_str = f"{(net_recv_mb * 1024):.0f}K"
        elif net_recv_mb < 1024:
            recv_str = f"{net_recv_mb:.1f}M"
        else:
            recv_str = f"{(net_recv_mb / 1024):.1f}G"
        
        print(f"   🔵 Network: ↑{sent_str} ↓{recv_str}")
        print(f"   🟠 Disk: {disk['percent']:.1f}%")
        
        print("\n✅ Updated Features:")
        print("   • Memory now shows: Percentage + (UsedGB/TotalGB)")
        print("   • Format: 'Memory: 81.2% (3.56GB/4.8GB)'")
        print("   • Responsive design adjusted for longer text")
        print("   • CSS spacing optimized for all screen sizes")
        
        print(f"\n🌐 Check the header at: http://127.0.0.1:5053")
        print("   The memory section now displays both percentage and GB usage!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_memory_format()
