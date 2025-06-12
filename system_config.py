#!/usr/bin/env python3
"""
System compatibility and configuration utilities for WiGuard Dashboard
"""

import os
import sys
import subprocess
import platform
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SystemConfig:
    """System configuration and compatibility checker"""
    
    def __init__(self, base_dir: Optional[str] = None):
        """Initialize system configuration"""
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent
        self.system = platform.system().lower()
        self.is_linux = self.system == 'linux'
        self.is_windows = self.system == 'windows'
        self.is_macos = self.system == 'darwin'
        
        # Load environment variables
        self.load_environment()
        
        # Detect system capabilities
        self.capabilities = self.detect_capabilities()
        
    def load_environment(self):
        """Load environment configuration"""
        env_file = self.base_dir / '.env'
        if env_file.exists():
            try:
                from dotenv import load_dotenv
                load_dotenv(env_file)
                logger.info("Loaded configuration from .env file")
            except ImportError:
                logger.warning("python-dotenv not installed, using system environment only")
        
        # Set defaults for missing environment variables
        self.config = {
            'db_host': os.getenv('DB_HOST', 'localhost'),
            'db_user': os.getenv('DB_USER', 'dashboard'),
            'db_password': os.getenv('DB_PASSWORD', 'securepass'),
            'db_name': os.getenv('DB_NAME', 'security_dashboard'),
            'flask_host': os.getenv('FLASK_HOST', '127.0.0.1'),
            'flask_port': int(os.getenv('FLASK_PORT', '5053')),
            'dashboard_url': os.getenv('DASHBOARD_URL', f"http://127.0.0.1:{os.getenv('FLASK_PORT', '5053')}"),
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'log_dir': os.getenv('LOG_DIR', 'logs'),
            'monitoring_log_file': os.getenv('MONITORING_LOG_FILE', 'monitoring.log'),
            'primary_interface': os.getenv('PRIMARY_INTERFACE', ''),
            'monitor_interface': os.getenv('MONITOR_INTERFACE', ''),
            'bluetooth_interface': os.getenv('BLUETOOTH_INTERFACE', ''),
        }
        
    def get_log_file_path(self) -> str:
        """Get the full path to the monitoring log file"""
        log_dir = self.base_dir / self.config['log_dir']
        log_dir.mkdir(exist_ok=True)
        return str(log_dir / self.config['monitoring_log_file'])
        
    def detect_capabilities(self) -> Dict[str, bool]:
        """Detect system capabilities"""
        capabilities = {
            'wireless_monitoring': False,
            'packet_capture': False,
            'bluetooth': False,
            'gps': False,
            'mysql': False,
            'airmon': False,
            'scapy': False,
        }
        
        # Check for wireless tools
        if self.is_linux:
            capabilities['airmon'] = bool(shutil.which('airmon-ng'))
            capabilities['wireless_monitoring'] = bool(shutil.which('iwconfig'))
            
        # Check for Python packages
        try:
            import scapy
            capabilities['scapy'] = True
            capabilities['packet_capture'] = True
        except ImportError:
            pass
            
        try:
            import MySQLdb
            capabilities['mysql'] = True
        except ImportError:
            try:
                import pymysql
                capabilities['mysql'] = True
            except ImportError:
                pass
                
        # Check for bluetooth
        if self.is_linux:
            capabilities['bluetooth'] = bool(shutil.which('bluetoothctl'))
            
        return capabilities
        
    def get_network_interfaces(self) -> List[Dict[str, str]]:
        """Get available network interfaces"""
        interfaces = []
        
        try:
            import psutil
            for interface, addrs in psutil.net_if_addrs().items():
                interface_info = {
                    'name': interface,
                    'type': 'unknown',
                    'available': True,
                    'description': f"Network interface {interface}"
                }
                
                # Determine interface type
                if 'mon' in interface.lower():
                    interface_info['type'] = 'monitor'
                elif 'wlan' in interface.lower() or 'wifi' in interface.lower():
                    interface_info['type'] = 'wireless'
                elif 'eth' in interface.lower():
                    interface_info['type'] = 'ethernet'
                elif 'bt' in interface.lower() or 'blue' in interface.lower():
                    interface_info['type'] = 'bluetooth'
                elif interface.lower() in ['lo', 'localhost']:
                    interface_info['type'] = 'loopback'
                    
                interfaces.append(interface_info)
                
        except ImportError:
            # Fallback for systems without psutil
            if self.is_linux:
                try:
                    result = subprocess.run(['ip', 'link', 'show'], 
                                          capture_output=True, text=True, timeout=10)
                    for line in result.stdout.split('\n'):
                        if ': ' in line and 'state' in line:
                            interface_name = line.split(': ')[1].split('@')[0]
                            interfaces.append({
                                'name': interface_name,
                                'type': 'unknown',
                                'available': True,
                                'description': f"Network interface {interface_name}"
                            })
                except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                    pass
                    
        return interfaces
        
    def get_best_interface(self, interface_type: str = 'wireless') -> Optional[str]:
        """Get the best available interface for a specific type"""
        interfaces = self.get_network_interfaces()
        
        # Use configured interface if available
        if interface_type == 'wireless' and self.config['primary_interface']:
            return self.config['primary_interface']
        elif interface_type == 'monitor' and self.config['monitor_interface']:
            return self.config['monitor_interface']
        elif interface_type == 'bluetooth' and self.config['bluetooth_interface']:
            return self.config['bluetooth_interface']
            
        # Auto-detect best interface
        for interface in interfaces:
            if interface['type'] == interface_type and interface['available']:
                return interface['name']
                
        # Fallback patterns
        fallback_patterns = {
            'wireless': ['wlan0', 'wifi0', 'wlp*'],
            'monitor': ['wlan0mon', 'mon0'],
            'bluetooth': ['hci0', 'bt0'],
            'ethernet': ['eth0', 'enp*']
        }
        
        if interface_type in fallback_patterns:
            for pattern in fallback_patterns[interface_type]:
                for interface in interfaces:
                    if pattern.replace('*', '') in interface['name']:
                        return interface['name']
                        
        return None
        
    def check_requirements(self) -> Tuple[bool, List[str]]:
        """Check if system meets requirements"""
        issues = []
        
        # Check Python version
        if sys.version_info < (3, 6):
            issues.append("Python 3.6+ required")
            
        # Check required capabilities
        if not self.capabilities['scapy']:
            issues.append("Scapy package not available - packet capture disabled")
            
        if not self.capabilities['mysql']:
            issues.append("MySQL connector not available - database features disabled")
            
        if self.is_linux and not self.capabilities['wireless_monitoring']:
            issues.append("Wireless monitoring tools not available")
            
        # Check for interfaces
        interfaces = self.get_network_interfaces()
        if not interfaces:
            issues.append("No network interfaces detected")
            
        return len(issues) == 0, issues
        
    def create_monitor_interface(self, base_interface: str) -> Optional[str]:
        """Create monitor mode interface"""
        if not self.is_linux or not self.capabilities['airmon']:
            logger.warning("Monitor mode creation not supported on this system")
            return None
            
        try:
            # Try to create monitor interface
            result = subprocess.run(['sudo', 'airmon-ng', 'start', base_interface],
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # Extract monitor interface name from output
                for line in result.stdout.split('\n'):
                    if 'monitor mode enabled' in line.lower():
                        parts = line.split()
                        for part in parts:
                            if 'mon' in part:
                                logger.info(f"Created monitor interface: {part}")
                                return part
                                
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, PermissionError) as e:
            logger.error(f"Failed to create monitor interface: {e}")
            
        return None
        
    def setup_environment(self) -> bool:
        """Setup the runtime environment"""
        try:
            # Create necessary directories
            (self.base_dir / self.config['log_dir']).mkdir(exist_ok=True)
            
            # Set up logging
            log_level = getattr(logging, self.config['log_level'].upper(), logging.INFO)
            logging.getLogger().setLevel(log_level)
            
            logger.info(f"WiGuard Dashboard initialized on {platform.system()} {platform.release()}")
            logger.info(f"Base directory: {self.base_dir}")
            logger.info(f"Capabilities: {self.capabilities}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup environment: {e}")
            return False
            
    def get_system_info(self) -> Dict:
        """Get comprehensive system information"""
        return {
            'platform': platform.platform(),
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'capabilities': self.capabilities,
            'interfaces': self.get_network_interfaces(),
            'base_dir': str(self.base_dir),
            'config': self.config
        }

# Global system configuration instance
system_config = SystemConfig()

def get_config():
    """Get the global system configuration"""
    return system_config

if __name__ == "__main__":
    # System check when run directly
    config = SystemConfig()
    
    print("WiGuard Dashboard System Check")
    print("=" * 40)
    print(f"Platform: {platform.platform()}")
    print(f"Python: {platform.python_version()}")
    print()
    
    print("Capabilities:")
    for capability, available in config.capabilities.items():
        status = "✓" if available else "✗"
        print(f"  {status} {capability}")
    print()
    
    print("Network Interfaces:")
    interfaces = config.get_network_interfaces()
    if interfaces:
        for interface in interfaces:
            print(f"  • {interface['name']} ({interface['type']})")
    else:
        print("  No interfaces detected")
    print()
    
    success, issues = config.check_requirements()
    print("Requirements Check:")
    if success:
        print("  ✓ All requirements met")
    else:
        print("  Issues found:")
        for issue in issues:
            print(f"    • {issue}")
    print()
    
    print("Recommended Interfaces:")
    for iface_type in ['wireless', 'monitor']:
        best = config.get_best_interface(iface_type)
        print(f"  {iface_type}: {best or 'None available'}")
