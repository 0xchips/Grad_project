#!/usr/bin/env python3
"""
Advanced Interface Manager for WiGuard Dashboard
Provides comprehensive network interface management across platforms
"""

import os
import sys
import subprocess
import platform
import time
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, NamedTuple
from dataclasses import dataclass
from enum import Enum
import threading
import signal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InterfaceType(Enum):
    ETHERNET = "ethernet"
    WIRELESS = "wireless" 
    MONITOR = "monitor"
    BLUETOOTH = "bluetooth"
    LOOPBACK = "loopback"
    VIRTUAL = "virtual"
    UNKNOWN = "unknown"

class InterfaceState(Enum):
    UP = "up"
    DOWN = "down"
    DORMANT = "dormant"
    UNKNOWN = "unknown"

@dataclass
class InterfaceInfo:
    name: str
    type: InterfaceType
    state: InterfaceState
    mac_address: Optional[str] = None
    ip_addresses: List[str] = None
    mtu: Optional[int] = None
    driver: Optional[str] = None
    capabilities: List[str] = None
    statistics: Dict = None
    wireless_info: Dict = None
    monitor_capable: bool = False
    injection_capable: bool = False
    
    def __post_init__(self):
        if self.ip_addresses is None:
            self.ip_addresses = []
        if self.capabilities is None:
            self.capabilities = []
        if self.statistics is None:
            self.statistics = {}
        if self.wireless_info is None:
            self.wireless_info = {}

class InterfaceManager:
    """Advanced network interface management"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.is_linux = self.system == 'linux'
        self.is_windows = self.system == 'windows'
        self.is_macos = self.system == 'darwin'
        self.interfaces = {}
        self.monitoring_thread = None
        self.monitoring_active = False
        self._update_lock = threading.Lock()
        
    def discover_interfaces(self) -> Dict[str, InterfaceInfo]:
        """Discover all network interfaces"""
        interfaces = {}
        
        if self.is_linux:
            interfaces.update(self._discover_linux_interfaces())
        elif self.is_macos:
            interfaces.update(self._discover_macos_interfaces())
        elif self.is_windows:
            interfaces.update(self._discover_windows_interfaces())
            
        # Update internal cache
        with self._update_lock:
            self.interfaces = interfaces
            
        return interfaces
    
    def _discover_linux_interfaces(self) -> Dict[str, InterfaceInfo]:
        """Discover interfaces on Linux systems"""
        interfaces = {}
        
        # Method 1: Parse /sys/class/net
        try:
            net_path = Path('/sys/class/net')
            if net_path.exists():
                for iface_path in net_path.iterdir():
                    if iface_path.is_dir():
                        interface = self._parse_linux_interface(iface_path)
                        if interface:
                            interfaces[interface.name] = interface
        except Exception as e:
            logger.warning(f"Failed to parse /sys/class/net: {e}")
            
        # Method 2: Use ip command as fallback
        if not interfaces:
            interfaces.update(self._discover_interfaces_ip_command())
            
        return interfaces
    
    def _parse_linux_interface(self, iface_path: Path) -> Optional[InterfaceInfo]:
        """Parse Linux interface from /sys/class/net"""
        try:
            name = iface_path.name
            
            # Read basic info
            operstate_file = iface_path / 'operstate'
            state = InterfaceState.UNKNOWN
            if operstate_file.exists():
                operstate = operstate_file.read_text().strip().lower()
                state = InterfaceState.UP if operstate == 'up' else InterfaceState.DOWN
                
            # Read MAC address
            mac_file = iface_path / 'address'
            mac_address = None
            if mac_file.exists():
                mac_address = mac_file.read_text().strip()
                
            # Read MTU
            mtu_file = iface_path / 'mtu'
            mtu = None
            if mtu_file.exists():
                try:
                    mtu = int(mtu_file.read_text().strip())
                except ValueError:
                    pass
                    
            # Determine interface type
            interface_type = self._determine_interface_type(name, iface_path)
            
            # Get wireless capabilities if wireless
            wireless_info = {}
            monitor_capable = False
            injection_capable = False
            
            if interface_type == InterfaceType.WIRELESS:
                wireless_info = self._get_wireless_info_linux(name)
                monitor_capable = self._check_monitor_capability_linux(name)
                injection_capable = self._check_injection_capability_linux(name)
                
            # Get IP addresses
            ip_addresses = self._get_ip_addresses_linux(name)
            
            # Get statistics
            statistics = self._get_interface_statistics_linux(iface_path)
            
            return InterfaceInfo(
                name=name,
                type=interface_type,
                state=state,
                mac_address=mac_address,
                ip_addresses=ip_addresses,
                mtu=mtu,
                capabilities=self._get_interface_capabilities_linux(name),
                statistics=statistics,
                wireless_info=wireless_info,
                monitor_capable=monitor_capable,
                injection_capable=injection_capable
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse interface {iface_path.name}: {e}")
            return None
    
    def _determine_interface_type(self, name: str, iface_path: Path = None) -> InterfaceType:
        """Determine interface type from name and system info"""
        name_lower = name.lower()
        
        # Check for specific patterns
        if 'mon' in name_lower and ('wlan' in name_lower or 'wifi' in name_lower):
            return InterfaceType.MONITOR
        elif 'wlan' in name_lower or 'wifi' in name_lower or 'wlp' in name_lower:
            return InterfaceType.WIRELESS
        elif 'eth' in name_lower or 'enp' in name_lower or 'ens' in name_lower:
            return InterfaceType.ETHERNET
        elif name_lower in ['lo', 'localhost']:
            return InterfaceType.LOOPBACK
        elif 'bt' in name_lower or 'blue' in name_lower or 'hci' in name_lower:
            return InterfaceType.BLUETOOTH
        elif 'vir' in name_lower or 'tap' in name_lower or 'tun' in name_lower:
            return InterfaceType.VIRTUAL
            
        # Check wireless directory for more accurate detection
        if iface_path and self.is_linux:
            wireless_path = iface_path / 'wireless'
            if wireless_path.exists():
                return InterfaceType.WIRELESS
                
        return InterfaceType.UNKNOWN
    
    def _get_wireless_info_linux(self, interface: str) -> Dict:
        """Get wireless information for Linux interface"""
        info = {}
        
        try:
            # Try iwconfig first
            result = subprocess.run(['iwconfig', interface], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                info.update(self._parse_iwconfig_output(result.stdout))
        except Exception:
            pass
            
        try:
            # Try iw dev interface info
            result = subprocess.run(['iw', 'dev', interface, 'info'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                info.update(self._parse_iw_info_output(result.stdout))
        except Exception:
            pass
            
        return info
    
    def _check_monitor_capability_linux(self, interface: str) -> bool:
        """Check if interface supports monitor mode"""
        try:
            # Method 1: Check with iw
            result = subprocess.run(['iw', 'phy'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and 'monitor' in result.stdout.lower():
                return True
                
            # Method 2: Try to get interface capabilities
            result = subprocess.run(['iw', 'dev', interface, 'info'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                # Look for wiphy information
                for line in result.stdout.split('\n'):
                    if 'wiphy' in line.lower():
                        wiphy = line.split()[-1]
                        # Check wiphy capabilities
                        wiphy_result = subprocess.run(['iw', 'phy', wiphy, 'info'], 
                                                    capture_output=True, text=True, timeout=5)
                        if wiphy_result.returncode == 0 and 'monitor' in wiphy_result.stdout.lower():
                            return True
                            
        except Exception as e:
            logger.debug(f"Monitor capability check failed for {interface}: {e}")
            
        return False
    
    def _check_injection_capability_linux(self, interface: str) -> bool:
        """Check if interface supports packet injection"""
        try:
            # This is a simplified check - proper injection testing requires more complex methods
            result = subprocess.run(['iw', 'list'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                # Look for TX power control and other injection indicators
                return 'tx power' in result.stdout.lower()
        except Exception:
            pass
        return False
    
    def create_monitor_interface(self, base_interface: str, monitor_name: str = None) -> Optional[str]:
        """Create monitor mode interface"""
        if not monitor_name:
            monitor_name = f"{base_interface}mon"
            
        if not self.is_linux:
            logger.error("Monitor interface creation only supported on Linux")
            return None
            
        try:
            # Method 1: Try airmon-ng
            if subprocess.run(['which', 'airmon-ng'], capture_output=True).returncode == 0:
                result = subprocess.run(['sudo', 'airmon-ng', 'start', base_interface],
                                      capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    # Parse output to find monitor interface name
                    for line in result.stdout.split('\n'):
                        if 'monitor mode' in line.lower() and 'enabled' in line.lower():
                            parts = line.split()
                            for part in parts:
                                if 'mon' in part:
                                    logger.info(f"Created monitor interface: {part}")
                                    return part
                                    
            # Method 2: Try iw manually
            # First, bring interface down
            subprocess.run(['sudo', 'ip', 'link', 'set', base_interface, 'down'], 
                         capture_output=True, timeout=10)
            
            # Add monitor interface
            result = subprocess.run(['sudo', 'iw', 'dev', base_interface, 'interface', 'add', 
                                   monitor_name, 'type', 'monitor'],
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                # Bring monitor interface up
                subprocess.run(['sudo', 'ip', 'link', 'set', monitor_name, 'up'],
                             capture_output=True, timeout=10)
                logger.info(f"Created monitor interface: {monitor_name}")
                return monitor_name
                
        except Exception as e:
            logger.error(f"Failed to create monitor interface: {e}")
            
        return None
    
    def get_best_interface(self, interface_type: InterfaceType, 
                          requirements: Dict = None) -> Optional[InterfaceInfo]:
        """Get the best interface matching criteria"""
        interfaces = self.discover_interfaces()
        candidates = []
        
        # Filter by type
        for iface in interfaces.values():
            if iface.type == interface_type:
                candidates.append(iface)
                
        if not candidates:
            return None
            
        # Apply requirements filtering
        if requirements:
            filtered = []
            for iface in candidates:
                if self._meets_requirements(iface, requirements):
                    filtered.append(iface)
            candidates = filtered
            
        if not candidates:
            return None
            
        # Sort by priority (up state, has IP, etc.)
        def priority_score(iface):
            score = 0
            if iface.state == InterfaceState.UP:
                score += 10
            if iface.ip_addresses:
                score += 5
            if iface.monitor_capable and interface_type == InterfaceType.MONITOR:
                score += 3
            if iface.injection_capable:
                score += 2
            return score
            
        candidates.sort(key=priority_score, reverse=True)
        return candidates[0]
    
    def _meets_requirements(self, interface: InterfaceInfo, requirements: Dict) -> bool:
        """Check if interface meets requirements"""
        if requirements.get('monitor_capable') and not interface.monitor_capable:
            return False
        if requirements.get('injection_capable') and not interface.injection_capable:
            return False
        if requirements.get('state') == 'up' and interface.state != InterfaceState.UP:
            return False
        return True
    
    def start_monitoring(self, callback=None, interval=5):
        """Start monitoring interface changes"""
        if self.monitoring_active:
            return
            
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(callback, interval),
            daemon=True
        )
        self.monitoring_thread.start()
        logger.info("Interface monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring interface changes"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=10)
        logger.info("Interface monitoring stopped")
    
    def _monitoring_loop(self, callback, interval):
        """Monitoring loop for interface changes"""
        last_interfaces = {}
        
        while self.monitoring_active:
            try:
                current_interfaces = self.discover_interfaces()
                
                # Detect changes
                changes = self._detect_changes(last_interfaces, current_interfaces)
                
                if changes and callback:
                    callback(changes)
                    
                last_interfaces = current_interfaces.copy()
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Interface monitoring error: {e}")
                time.sleep(interval)
    
    def _detect_changes(self, old_interfaces, new_interfaces) -> Dict:
        """Detect interface changes"""
        changes = {
            'added': [],
            'removed': [],
            'modified': []
        }
        
        old_names = set(old_interfaces.keys())
        new_names = set(new_interfaces.keys())
        
        # Detect added/removed
        changes['added'] = list(new_names - old_names)
        changes['removed'] = list(old_names - new_names)
        
        # Detect modified
        for name in old_names & new_names:
            old_iface = old_interfaces[name]
            new_iface = new_interfaces[name]
            
            if (old_iface.state != new_iface.state or 
                old_iface.ip_addresses != new_iface.ip_addresses):
                changes['modified'].append(name)
                
        return changes
    
    # Additional helper methods for different platforms...
    def _discover_interfaces_ip_command(self) -> Dict[str, InterfaceInfo]:
        """Discover interfaces using ip command as fallback"""
        interfaces = {}
        try:
            result = subprocess.run(['ip', 'link', 'show'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if ': ' in line and 'state' in line:
                        parts = line.split(': ')
                        if len(parts) >= 2:
                            interface_name = parts[1].split('@')[0]
                            
                            # Determine state
                            state = InterfaceState.UP if 'state UP' in line else InterfaceState.DOWN
                            
                            interfaces[interface_name] = InterfaceInfo(
                                name=interface_name,
                                type=self._determine_interface_type(interface_name),
                                state=state,
                                ip_addresses=self._get_ip_addresses_linux(interface_name),
                                capabilities=[],
                                statistics={},
                                monitor_capable=False,
                                injection_capable=False
                            )
        except Exception as e:
            logger.warning(f"ip command failed: {e}")
        
        return interfaces
    
    def _get_ip_addresses_linux(self, interface: str) -> List[str]:
        """Get IP addresses for Linux interface"""
        addresses = []
        try:
            result = subprocess.run(['ip', 'addr', 'show', interface], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'inet ' in line:
                        addr = line.strip().split()[1].split('/')[0]
                        addresses.append(addr)
        except Exception:
            pass
        return addresses
    
    def _get_interface_statistics_linux(self, iface_path: Path) -> Dict:
        """Get interface statistics from /sys/class/net"""
        stats = {}
        try:
            stats_path = iface_path / 'statistics'
            if stats_path.exists():
                for stat_file in stats_path.iterdir():
                    if stat_file.is_file():
                        try:
                            value = int(stat_file.read_text().strip())
                            stats[stat_file.name] = value
                        except (ValueError, OSError):
                            pass
        except Exception:
            pass
        return stats
    
    def _get_interface_capabilities_linux(self, interface: str) -> List[str]:
        """Get interface capabilities"""
        capabilities = []
        try:
            # Check wireless capabilities
            result = subprocess.run(['iw', 'dev', interface, 'info'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                if 'type monitor' in result.stdout.lower():
                    capabilities.append('monitor')
                if 'type managed' in result.stdout.lower():
                    capabilities.append('managed')
        except Exception:
            pass
        return capabilities
    
    def _parse_iwconfig_output(self, output: str) -> Dict:
        """Parse iwconfig output"""
        info = {}
        for line in output.split('\n'):
            line = line.strip()
            if 'ESSID:' in line:
                essid = line.split('ESSID:')[1].strip().strip('"')
                if essid != 'off/any':
                    info['ssid'] = essid
            elif 'Mode:' in line:
                mode = line.split('Mode:')[1].split()[0]
                info['mode'] = mode
            elif 'Frequency:' in line:
                freq = line.split('Frequency:')[1].split()[0]
                info['frequency'] = freq
        return info
    
    def _parse_iw_info_output(self, output: str) -> Dict:
        """Parse iw dev info output"""
        info = {}
        for line in output.split('\n'):
            line = line.strip()
            if line.startswith('type '):
                info['type'] = line.split()[1]
            elif line.startswith('channel '):
                info['channel'] = line.split()[1]
        return info

def main():
    """CLI interface for interface manager"""
    import argparse
    
    parser = argparse.ArgumentParser(description='WiGuard Interface Manager')
    parser.add_argument('--discover', action='store_true', help='Discover all interfaces')
    parser.add_argument('--monitor', action='store_true', help='Start interface monitoring')
    parser.add_argument('--create-monitor', metavar='INTERFACE', help='Create monitor interface')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    
    args = parser.parse_args()
    
    manager = InterfaceManager()
    
    if args.discover:
        interfaces = manager.discover_interfaces()
        
        if args.json:
            print(json.dumps(manager.get_system_info(), indent=2))
        else:
            print("Discovered Network Interfaces:")
            print("=" * 50)
            for name, iface in interfaces.items():
                print(f"Interface: {name}")
                print(f"  Type: {iface.type.value}")
                print(f"  State: {iface.state.value}")
                print(f"  MAC: {iface.mac_address or 'N/A'}")
                print(f"  IPs: {', '.join(iface.ip_addresses) or 'None'}")
                if iface.type == InterfaceType.WIRELESS:
                    print(f"  Monitor Capable: {iface.monitor_capable}")
                    print(f"  Injection Capable: {iface.injection_capable}")
                    if iface.wireless_info:
                        print(f"  Wireless Info: {iface.wireless_info}")
                print()
    
    elif args.create_monitor:
        monitor_iface = manager.create_monitor_interface(args.create_monitor)
        if monitor_iface:
            print(f"Created monitor interface: {monitor_iface}")
        else:
            print(f"Failed to create monitor interface for {args.create_monitor}")
    
    elif args.monitor:
        def change_callback(changes):
            print(f"Interface changes detected: {changes}")
        
        print("Starting interface monitoring... Press Ctrl+C to stop")
        manager.start_monitoring(callback=change_callback)
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            manager.stop_monitoring()
            print("\nMonitoring stopped")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
