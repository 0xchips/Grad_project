#!/usr/bin/env python3
"""
Advanced System Validator and Troubleshooter for WiGuard Dashboard
Comprehensive system validation, troubleshooting, and auto-repair capabilities
"""

import os
import sys
import subprocess
import platform
import json
import logging
import time
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, NamedTuple
from dataclasses import dataclass, asdict
from enum import Enum
import requests
import socket
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestResult(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    SKIP = "SKIP"

class TestCategory(Enum):
    SYSTEM = "system"
    NETWORK = "network"
    WIRELESS = "wireless"
    DATABASE = "database"
    PYTHON = "python"
    PERMISSIONS = "permissions"
    SERVICES = "services"

@dataclass
class ValidationTest:
    name: str
    category: TestCategory
    description: str
    result: TestResult
    message: str
    fix_suggestion: Optional[str] = None
    auto_fixable: bool = False
    execution_time: float = 0.0
    details: Dict = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}

class SystemValidator:
    """Comprehensive system validation and troubleshooting"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.is_linux = self.system == 'linux'
        self.is_windows = self.system == 'windows'
        self.is_macos = self.system == 'darwin'
        self.tests = []
        self.auto_fix_enabled = False
        
        # Load system configuration if available
        try:
            from system_config import get_config
            self.system_config = get_config()
        except ImportError:
            self.system_config = None
    
    def run_all_tests(self, categories: List[TestCategory] = None, auto_fix: bool = False) -> List[ValidationTest]:
        """Run all validation tests"""
        self.auto_fix_enabled = auto_fix
        self.tests = []
        
        if categories is None:
            categories = list(TestCategory)
        
        logger.info("Starting comprehensive system validation...")
        
        # System tests
        if TestCategory.SYSTEM in categories:
            self._run_system_tests()
        
        # Python environment tests
        if TestCategory.PYTHON in categories:
            self._run_python_tests()
        
        # Network tests
        if TestCategory.NETWORK in categories:
            self._run_network_tests()
        
        # Wireless tests
        if TestCategory.WIRELESS in categories:
            self._run_wireless_tests()
        
        # Database tests
        if TestCategory.DATABASE in categories:
            self._run_database_tests()
        
        # Permissions tests
        if TestCategory.PERMISSIONS in categories:
            self._run_permissions_tests()
        
        # Services tests
        if TestCategory.SERVICES in categories:
            self._run_services_tests()
        
        logger.info(f"Validation completed. {len(self.tests)} tests run.")
        return self.tests
    
    def _run_test(self, name: str, category: TestCategory, description: str, 
                  test_func, fix_func=None) -> ValidationTest:
        """Run a single test with timing and error handling"""
        start_time = time.time()
        
        try:
            result, message, details = test_func()
            execution_time = time.time() - start_time
            
            test = ValidationTest(
                name=name,
                category=category,
                description=description,
                result=result,
                message=message,
                execution_time=execution_time,
                details=details or {},
                auto_fixable=fix_func is not None
            )
            
            # Attempt auto-fix if enabled and test failed
            if (self.auto_fix_enabled and fix_func and 
                result in [TestResult.FAIL, TestResult.WARN]):
                try:
                    fix_result = fix_func()
                    if fix_result:
                        test.message += f" [AUTO-FIXED: {fix_result}]"
                        test.result = TestResult.PASS
                except Exception as e:
                    test.message += f" [AUTO-FIX FAILED: {e}]"
            
            # Add fix suggestion
            if fix_func and test.result in [TestResult.FAIL, TestResult.WARN]:
                test.fix_suggestion = self._get_fix_suggestion(name, test.details)
            
        except Exception as e:
            execution_time = time.time() - start_time
            test = ValidationTest(
                name=name,
                category=category,
                description=description,
                result=TestResult.FAIL,
                message=f"Test execution failed: {e}",
                execution_time=execution_time,
                details={'error': str(e)}
            )
        
        self.tests.append(test)
        return test
    
    def _run_system_tests(self):
        """Run system-level tests"""
        
        def test_os_compatibility():
            supported_systems = ['linux', 'darwin', 'windows']
            if self.system in supported_systems:
                return TestResult.PASS, f"OS {platform.system()} is supported", {'os': self.system}
            else:
                return TestResult.WARN, f"OS {platform.system()} has limited support", {'os': self.system}
        
        def test_python_version():
            version = sys.version_info
            if version >= (3, 8):
                return TestResult.PASS, f"Python {version.major}.{version.minor}.{version.micro} is compatible", {'version': f"{version.major}.{version.minor}.{version.micro}"}
            elif version >= (3, 6):
                return TestResult.WARN, f"Python {version.major}.{version.minor}.{version.micro} is minimally supported", {'version': f"{version.major}.{version.minor}.{version.micro}"}
            else:
                return TestResult.FAIL, f"Python {version.major}.{version.minor}.{version.micro} is too old", {'version': f"{version.major}.{version.minor}.{version.micro}"}
        
        def test_disk_space():
            try:
                disk_usage = shutil.disk_usage('/')
                free_gb = disk_usage.free / (1024**3)
                total_gb = disk_usage.total / (1024**3)
                percent_free = (disk_usage.free / disk_usage.total) * 100
                
                if free_gb < 1:
                    return TestResult.FAIL, f"Critical: Only {free_gb:.1f}GB free space", {'free_gb': free_gb, 'percent_free': percent_free}
                elif free_gb < 5:
                    return TestResult.WARN, f"Warning: Only {free_gb:.1f}GB free space", {'free_gb': free_gb, 'percent_free': percent_free}
                else:
                    return TestResult.PASS, f"{free_gb:.1f}GB free space available", {'free_gb': free_gb, 'percent_free': percent_free}
            except Exception as e:
                return TestResult.FAIL, f"Cannot check disk space: {e}", {}
        
        def test_memory():
            try:
                import psutil
                memory = psutil.virtual_memory()
                total_gb = memory.total / (1024**3)
                
                if total_gb < 2:
                    return TestResult.FAIL, f"Insufficient memory: {total_gb:.1f}GB", {'total_gb': total_gb}
                elif total_gb < 4:
                    return TestResult.WARN, f"Limited memory: {total_gb:.1f}GB", {'total_gb': total_gb}
                else:
                    return TestResult.PASS, f"Adequate memory: {total_gb:.1f}GB", {'total_gb': total_gb}
            except ImportError:
                return TestResult.SKIP, "psutil not available for memory check", {}
        
        self._run_test("OS Compatibility", TestCategory.SYSTEM, "Check OS compatibility", test_os_compatibility)
        self._run_test("Python Version", TestCategory.SYSTEM, "Check Python version", test_python_version)
        self._run_test("Disk Space", TestCategory.SYSTEM, "Check available disk space", test_disk_space)
        self._run_test("Memory", TestCategory.SYSTEM, "Check system memory", test_memory)
    
    def _run_python_tests(self):
        """Run Python environment tests"""
        
        def test_virtual_environment():
            in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
            if in_venv:
                return TestResult.PASS, "Running in virtual environment", {'venv_path': sys.prefix}
            else:
                return TestResult.WARN, "Not running in virtual environment", {'system_python': True}
        
        def test_required_packages():
            required_packages = [
                'flask', 'requests', 'termcolor', 'python-dotenv',
                'scapy', 'psutil'
            ]
            
            missing_packages = []
            available_packages = []
            
            for package in required_packages:
                try:
                    __import__(package.replace('-', '_'))
                    available_packages.append(package)
                except ImportError:
                    missing_packages.append(package)
            
            if not missing_packages:
                return TestResult.PASS, f"All required packages available", {'available': available_packages}
            elif len(missing_packages) <= 2:
                return TestResult.WARN, f"Some packages missing: {missing_packages}", {'missing': missing_packages, 'available': available_packages}
            else:
                return TestResult.FAIL, f"Many packages missing: {missing_packages}", {'missing': missing_packages, 'available': available_packages}
        
        def test_database_connectors():
            connectors = []
            try:
                import MySQLdb
                connectors.append('MySQLdb')
            except ImportError:
                pass
            
            try:
                import pymysql
                connectors.append('pymysql')
            except ImportError:
                pass
            
            if connectors:
                return TestResult.PASS, f"Database connectors available: {connectors}", {'connectors': connectors}
            else:
                return TestResult.FAIL, "No database connectors available", {'connectors': []}
        
        self._run_test("Virtual Environment", TestCategory.PYTHON, "Check virtual environment", test_virtual_environment)
        self._run_test("Required Packages", TestCategory.PYTHON, "Check required Python packages", test_required_packages)
        self._run_test("Database Connectors", TestCategory.PYTHON, "Check database connectivity", test_database_connectors)
    
    def _run_network_tests(self):
        """Run network connectivity tests"""
        
        def test_internet_connectivity():
            try:
                response = requests.get('https://8.8.8.8', timeout=10)
                return TestResult.PASS, "Internet connectivity available", {'response_code': response.status_code}
            except requests.exceptions.RequestException as e:
                return TestResult.FAIL, f"No internet connectivity: {e}", {}
        
        def test_dns_resolution():
            try:
                socket.getaddrinfo('www.google.com', 80)
                return TestResult.PASS, "DNS resolution working", {}
            except socket.gaierror as e:
                return TestResult.FAIL, f"DNS resolution failed: {e}", {}
        
        def test_local_network():
            try:
                # Try to connect to local gateway
                result = subprocess.run(['ping', '-c', '1', '192.168.1.1'], 
                                      capture_output=True, timeout=10)
                if result.returncode == 0:
                    return TestResult.PASS, "Local network connectivity", {}
                else:
                    return TestResult.WARN, "Local network connectivity issues", {}
            except Exception as e:
                return TestResult.SKIP, f"Cannot test local network: {e}", {}
        
        def test_port_availability():
            default_ports = [5053, 3306, 6379]  # Flask, MySQL, Redis
            available_ports = []
            used_ports = []
            
            for port in default_ports:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    result = sock.connect_ex(('127.0.0.1', port))
                    if result == 0:
                        used_ports.append(port)
                    else:
                        available_ports.append(port)
                finally:
                    sock.close()
            
            if used_ports:
                return TestResult.WARN, f"Some ports in use: {used_ports}", {'used': used_ports, 'available': available_ports}
            else:
                return TestResult.PASS, "Default ports available", {'available': available_ports}
        
        self._run_test("Internet Connectivity", TestCategory.NETWORK, "Test internet connection", test_internet_connectivity)
        self._run_test("DNS Resolution", TestCategory.NETWORK, "Test DNS resolution", test_dns_resolution)
        self._run_test("Local Network", TestCategory.NETWORK, "Test local network", test_local_network)
        self._run_test("Port Availability", TestCategory.NETWORK, "Check port availability", test_port_availability)
    
    def _run_wireless_tests(self):
        """Run wireless capability tests"""
        
        def test_wireless_tools():
            tools = ['iwconfig', 'iw', 'airmon-ng', 'airodump-ng']
            available_tools = []
            missing_tools = []
            
            for tool in tools:
                if shutil.which(tool):
                    available_tools.append(tool)
                else:
                    missing_tools.append(tool)
            
            if len(available_tools) >= 2:
                return TestResult.PASS, f"Wireless tools available: {available_tools}", {'available': available_tools, 'missing': missing_tools}
            elif available_tools:
                return TestResult.WARN, f"Limited wireless tools: {available_tools}", {'available': available_tools, 'missing': missing_tools}
            else:
                return TestResult.FAIL, "No wireless tools available", {'missing': missing_tools}
        
        def test_wireless_interfaces():
            interfaces = []
            
            try:
                # Method 1: Check /sys/class/net for wireless interfaces
                net_path = Path('/sys/class/net')
                if net_path.exists():
                    for iface_path in net_path.iterdir():
                        if (iface_path / 'wireless').exists():
                            interfaces.append(iface_path.name)
            except Exception:
                pass
            
            if not interfaces:
                try:
                    # Method 2: Use iwconfig
                    result = subprocess.run(['iwconfig'], capture_output=True, text=True, timeout=10)
                    for line in result.stdout.split('\n'):
                        if 'IEEE 802.11' in line:
                            interface = line.split()[0]
                            if interface not in interfaces:
                                interfaces.append(interface)
                except Exception:
                    pass
            
            if interfaces:
                return TestResult.PASS, f"Wireless interfaces found: {interfaces}", {'interfaces': interfaces}
            else:
                return TestResult.FAIL, "No wireless interfaces detected", {}
        
        def test_monitor_mode_capability():
            if not self.is_linux:
                return TestResult.SKIP, "Monitor mode only supported on Linux", {}
            
            try:
                result = subprocess.run(['iw', 'list'], capture_output=True, text=True, timeout=10)
                if 'monitor' in result.stdout.lower():
                    return TestResult.PASS, "Monitor mode capability detected", {}
                else:
                    return TestResult.WARN, "Monitor mode capability uncertain", {}
            except Exception as e:
                return TestResult.FAIL, f"Cannot check monitor mode: {e}", {}
        
        if self.is_linux or self.is_macos:
            self._run_test("Wireless Tools", TestCategory.WIRELESS, "Check wireless tools availability", test_wireless_tools)
            self._run_test("Wireless Interfaces", TestCategory.WIRELESS, "Detect wireless interfaces", test_wireless_interfaces)
            
        if self.is_linux:
            self._run_test("Monitor Mode", TestCategory.WIRELESS, "Check monitor mode capability", test_monitor_mode_capability)
    
    def _run_database_tests(self):
        """Run database connectivity tests"""
        
        def test_mysql_service():
            try:
                # Try connecting to local MySQL
                import pymysql
                connection = pymysql.connect(
                    host='localhost',
                    user='root',
                    password='',
                    connect_timeout=5
                )
                connection.close()
                return TestResult.PASS, "MySQL service accessible", {}
            except Exception as e:
                return TestResult.WARN, f"MySQL service not accessible: {e}", {}
        
        def test_database_schema():
            # Check if database files exist
            db_files = ['security_dashboard.db', 'init.sql']
            existing_files = []
            
            for db_file in db_files:
                if Path(db_file).exists():
                    existing_files.append(db_file)
            
            if existing_files:
                return TestResult.PASS, f"Database files found: {existing_files}", {'files': existing_files}
            else:
                return TestResult.WARN, "No database files found", {}
        
        self._run_test("MySQL Service", TestCategory.DATABASE, "Check MySQL service", test_mysql_service)
        self._run_test("Database Schema", TestCategory.DATABASE, "Check database files", test_database_schema)
    
    def _run_permissions_tests(self):
        """Run permissions and security tests"""
        
        def test_root_access():
            if hasattr(os, 'geteuid'):
                is_root = os.geteuid() == 0
                if is_root:
                    return TestResult.WARN, "Running as root (security risk)", {'root': True}
                else:
                    return TestResult.PASS, "Not running as root", {'root': False}
            else:
                return TestResult.SKIP, "Cannot check root status on this platform", {}
        
        def test_sudo_access():
            try:
                result = subprocess.run(['sudo', '-n', 'true'], capture_output=True, timeout=5)
                if result.returncode == 0:
                    return TestResult.PASS, "Sudo access available", {'sudo': True}
                else:
                    return TestResult.WARN, "Sudo access not configured", {'sudo': False}
            except Exception:
                return TestResult.SKIP, "Cannot test sudo access", {}
        
        def test_file_permissions():
            critical_files = ['flaskkk.py', 'system_config.py', 'real_time_monitor.py']
            permission_issues = []
            
            for file in critical_files:
                file_path = Path(file)
                if file_path.exists():
                    if not os.access(file_path, os.R_OK):
                        permission_issues.append(f"{file}: not readable")
                    if file.endswith('.py') and not os.access(file_path, os.X_OK):
                        permission_issues.append(f"{file}: not executable")
            
            if permission_issues:
                return TestResult.WARN, f"Permission issues: {permission_issues}", {'issues': permission_issues}
            else:
                return TestResult.PASS, "File permissions OK", {}
        
        self._run_test("Root Access", TestCategory.PERMISSIONS, "Check root access", test_root_access)
        self._run_test("Sudo Access", TestCategory.PERMISSIONS, "Check sudo access", test_sudo_access)
        self._run_test("File Permissions", TestCategory.PERMISSIONS, "Check file permissions", test_file_permissions)
    
    def _run_services_tests(self):
        """Run service availability tests"""
        
        def test_systemd_availability():
            if not self.is_linux:
                return TestResult.SKIP, "Systemd only available on Linux", {}
            
            try:
                result = subprocess.run(['systemctl', '--version'], capture_output=True, timeout=5)
                if result.returncode == 0:
                    return TestResult.PASS, "Systemd available", {}
                else:
                    return TestResult.WARN, "Systemd not available", {}
            except Exception:
                return TestResult.WARN, "Cannot check systemd", {}
        
        def test_process_management():
            # Check if we can manage processes
            try:
                import psutil
                processes = psutil.pids()
                if len(processes) > 0:
                    return TestResult.PASS, f"Process management available ({len(processes)} processes)", {'process_count': len(processes)}
                else:
                    return TestResult.WARN, "Process management limited", {}
            except ImportError:
                return TestResult.SKIP, "psutil not available", {}
        
        if self.is_linux:
            self._run_test("Systemd", TestCategory.SERVICES, "Check systemd availability", test_systemd_availability)
        self._run_test("Process Management", TestCategory.SERVICES, "Check process management", test_process_management)
    
    def _get_fix_suggestion(self, test_name: str, details: Dict) -> str:
        """Get fix suggestions for failed tests"""
        suggestions = {
            "Python Version": "Upgrade Python: 'sudo apt update && sudo apt install python3.9'",
            "Required Packages": "Install packages: 'pip install -r requirements.txt'",
            "Database Connectors": "Install connector: 'pip install pymysql' or 'pip install mysqlclient'",
            "Internet Connectivity": "Check network connection and firewall settings",
            "DNS Resolution": "Check DNS settings: 'cat /etc/resolv.conf'",
            "Wireless Tools": "Install tools: 'sudo apt install wireless-tools aircrack-ng'",
            "Wireless Interfaces": "Check interface with 'iwconfig' or 'ip link show'",
            "MySQL Service": "Start MySQL: 'sudo systemctl start mysql'",
            "Sudo Access": "Configure sudo: 'sudo visudo' or add user to sudo group",
            "File Permissions": "Fix permissions: 'chmod +x *.py' or 'chmod 644 config files'",
            "Disk Space": "Clean disk space: 'sudo apt autoremove && sudo apt autoclean'"
        }
        
        return suggestions.get(test_name, "Check system documentation for resolution steps")
    
    def generate_report(self, format: str = 'json') -> str:
        """Generate validation report"""
        if format.lower() == 'json':
            return self._generate_json_report()
        elif format.lower() == 'html':
            return self._generate_html_report()
        elif format.lower() == 'text':
            return self._generate_text_report()
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _generate_json_report(self) -> str:
        """Generate JSON report"""
        report = {
            'timestamp': time.time(),
            'system_info': {
                'platform': platform.platform(),
                'system': platform.system(),
                'python_version': platform.python_version()
            },
            'summary': self._get_test_summary(),
            'tests': [asdict(test) for test in self.tests]
        }
        
        return json.dumps(report, indent=2)
    
    def _generate_text_report(self) -> str:
        """Generate text report"""
        lines = []
        lines.append("WiGuard Dashboard System Validation Report")
        lines.append("=" * 50)
        lines.append(f"Platform: {platform.platform()}")
        lines.append(f"Python: {platform.python_version()}")
        lines.append(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        summary = self._get_test_summary()
        lines.append("Summary:")
        lines.append(f"  PASS: {summary['pass']}")
        lines.append(f"  WARN: {summary['warn']}")
        lines.append(f"  FAIL: {summary['fail']}")
        lines.append(f"  SKIP: {summary['skip']}")
        lines.append("")
        
        # Group tests by category
        categories = {}
        for test in self.tests:
            if test.category not in categories:
                categories[test.category] = []
            categories[test.category].append(test)
        
        for category, tests in categories.items():
            lines.append(f"{category.value.title()} Tests:")
            lines.append("-" * 30)
            
            for test in tests:
                status_icon = {
                    TestResult.PASS: "✓",
                    TestResult.WARN: "⚠",
                    TestResult.FAIL: "✗",
                    TestResult.SKIP: "○"
                }[test.result]
                
                lines.append(f"  {status_icon} {test.name}: {test.message}")
                if test.fix_suggestion and test.result != TestResult.PASS:
                    lines.append(f"    → Fix: {test.fix_suggestion}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _get_test_summary(self) -> Dict:
        """Get test result summary"""
        summary = {result.value.lower(): 0 for result in TestResult}
        
        for test in self.tests:
            summary[test.result.value.lower()] += 1
        
        return summary
    
    def save_report(self, filepath: str, format: str = 'json'):
        """Save validation report to file"""
        report = self.generate_report(format)
        
        with open(filepath, 'w') as f:
            f.write(report)
        
        logger.info(f"Validation report saved to {filepath}")

def main():
    """CLI interface for system validator"""
    import argparse
    
    parser = argparse.ArgumentParser(description='WiGuard System Validator')
    parser.add_argument('--categories', nargs='+', 
                      choices=[cat.value for cat in TestCategory],
                      help='Test categories to run')
    parser.add_argument('--auto-fix', action='store_true', help='Attempt automatic fixes')
    parser.add_argument('--format', choices=['json', 'text', 'html'], default='text',
                      help='Report format')
    parser.add_argument('--output', metavar='FILE', help='Save report to file')
    parser.add_argument('--quick', action='store_true', help='Run quick validation only')
    
    args = parser.parse_args()
    
    validator = SystemValidator()
    
    # Determine categories to run
    categories = None
    if args.categories:
        categories = [TestCategory(cat) for cat in args.categories]
    elif args.quick:
        categories = [TestCategory.SYSTEM, TestCategory.PYTHON]
    
    # Run tests
    tests = validator.run_all_tests(categories=categories, auto_fix=args.auto_fix)
    
    # Generate and display/save report
    if args.output:
        validator.save_report(args.output, args.format)
        print(f"Report saved to {args.output}")
    else:
        report = validator.generate_report(args.format)
        print(report)
    
    # Exit with appropriate code
    summary = validator._get_test_summary()
    if summary['fail'] > 0:
        sys.exit(1)
    elif summary['warn'] > 0:
        sys.exit(2)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
