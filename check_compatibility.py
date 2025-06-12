#!/usr/bin/env python3
"""
WiGuard Dashboard Compatibility Checker
Checks system compatibility and provides recommendations for optimal operation
"""

import os
import sys
import platform
import subprocess
import importlib
from pathlib import Path

def print_header():
    """Print the compatibility checker header"""
    print("=" * 60)
    print("WiGuard Dashboard - System Compatibility Checker")
    print("=" * 60)

def check_python_version():
    """Check Python version compatibility"""
    print("\n🐍 Python Version Check:")
    version = sys.version_info
    print(f"   Current: Python {version.major}.{version.minor}.{version.micro}")
    
    if version >= (3, 8):
        print("   ✅ Python version is compatible")
        return True
    else:
        print("   ❌ Python 3.8+ required")
        return False

def check_operating_system():
    """Check operating system compatibility"""
    print("\n💻 Operating System Check:")
    system = platform.system()
    release = platform.release()
    machine = platform.machine()
    
    print(f"   System: {system} {release}")
    print(f"   Architecture: {machine}")
    
    compatibility = {
        'Linux': '✅ Full compatibility',
        'Darwin': '⚠️  Limited wireless features',
        'Windows': '❌ Limited compatibility (use WSL2)'
    }
    
    status = compatibility.get(system, '❓ Unknown compatibility')
    print(f"   Status: {status}")
    
    return system == 'Linux'

def check_required_packages():
    """Check for required Python packages"""
    print("\n📦 Python Package Check:")
    
    required_packages = [
        ('flask', 'Flask'),
        ('MySQLdb', 'mysqlclient'),
        ('scapy', 'scapy'),
        ('requests', 'requests'),
        ('psutil', 'psutil'),
        ('termcolor', 'termcolor'),
    ]
    
    optional_packages = [
        ('pymysql', 'pymysql (MySQL fallback)'),
        ('dotenv', 'python-dotenv'),
        ('cryptography', 'cryptography'),
    ]
    
    all_good = True
    
    for module, name in required_packages:
        try:
            importlib.import_module(module)
            print(f"   ✅ {name}")
        except ImportError:
            print(f"   ❌ {name} - REQUIRED")
            all_good = False
    
    print("\n   Optional packages:")
    for module, name in optional_packages:
        try:
            importlib.import_module(module)
            print(f"   ✅ {name}")
        except ImportError:
            print(f"   ⚠️  {name} - optional")
    
    return all_good

def check_system_tools():
    """Check for required system tools"""
    print("\n🔧 System Tools Check:")
    
    tools = {
        'iwconfig': 'Wireless interface configuration',
        'iw': 'Modern wireless tools',
        'airmon-ng': 'Monitor mode creation',
        'nmap': 'Network discovery',
        'mysql': 'MySQL database client',
        'sudo': 'Elevated privileges',
    }
    
    available_tools = {}
    
    for tool, description in tools.items():
        try:
            result = subprocess.run(['which', tool], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"   ✅ {tool} - {description}")
                available_tools[tool] = True
            else:
                if tool in ['mysql']:
                    print(f"   ⚠️  {tool} - {description} (optional)")
                else:
                    print(f"   ❌ {tool} - {description}")
                available_tools[tool] = False
        except Exception:
            print(f"   ❌ {tool} - {description}")
            available_tools[tool] = False
    
    return available_tools

def check_network_interfaces():
    """Check for available network interfaces"""
    print("\n🌐 Network Interface Check:")
    
    try:
        # Try to import psutil for cross-platform interface detection
        import psutil
        interfaces = psutil.net_if_addrs()
        
        wireless_interfaces = []
        ethernet_interfaces = []
        other_interfaces = []
        
        for interface, addrs in interfaces.items():
            if any(keyword in interface.lower() 
                   for keyword in ['wlan', 'wifi', 'wireless']):
                wireless_interfaces.append(interface)
            elif any(keyword in interface.lower() 
                     for keyword in ['eth', 'enp', 'ens']):
                ethernet_interfaces.append(interface)
            elif interface.lower() not in ['lo', 'localhost']:
                other_interfaces.append(interface)
        
        print(f"   Wireless interfaces: {wireless_interfaces or 'None found'}")
        print(f"   Ethernet interfaces: {ethernet_interfaces or 'None found'}")
        if other_interfaces:
            print(f"   Other interfaces: {other_interfaces}")
        
        return len(wireless_interfaces) > 0
        
    except ImportError:
        print("   ⚠️  psutil not available, using fallback method")
        try:
            # Fallback: try to list interfaces using system commands
            if platform.system() == 'Linux':
                result = subprocess.run(['ip', 'link', 'show'], 
                                      capture_output=True, text=True)
                interfaces = []
                for line in result.stdout.split('\n'):
                    if ': ' in line and 'state' in line:
                        interface = line.split(': ')[1].split('@')[0]
                        interfaces.append(interface)
                print(f"   Available interfaces: {interfaces}")
                return any('wlan' in iface for iface in interfaces)
        except Exception:
            pass
        
        print("   ❌ Unable to detect network interfaces")
        return False

def check_permissions():
    """Check for required permissions"""
    print("\n🔐 Permissions Check:")
    
    # Check if running as root
    if os.geteuid() == 0:
        print("   ⚠️  Running as root (may be required for packet capture)")
    else:
        print("   ℹ️  Running as non-root user")
    
    # Check sudo access
    try:
        result = subprocess.run(['sudo', '-n', 'true'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("   ✅ Sudo access available")
            return True
        else:
            print("   ⚠️  Sudo access may be required for full functionality")
            return False
    except Exception:
        print("   ❌ Unable to check sudo access")
        return False

def check_database_connectivity():
    """Check database connectivity"""
    print("\n🗄️  Database Connectivity Check:")
    
    # Check if MySQL service is running
    try:
        result = subprocess.run(['systemctl', 'is-active', 'mysql'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("   ✅ MySQL service is running")
        else:
            # Try mariadb
            result = subprocess.run(['systemctl', 'is-active', 'mariadb'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("   ✅ MariaDB service is running")
            else:
                print("   ⚠️  MySQL/MariaDB service not running")
    except Exception:
        print("   ⚠️  Unable to check database service status")
    
    # Try to connect to database
    try:
        # Try mysqlclient first
        import MySQLdb
        
        # Default connection parameters
        conn_params = {
            'host': 'localhost',
            'user': 'dashboard',
            'passwd': 'securepass',
            'db': 'security_dashboard'
        }
        
        try:
            conn = MySQLdb.connect(**conn_params)
            conn.close()
            print("   ✅ Database connection successful")
            return True
        except Exception as e:
            print(f"   ❌ Database connection failed: {e}")
            print("   ℹ️  Database features will be disabled")
            return False
            
    except ImportError:
        try:
            import pymysql
            print("   ⚠️  Using pymysql fallback")
            return False
        except ImportError:
            print("   ❌ No MySQL connector available")
            return False

def provide_recommendations(results):
    """Provide recommendations based on check results"""
    print("\n💡 Recommendations:")
    
    if not results.get('python_ok', False):
        print("   📥 Upgrade Python to version 3.8 or higher")
    
    if not results.get('packages_ok', False):
        print("   📦 Install missing Python packages:")
        print("      pip install -r requirements.txt")
    
    if not results.get('wireless_ok', False):
        print("   📡 No wireless interfaces detected:")
        print("      - Check if wireless adapter is connected")
        print("      - Install wireless drivers if needed")
        print("      - Some features will be limited")
    
    if not results.get('tools_ok', False):
        print("   🔧 Install missing system tools:")
        if platform.system() == 'Linux':
            # Debian/Ubuntu
            print("      sudo apt install wireless-tools aircrack-ng nmap")
            # Red Hat/CentOS
            print("      # OR: sudo dnf install wireless-tools aircrack-ng nmap")
    
    if not results.get('database_ok', False):
        print("   🗄️  Database setup needed:")
        print("      - Install MySQL/MariaDB")
        print("      - Create database and user (see init.sql)")
        print("      - Configure connection in .env file")
    
    if not results.get('permissions_ok', False):
        print("   🔐 Permission setup:")
        print("      - Add user to netdev group: sudo usermod -a -G netdev $USER")
        print("      - Or run with sudo for packet capture features")

def main():
    """Main compatibility checker function"""
    print_header()
    
    results = {}
    
    # Run all checks
    results['python_ok'] = check_python_version()
    results['os_ok'] = check_operating_system()
    results['packages_ok'] = check_required_packages()
    
    tool_results = check_system_tools()
    results['tools_ok'] = any(tool_results.values())
    
    results['wireless_ok'] = check_network_interfaces()
    results['permissions_ok'] = check_permissions()
    results['database_ok'] = check_database_connectivity()
    
    # Overall assessment
    print("\n📊 Overall Assessment:")
    critical_checks = ['python_ok', 'packages_ok']
    important_checks = ['wireless_ok', 'tools_ok']
    
    critical_passed = all(results.get(check, False) for check in critical_checks)
    important_passed = all(results.get(check, False) for check in important_checks)
    
    if critical_passed and important_passed:
        print("   ✅ System is fully compatible")
        overall_status = "excellent"
    elif critical_passed:
        print("   ⚠️  System is compatible with some limitations")
        overall_status = "good"
    else:
        print("   ❌ System requires setup before use")
        overall_status = "needs_work"
    
    # Provide recommendations
    if overall_status != "excellent":
        provide_recommendations(results)
    
    print("\n" + "=" * 60)
    print("Compatibility check complete!")
    
    if overall_status == "excellent":
        print("✅ Your system is ready to run WiGuard Dashboard!")
    elif overall_status == "good":
        print("⚠️  Your system can run WiGuard with some limitations.")
    else:
        print("❌ Please address the issues above before running WiGuard.")
    
    print("\nFor detailed installation instructions, see INSTALL.md")
    print("=" * 60)
    
    # Return exit code based on results
    return 0 if critical_passed else 1

if __name__ == "__main__":
    sys.exit(main())
