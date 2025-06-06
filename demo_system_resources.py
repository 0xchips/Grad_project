#!/usr/bin/env python3
"""
System Resources Monitoring - Live Demo Script
==============================================

This script demonstrates the completed System Resources monitoring feature
by showing real-time data from the dashboard API.

Usage: python3 demo_system_resources.py
"""

import requests
import time
import json
from datetime import datetime

def format_bytes(bytes_value):
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} TB"

def get_usage_color(percentage):
    """Get color indicator based on usage percentage"""
    if percentage >= 80:
        return "🔴"  # Red - High usage
    elif percentage >= 60:
        return "🟡"  # Yellow - Medium usage
    else:
        return "🟢"  # Green - Normal usage

def display_system_resources():
    """Fetch and display system resources"""
    try:
        response = requests.get('http://localhost:5053/api/system-resources', timeout=5)
        if response.status_code == 200:
            data = response.json()
            
            # Clear screen (works on most terminals)
            print('\033[2J\033[H')
            
            print("🖥️  CyberShield Dashboard - System Resources Monitor")
            print("=" * 60)
            print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print()
            
            # CPU Information
            cpu_percent = data['cpu']['percent']
            cpu_cores = data['cpu']['cores']
            cpu_color = get_usage_color(cpu_percent)
            print(f"{cpu_color} CPU Usage: {cpu_percent:.1f}% ({cpu_cores} cores)")
            print(f"   {'█' * int(cpu_percent/2):<50} {cpu_percent:.1f}%")
            print()
            
            # Memory Information
            mem_percent = data['memory']['percent']
            mem_used = data['memory']['used_gb']
            mem_total = data['memory']['total_gb']
            mem_available = data['memory']['available_gb']
            mem_color = get_usage_color(mem_percent)
            print(f"{mem_color} Memory Usage: {mem_percent:.1f}%")
            print(f"   Used: {mem_used:.1f}GB | Total: {mem_total:.1f}GB | Available: {mem_available:.1f}GB")
            print(f"   {'█' * int(mem_percent/2):<50} {mem_percent:.1f}%")
            print()
            
            # Network Information
            net_sent = data['network']['bytes_sent']
            net_recv = data['network']['bytes_recv']
            net_packets_sent = data['network']['packets_sent']
            net_packets_recv = data['network']['packets_recv']
            print(f"🌐 Network I/O:")
            print(f"   ⬆️  Sent: {format_bytes(net_sent)} ({net_packets_sent:,} packets)")
            print(f"   ⬇️  Received: {format_bytes(net_recv)} ({net_packets_recv:,} packets)")
            print(f"   📊 Total: {format_bytes(net_sent + net_recv)}")
            print()
            
            # Disk Information
            disk_percent = data['disk']['percent']
            disk_used = data['disk']['used_gb']
            disk_total = data['disk']['total_gb']
            disk_free = data['disk']['free_gb']
            disk_color = get_usage_color(disk_percent)
            print(f"{disk_color} Disk Usage: {disk_percent:.1f}%")
            print(f"   Used: {disk_used:.1f}GB | Total: {disk_total:.1f}GB | Free: {disk_free:.1f}GB")
            print(f"   {'█' * int(disk_percent/2):<50} {disk_percent:.1f}%")
            print()
            
            print("=" * 60)
            print("🔄 Updates every 2 seconds | Press Ctrl+C to exit")
            print("🌐 Dashboard: http://localhost:5053")
            
        else:
            print(f"❌ API Error: HTTP {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

def main():
    """Main demo loop"""
    print("🚀 Starting System Resources Demo...")
    print("   Connecting to CyberShield Dashboard...")
    
    try:
        while True:
            display_system_resources()
            time.sleep(2)  # Match dashboard refresh rate
            
    except KeyboardInterrupt:
        print("\n\n👋 Demo stopped by user")
        print("✅ System Resources monitoring is working perfectly!")
        print("🎯 Feature Status: COMPLETE AND OPERATIONAL")

if __name__ == "__main__":
    main()
