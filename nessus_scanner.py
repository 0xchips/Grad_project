#!/usr/bin/env python3
"""
Nessus Scanner Integration Module
Handles Nessus installation, configuration, and vulnerability scanning
"""

import os
import sys
import json
import time
import requests
import subprocess
import logging
from typing import Dict, List, Optional, Tuple
from urllib3.exceptions import InsecureRequestWarning
import urllib3

# Import fallback scanner
try:
    from testing.fallback_scanner import FallbackScanner
except ImportError:
    FallbackScanner = None

# Disable SSL warnings for Nessus API
urllib3.disable_warnings(InsecureRequestWarning)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NessusScanner:
    def __init__(self, host='localhost', port=8834, username='admin', password='admin123'):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.base_url = f"https://{host}:{port}"
        self.session = requests.Session()
        self.session.verify = False  # Disable SSL verification for local Nessus
        self.token = None
        self.scan_id = None
        
        # Initialize fallback scanner
        self.fallback_scanner = FallbackScanner() if FallbackScanner else None
        
    def is_nessus_installed(self) -> bool:
        """Check if Nessus is installed on the system"""
        try:
            result = subprocess.run(['which', 'nessusd'], capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False
    
    def install_nessus(self) -> bool:
        """Install Nessus scanner"""
        try:
            logger.info("Starting Nessus installation...")
            
            # Check if running on Kali Linux
            if not os.path.exists('/etc/debian_version'):
                logger.error("This installation script is designed for Debian/Kali Linux")
                return False
            
            # Download and install Nessus
            commands = [
                # Update package list
                ['sudo', 'apt', 'update'],
                
                # Install dependencies
                ['sudo', 'apt', 'install', '-y', 'curl', 'wget'],
                
                # Download Nessus (adjust URL for latest version)
                ['wget', 'https://www.tenable.com/downloads/api/v1/public/pages/nessus/downloads/17204/download?i_agree_to_tenable_license_agreement=true', 
                 '-O', '/tmp/Nessus-latest-debian9_amd64.deb'],
                
                # Install Nessus package
                ['sudo', 'dpkg', '-i', '/tmp/Nessus-latest-debian9_amd64.deb']
            ]
            
            for cmd in commands:
                logger.info(f"Executing: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.error(f"Command failed: {result.stderr}")
                    if 'dpkg' in cmd:  # Try to fix broken packages
                        subprocess.run(['sudo', 'apt', '--fix-broken', 'install'], capture_output=True)
                        continue
                    return False
            
            # Start Nessus service
            subprocess.run(['sudo', 'systemctl', 'enable', 'nessusd'], capture_output=True)
            subprocess.run(['sudo', 'systemctl', 'start', 'nessusd'], capture_output=True)
            
            logger.info("Nessus installation completed. Waiting for service to start...")
            time.sleep(30)  # Wait for Nessus to start
            
            return True
            
        except Exception as e:
            logger.error(f"Nessus installation failed: {str(e)}")
            return False
    
    def wait_for_nessus_ready(self, timeout=300) -> bool:
        """Wait for Nessus to be ready"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = self.session.get(f"{self.base_url}/session", timeout=10)
                if response.status_code == 200:
                    logger.info("Nessus is ready!")
                    return True
            except Exception:
                pass
            logger.info("Waiting for Nessus to start...")
            time.sleep(10)
        
        logger.error("Nessus failed to start within timeout period")
        return False
    
    def create_admin_user(self) -> bool:
        """Create admin user for Nessus"""
        try:
            # Check if we need to create initial user
            response = self.session.get(f"{self.base_url}/users")
            if response.status_code == 401:
                # Initial setup required
                setup_data = {
                    'username': self.username,
                    'password': self.password,
                    'email': 'admin@localhost.local'
                }
                
                response = self.session.post(f"{self.base_url}/users", json=setup_data)
                if response.status_code == 200:
                    logger.info("Admin user created successfully")
                    return True
                else:
                    logger.error(f"Failed to create admin user: {response.text}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating admin user: {str(e)}")
            return False
    
    def authenticate(self) -> bool:
        """Authenticate with Nessus API"""
        try:
            auth_data = {
                'username': self.username,
                'password': self.password
            }
            
            response = self.session.post(f"{self.base_url}/session", json=auth_data)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('token')
                self.session.headers.update({'X-Cookie': f'token={self.token}'})
                logger.info("Authentication successful")
                return True
            else:
                logger.error(f"Authentication failed: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return False
    
    def get_scan_templates(self) -> List[Dict]:
        """Get available scan templates"""
        try:
            response = self.session.get(f"{self.base_url}/editor/scan/templates")
            if response.status_code == 200:
                return response.json().get('templates', [])
            return []
        except Exception as e:
            logger.error(f"Error getting scan templates: {str(e)}")
            return []
    
    def create_scan(self, name: str, targets: str, template_uuid: str = None) -> Optional[int]:
        """Create a new vulnerability scan"""
        try:
            # Get default template if none specified
            if not template_uuid:
                templates = self.get_scan_templates()
                # Use basic network scan template
                for template in templates:
                    if 'basic' in template.get('name', '').lower():
                        template_uuid = template.get('uuid')
                        break
                
                if not template_uuid and templates:
                    template_uuid = templates[0].get('uuid')
            
            scan_data = {
                'uuid': template_uuid,
                'settings': {
                    'name': name,
                    'targets': targets,
                    'enabled': 'true',
                    'launch': 'ONETIME'
                }
            }
            
            response = self.session.post(f"{self.base_url}/scans", json=scan_data)
            
            if response.status_code == 200:
                scan_info = response.json()
                self.scan_id = scan_info['scan']['id']
                logger.info(f"Scan created with ID: {self.scan_id}")
                return self.scan_id
            else:
                logger.error(f"Failed to create scan: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating scan: {str(e)}")
            return None
    
    def launch_scan(self, scan_id: int = None) -> bool:
        """Launch a vulnerability scan"""
        try:
            if not scan_id:
                scan_id = self.scan_id
            
            if not scan_id:
                logger.error("No scan ID available")
                return False
            
            response = self.session.post(f"{self.base_url}/scans/{scan_id}/launch")
            
            if response.status_code == 200:
                logger.info(f"Scan {scan_id} launched successfully")
                return True
            else:
                logger.error(f"Failed to launch scan: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error launching scan: {str(e)}")
            return False
    
    def get_scan_status(self, scan_id: int = None) -> Dict:
        """Get scan status and progress"""
        try:
            # Check if fallback scanner has an active scan
            if self.fallback_scanner and self.fallback_scanner.scan_status != 'idle':
                return self.fallback_scanner.get_scan_status()
            
            # Otherwise check Nessus scan
            if not scan_id:
                scan_id = self.scan_id
            
            if not scan_id:
                return {'status': 'error', 'message': 'No scan ID available'}
            
            response = self.session.get(f"{self.base_url}/scans/{scan_id}")
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'status': data.get('info', {}).get('status', 'unknown'),
                    'progress': data.get('info', {}).get('progress', 0),
                    'start_time': data.get('info', {}).get('timestamp'),
                    'scan_id': scan_id
                }
            else:
                return {'status': 'error', 'message': f'Failed to get scan status: {response.text}'}
                
        except Exception as e:
            return {'status': 'error', 'message': f'Error getting scan status: {str(e)}'}
    
    def get_scan_results(self, scan_id: int = None) -> Dict:
        """Get scan results"""
        try:
            if not scan_id:
                scan_id = self.scan_id
            
            if not scan_id:
                return {'error': 'No scan ID available'}
            
            response = self.session.get(f"{self.base_url}/scans/{scan_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract vulnerability summary
                vulnerabilities = data.get('vulnerabilities', [])
                hosts = data.get('hosts', [])
                
                summary = {
                    'total_hosts': len(hosts),
                    'total_vulnerabilities': len(vulnerabilities),
                    'critical': len([v for v in vulnerabilities if v.get('severity') == 4]),
                    'high': len([v for v in vulnerabilities if v.get('severity') == 3]),
                    'medium': len([v for v in vulnerabilities if v.get('severity') == 2]),
                    'low': len([v for v in vulnerabilities if v.get('severity') == 1]),
                    'info': len([v for v in vulnerabilities if v.get('severity') == 0]),
                    'scan_status': data.get('info', {}).get('status', 'unknown'),
                    'hosts': hosts,
                    'vulnerabilities': vulnerabilities[:50]  # Limit for performance
                }
                
                return summary
            else:
                return {'error': f'Failed to get scan results: {response.text}'}
                
        except Exception as e:
            return {'error': f'Error getting scan results: {str(e)}'}
    
    def export_scan_report(self, scan_id: int = None, format_type: str = 'pdf') -> Optional[str]:
        """Export scan report"""
        try:
            # Check if we should use fallback scanner report
            if self.fallback_scanner and (not scan_id or str(scan_id).startswith('fallback_')):
                logger.info("Generating fallback scanner report")
                return self.fallback_scanner.generate_report(format_type)
            
            if not scan_id:
                scan_id = self.scan_id
            
            if not scan_id:
                logger.error("No scan ID available")
                return None
            
            # Request report export from Nessus
            export_data = {
                'format': format_type,
                'chapters': 'vuln_hosts_summary;vuln_by_host;compliance_exec;remediations;vuln_by_plugin;compliance'
            }
            
            response = self.session.post(f"{self.base_url}/scans/{scan_id}/export", json=export_data)
            
            if response.status_code == 200:
                export_info = response.json()
                file_id = export_info.get('file')
                
                # Wait for export to complete
                while True:
                    status_response = self.session.get(f"{self.base_url}/scans/{scan_id}/export/{file_id}/status")
                    if status_response.status_code == 200:
                        status = status_response.json().get('status')
                        if status == 'ready':
                            break
                        elif status == 'error':
                            logger.error("Export failed")
                            return None
                    time.sleep(2)
                
                # Download the report
                download_response = self.session.get(f"{self.base_url}/scans/{scan_id}/export/{file_id}/download")
                if download_response.status_code == 200:
                    filename = f"nessus_scan_{scan_id}_{int(time.time())}.{format_type}"
                    filepath = os.path.join('/tmp', filename)
                    
                    with open(filepath, 'wb') as f:
                        f.write(download_response.content)
                    
                    logger.info(f"Report exported to: {filepath}")
                    return filepath
                    
            return None
            
        except Exception as e:
            logger.error(f"Error exporting report: {str(e)}")
            return None
    
    def setup_nessus(self) -> bool:
        """Complete Nessus setup process"""
        try:
            # Check if Nessus is installed
            if not self.is_nessus_installed():
                logger.info("Nessus not found. Installing...")
                if not self.install_nessus():
                    return False
            
            # Wait for Nessus to be ready
            if not self.wait_for_nessus_ready():
                return False
            
            # Create admin user if needed
            if not self.create_admin_user():
                return False
            
            # Authenticate
            if not self.authenticate():
                return False
            
            logger.info("Nessus setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Nessus setup failed: {str(e)}")
            return False
    
    def run_full_scan(self, targets: str = "192.168.1.0/24") -> Dict:
        """Run a complete vulnerability scan"""
        try:
            # Check if Nessus is available and working
            if self.is_nessus_installed():
                logger.info("Nessus detected, attempting full Nessus scan...")
                
                # Setup Nessus if needed
                if not self.setup_nessus():
                    logger.warning("Nessus setup failed, falling back to alternative scanning")
                    return self._run_fallback_scan(targets)
                
                # Create and launch scan
                scan_name = f"WiGuard_Full_Scan_{int(time.time())}"
                scan_id = self.create_scan(scan_name, targets)
                
                if not scan_id:
                    logger.warning("Failed to create Nessus scan, falling back to alternative scanning")
                    return self._run_fallback_scan(targets)
                
                if not self.launch_scan(scan_id):
                    logger.warning("Failed to launch Nessus scan, falling back to alternative scanning")
                    return self._run_fallback_scan(targets)
                
                return {
                    'success': True,
                    'scan_id': scan_id,
                    'message': f'Nessus vulnerability scan started for targets: {targets}',
                    'scan_name': scan_name,
                    'scanner_type': 'nessus'
                }
            else:
                logger.info("Nessus not available, using fallback security scanning...")
                return self._run_fallback_scan(targets)
            
        except Exception as e:
            logger.error(f"Nessus scan failed: {str(e)}, falling back to alternative scanning")
            return self._run_fallback_scan(targets)
    
    def _run_fallback_scan(self, targets: str) -> Dict:
        """Run fallback security scan when Nessus is not available"""
        try:
            if not self.fallback_scanner:
                return {'error': 'Neither Nessus nor fallback scanner is available'}
            
            scan_name = f"WiGuard_Security_Scan_{int(time.time())}"
            result = self.fallback_scanner.start_scan(targets, scan_name)
            
            if result.get('success'):
                result['scanner_type'] = 'fallback'
                result['message'] = f'Security scan initiated using built-in tools for targets: {targets}'
                logger.info("Fallback security scan started successfully")
            
            return result
            
        except Exception as e:
            logger.error(f"Fallback scan failed: {str(e)}")
            return {'error': f'All scanning methods failed: {str(e)}'}
    
    def stop_scan(self) -> Dict:
        """Stop any running scan (Nessus or fallback)"""
        try:
            # First try to stop fallback scanner if it's running
            if self.fallback_scanner and self.fallback_scanner.scan_status == 'running':
                return self.fallback_scanner.stop_scan()
                
            # Then try to stop Nessus scan if one is active
            if self.is_nessus_installed():
                # Get current scans
                scan_status = self.get_scan_status()
                if scan_status.get('status') == 'running' and scan_status.get('scan_id'):
                    scan_id = scan_status.get('scan_id')
                    if self.stop_nessus_scan(scan_id):
                        return {
                            'success': True,
                            'message': f'Nessus scan {scan_id} stopped successfully'
                        }
            
            return {
                'message': 'No active scan found to stop'
            }
            
        except Exception as e:
            logger.error(f"Error stopping scan: {str(e)}")
            return {'error': f'Failed to stop scan: {str(e)}'}
    
    def stop_nessus_scan(self, scan_id: int) -> bool:
        """Stop a running Nessus scan"""
        try:
            if not self.api_client:
                return False
                
            self.api_client.scan_stop(scan_id)
            return True
        except:
            return False
    
def main():
    """Main function for testing"""
    scanner = NessusScanner()
    
    # Test installation and setup
    if scanner.setup_nessus():
        print("Nessus setup successful!")
        
        # Run a test scan
        result = scanner.run_full_scan("127.0.0.1")
        print(f"Scan result: {result}")
    else:
        print("Nessus setup failed!")

if __name__ == "__main__":
    main()
