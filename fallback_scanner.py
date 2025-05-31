#!/usr/bin/env python3
"""
CyberShield Fallback Scanner
Alternative vulnerability scanning when Nessus is not available
Uses built-in Kali Linux security tools
"""

import os
import sys
import json
import time
import subprocess
import logging
import threading
from typing import Dict, List, Optional
import ipaddress
import socket

logger = logging.getLogger(__name__)

class FallbackScanner:
    def __init__(self):
        self.scan_id = None
        self.scan_status = 'idle'
        self.scan_progress = 0
        self.scan_results = {}
        self.scan_thread = None
        self._stop_scan_flag = False  # Flag to signal scan termination
        
    def is_tool_available(self, tool_name: str) -> bool:
        """Check if a security tool is available"""
        try:
            result = subprocess.run(['which', tool_name], capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False
    
    def get_available_tools(self) -> Dict[str, bool]:
        """Get list of available security tools"""
        tools = {
            'nmap': self.is_tool_available('nmap'),
            'nikto': self.is_tool_available('nikto'),
            'dirb': self.is_tool_available('dirb'),
            'sslscan': self.is_tool_available('sslscan'),
            'whatweb': self.is_tool_available('whatweb'),
            'enum4linux': self.is_tool_available('enum4linux'),
            'netdiscover': self.is_tool_available('netdiscover')
        }
        return tools
    
    def run_nmap_scan(self, targets: str) -> Dict:
        """Run comprehensive nmap vulnerability scan"""
        try:
            logger.info(f"Running nmap scan on {targets}")
            self.scan_progress = 20
            
            if self._stop_scan_flag:
                return {'error': 'Scan was stopped'}
            
            # Comprehensive nmap scan with vulnerability detection
            cmd = [
                'nmap', '-sS', '-sU', '-T4', '-A', '-v',
                '--script=vuln,safe,discovery',
                '--script-timeout=30s',
                '--host-timeout=300s',
                '-oX', '/tmp/nmap_results.xml',
                targets
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
            self.scan_progress = 60
            
            # Parse results
            return self.parse_nmap_results(result.stdout, result.stderr)
            
        except subprocess.TimeoutExpired:
            logger.error("Nmap scan timed out")
            return {'error': 'Scan timed out after 30 minutes'}
        except Exception as e:
            logger.error(f"Nmap scan failed: {str(e)}")
            return {'error': f'Nmap scan failed: {str(e)}'}
    
    def parse_nmap_results(self, stdout: str, stderr: str) -> Dict:
        """Parse nmap output and categorize findings"""
        results = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'info': 0,
            'hosts_scanned': 0,
            'hosts_up': 0,
            'open_ports': 0,
            'vulnerabilities': [],
            'services': [],
            'raw_output': stdout
        }
        
        try:
            lines = stdout.split('\n')
            current_host = None
            
            for line in lines:
                line = line.strip()
                
                # Count hosts
                if 'Nmap scan report for' in line:
                    current_host = line.split('for ')[-1]
                    results['hosts_scanned'] += 1
                    if 'Host is up' in line or current_host:
                        results['hosts_up'] += 1
                
                # Count open ports
                if '/tcp open' in line or '/udp open' in line:
                    results['open_ports'] += 1
                    service_info = line.split()
                    if len(service_info) >= 3:
                        results['services'].append({
                            'host': current_host,
                            'port': service_info[0],
                            'service': service_info[2] if len(service_info) > 2 else 'unknown'
                        })
                
                # Detect vulnerabilities from script results
                if any(vuln_indicator in line.lower() for vuln_indicator in [
                    'vulnerable', 'cve-', 'exploit', 'weak', 'insecure', 'outdated'
                ]):
                    severity = self.classify_vulnerability(line)
                    results[severity] += 1
                    results['vulnerabilities'].append({
                        'host': current_host,
                        'description': line,
                        'severity': severity,
                        'source': 'nmap'
                    })
            
            self.scan_progress = 80
            return results
            
        except Exception as e:
            logger.error(f"Error parsing nmap results: {str(e)}")
            return results
    
    def classify_vulnerability(self, description: str) -> str:
        """Classify vulnerability severity based on description"""
        desc_lower = description.lower()
        
        if any(term in desc_lower for term in ['critical', 'remote code execution', 'rce', 'exploit']):
            return 'critical'
        elif any(term in desc_lower for term in ['high', 'privilege escalation', 'authentication bypass']):
            return 'high'
        elif any(term in desc_lower for term in ['medium', 'information disclosure', 'weak']):
            return 'medium'
        elif any(term in desc_lower for term in ['low', 'outdated', 'version']):
            return 'low'
        else:
            return 'info'
    
    def run_additional_scans(self, targets: str) -> Dict:
        """Run additional security scans"""
        results = {
            'open_services': [],
            'information_findings': []
        }
        
        # Check for stopping flag
        if self._stop_scan_flag:
            return results
            
        available_tools = self.get_available_tools()
        
        # Run sslscan if available
        if available_tools['sslscan']:
            self.scan_progress = 80
            ssl_results = self.run_ssl_scan(targets)
            if ssl_results and 'findings' in ssl_results:
                results['information_findings'].extend(ssl_results['findings'])
        
        # Run whatweb if available
        if available_tools['whatweb'] and not self._stop_scan_flag:
            self.scan_progress = 85
            whatweb_results = self.run_whatweb_scan(targets)
            if whatweb_results and 'services' in whatweb_results:
                results['open_services'].extend(whatweb_results['services'])
        
        return results
        
    def run_ssl_scan(self, targets: str) -> Dict:
        """Run sslscan to check for SSL/TLS vulnerabilities"""
        try:
            logger.info(f"Running SSL scan on {targets}")
            
            if self._stop_scan_flag:
                return {'error': 'Scan was stopped'}
            
            # Parse target hosts
            hosts = []
            try:
                network = ipaddress.ip_network(targets, strict=False)
                for host in network.hosts():
                    hosts.append(str(host))
            except:
                hosts = [targets.split('/')[0]]
            
            results = {
                'findings': []
            }
            
            # Only scan first 5 hosts
            for host in hosts[:5]:
                if self._stop_scan_flag:
                    break
                
                # Check if port 443 is open
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                try:
                    s.connect((host, 443))
                except:
                    continue
                finally:
                    s.close()
                
                # Run sslscan
                cmd = ['sslscan', '--no-colour', host]
                
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                    
                    # Parse for vulnerabilities
                    ssl_issues = []
                    for line in result.stdout.split('\n'):
                        line = line.strip()
                        if any(issue in line.lower() for issue in [
                            'vulnerable', 'weak', 'insecure', 'deprecated', 
                            'obsolete', 'md5', 'sha1', 'rc4', 'des', 'null',
                            'heartbleed', 'poodle', 'beast', 'freak', 'logjam'
                        ]):
                            severity = 'high' if any(critical in line.lower() for critical in [
                                'heartbleed', 'critical', 'remote code'
                            ]) else 'medium'
                            
                            ssl_issues.append({
                                'host': host,
                                'description': line,
                                'severity': severity,
                                'source': 'sslscan'
                            })
                    
                    # Add issues to results
                    results['findings'].extend(ssl_issues)
                    
                except subprocess.TimeoutExpired:
                    logger.warning(f"SSL scan timed out for {host}")
                except Exception as e:
                    logger.error(f"Error running SSL scan on {host}: {str(e)}")
            
            return results
            
        except Exception as e:
            logger.error(f"SSL scan failed: {str(e)}")
            return {'error': f'SSL scan failed: {str(e)}'}
            
    def run_whatweb_scan(self, targets: str) -> Dict:
        """Run whatweb to identify web technologies"""
        try:
            logger.info(f"Running whatweb on {targets}")
            
            if self._stop_scan_flag:
                return {'error': 'Scan was stopped'}
            
            # Parse target hosts
            hosts = []
            try:
                network = ipaddress.ip_network(targets, strict=False)
                for host in network.hosts():
                    hosts.append(str(host))
            except:
                hosts = [targets.split('/')[0]]
            
            results = {
                'services': []
            }
            
            # Only scan first 5 hosts
            for host in hosts[:5]:
                if self._stop_scan_flag:
                    break
                
                # Run whatweb scan
                cmd = [
                    'whatweb', '-a', '3',  # Aggressive mode
                    '--no-errors',
                    '--log-brief=/dev/stdout',
                    host
                ]
                
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                    
                    # Parse results
                    if result.stdout:
                        results['services'].append({
                            'host': host,
                            'technologies': result.stdout.strip(),
                            'source': 'whatweb'
                        })
                    
                except subprocess.TimeoutExpired:
                    logger.warning(f"whatweb scan timed out for {host}")
                except Exception as e:
                    logger.error(f"Error running whatweb on {host}: {str(e)}")
            
            return results
            
        except Exception as e:
            logger.error(f"whatweb scan failed: {str(e)}")
            return {'error': f'whatweb scan failed: {str(e)}'}
    
    def run_background_scan(self, targets: str, scan_name: str):
        """Run comprehensive scan in background thread"""
        try:
            self._stop_scan_flag = False
            self.scan_id = f"fallback_{int(time.time())}"
            self.scan_status = 'running'
            self.scan_progress = 10
            
            logger.info(f"Starting fallback security scan for {targets}")
            
            # Initialize results
            results = {
                'scan_id': self.scan_id,
                'scan_name': scan_name,
                'targets': targets,
                'start_time': time.time(),
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0,
                'info': 0,
                'total_vulnerabilities': 0,
                'hosts_scanned': 0,
                'hosts_up': 0,
                'open_ports': 0,
                'vulnerabilities': [],
                'services': [],
                'tools_used': []
            }
            
            # Check available tools
            available_tools = self.get_available_tools()
            results['tools_used'] = [tool for tool, available in available_tools.items() if available]
            
            # Check if scan has been stopped
            if self._stop_scan_flag:
                self.scan_status = 'aborted'
                return
            
            # Run nmap scan if available
            if available_tools['nmap']:
                nmap_results = self.run_nmap_scan(targets)
                if 'error' not in nmap_results:
                    results.update(nmap_results)
                    results['total_vulnerabilities'] = (
                        results['critical'] + results['high'] + 
                        results['medium'] + results['low']
                    )
                
                # Check if scan has been stopped
                if self._stop_scan_flag:
                    self.scan_status = 'aborted'
                    return
            
            # Run Nikto scan for web vulnerabilities if available
            if available_tools['nikto']:
                self.scan_progress = 60
                logger.info("Running Nikto web vulnerability scan...")
                nikto_results = self.run_nikto_scan(targets)
                if 'error' not in nikto_results:
                    # Update vulnerability counts
                    results['critical'] += nikto_results['critical']
                    results['high'] += nikto_results['high']
                    results['medium'] += nikto_results['medium']
                    results['low'] += nikto_results['low']
                    
                    # Add vulnerabilities
                    results['vulnerabilities'].extend(nikto_results.get('vulnerabilities', []))
                    results['total_vulnerabilities'] = (
                        results['critical'] + results['high'] + 
                        results['medium'] + results['low']
                    )
                
                # Check if scan has been stopped
                if self._stop_scan_flag:
                    self.scan_status = 'aborted'
                    return
            
            # Run additional scans
            additional_results = self.run_additional_scans(targets)
            results['additional_findings'] = additional_results
            
            # Update progress
            self.scan_progress = 100
            self.scan_status = 'completed'
            self.scan_results = results
            
            logger.info(f"Fallback scan completed. Found {results['total_vulnerabilities']} potential issues")
            
        except Exception as e:
            logger.error(f"Background scan failed: {str(e)}")
            self.scan_status = 'error'
            self.scan_results = {'error': str(e)}
    
    def start_scan(self, targets: str, scan_name: str) -> Dict:
        """Start a vulnerability scan"""
        try:
            if self.scan_status == 'running':
                return {'error': 'A scan is already running'}
            
            # Start scan in background thread
            self.scan_thread = threading.Thread(
                target=self.run_background_scan,
                args=(targets, scan_name)
            )
            self.scan_thread.daemon = True
            self.scan_thread.start()
            
            return {
                'success': True,
                'scan_id': f"fallback_{int(time.time())}",
                'message': f'Security scan initiated for targets: {targets}',
                'scan_name': scan_name,
                'tools_available': self.get_available_tools()
            }
            
        except Exception as e:
            logger.error(f"Failed to start scan: {str(e)}")
            return {'error': f'Failed to start scan: {str(e)}'}
    
    def get_scan_status(self) -> Dict:
        """Get current scan status"""
        return {
            'status': self.scan_status,
            'progress': self.scan_progress,
            'scan_id': self.scan_id
        }
    
    def get_scan_results(self) -> Dict:
        """Get scan results"""
        if self.scan_status == 'completed':
            return self.scan_results
        elif self.scan_status == 'error':
            return self.scan_results
        else:
            return {'message': 'Scan still in progress', 'progress': self.scan_progress}
    
    def stop_scan(self) -> Dict:
        """Stop a currently running scan"""
        try:
            if self.scan_status != 'running':
                return {'message': 'No scan is currently running'}
            
            # Set flag to stop the scan
            self._stop_scan_flag = True
            
            # Wait for the scan to terminate (with timeout)
            max_wait = 10  # seconds
            for _ in range(max_wait):
                if self.scan_status != 'running':
                    break
                time.sleep(1)
            
            # Force reset if scan is still running
            if self.scan_status == 'running':
                self.scan_status = 'aborted'
                
            self.scan_progress = 0
            return {
                'success': True,
                'message': 'Scan terminated successfully'
            }
            
        except Exception as e:
            logger.error(f"Error stopping scan: {str(e)}")
            return {'error': f'Failed to stop scan: {str(e)}'}
            
    def reset_scan_state(self) -> Dict:
        """Reset the scanner state"""
        try:
            self.stop_scan()
            self.scan_id = None
            self.scan_status = 'idle'
            self.scan_progress = 0
            self.scan_results = {}
            self._stop_scan_flag = False
            return {
                'success': True,
                'message': 'Scanner state reset successfully'
            }
        except Exception as e:
            logger.error(f"Error resetting scanner state: {str(e)}")
            return {'error': f'Failed to reset scanner state: {str(e)}'}
    
    def run_nikto_scan(self, targets: str) -> Dict:
        """Run Nikto web vulnerability scanner"""
        try:
            logger.info(f"Running Nikto scan on {targets}")
            
            if self._stop_scan_flag:
                return {'error': 'Scan was stopped'}
            
            # Simple target validation
            if '/' not in targets:
                targets = f"{targets}/24"  # Default to subnet scan
                
            # Parse hosts from subnet
            hosts = []
            try:
                network = ipaddress.ip_network(targets, strict=False)
                for host in network.hosts():
                    hosts.append(str(host))
            except:
                # If not a subnet, treat as a single host
                hosts = [targets.split('/')[0]]
            
            results = {
                'hosts_scanned': len(hosts),
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0,
                'info': 0,
                'vulnerabilities': []
            }
            
            # Only scan first 5 hosts to avoid excessive time
            for host in hosts[:5]:
                if self._stop_scan_flag:
                    break
                    
                # Check if port 80 or 443 is open before scanning
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                http_open = False
                https_open = False
                
                try:
                    s.connect((host, 80))
                    http_open = True
                except:
                    pass
                finally:
                    s.close()
                    
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                try:
                    s.connect((host, 443))
                    https_open = True
                except:
                    pass
                finally:
                    s.close()
                
                if not http_open and not https_open:
                    continue
                
                # Run Nikto scan
                protocol = 'https' if https_open else 'http'
                cmd = [
                    'nikto', '-h', f"{protocol}://{host}", 
                    '-Format', 'txt', '-nointeractive',
                    '-Tuning', '123457890',  # All types of tests except denial of service
                    '-maxtime', '120s'  # Limit scan time
                ]
                
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
                    
                    # Parse vulnerabilities
                    for line in result.stdout.split('\n'):
                        if any(term in line.lower() for term in [
                            'vulnerability', 'vulnerable', 'warning', 'critical',
                            'high', 'medium', 'low', 'risk', 'cve-', 'osvdb-'
                        ]):
                            severity = self.classify_vulnerability(line)
                            results[severity] += 1
                            results['vulnerabilities'].append({
                                'host': host,
                                'description': line,
                                'severity': severity,
                                'source': 'nikto'
                            })
                except subprocess.TimeoutExpired:
                    logger.warning(f"Nikto scan timed out for {host}")
                except Exception as e:
                    logger.error(f"Error running Nikto on {host}: {str(e)}")
            
            return results
            
        except Exception as e:
            logger.error(f"Nikto scan failed: {str(e)}")
            return {'error': f'Nikto scan failed: {str(e)}'}
    
    def generate_report(self, format_type: str = 'html') -> str:
        """Generate a formatted report from scan results"""
        try:
            if not self.scan_results:
                return None
                
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            
            if format_type.lower() == 'html':
                report_path = f"/tmp/cybershield_scan_report_{timestamp}.html"
                return self._generate_html_report(report_path)
            elif format_type.lower() == 'json':
                report_path = f"/tmp/cybershield_scan_report_{timestamp}.json"
                return self._generate_json_report(report_path)
            else:
                # Default to text format
                report_path = f"/tmp/cybershield_scan_report_{timestamp}.txt"
                return self._generate_text_report(report_path)
                
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return None
    
    def _generate_html_report(self, file_path: str) -> str:
        """Generate HTML format report"""
        try:
            results = self.scan_results
            total_vulns = results.get('critical', 0) + results.get('high', 0) + results.get('medium', 0) + results.get('low', 0)
            
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>CyberShield Security Scan Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; text-align: center; }}
        .summary {{ background: #ecf0f1; padding: 15px; margin: 20px 0; }}
        .critical {{ color: #e74c3c; font-weight: bold; }}
        .high {{ color: #e67e22; font-weight: bold; }}
        .medium {{ color: #f39c12; font-weight: bold; }}
        .low {{ color: #f1c40f; font-weight: bold; }}
        .vuln-item {{ margin: 10px 0; padding: 10px; border-left: 4px solid #3498db; background: #f8f9fa; }}
        .service-item {{ margin: 5px 0; padding: 8px; background: #e8f5e8; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>CyberShield Security Scan Report</h1>
        <p>Generated on: {time.strftime("%Y-%m-%d %H:%M:%S")}</p>
        <p>Scan ID: {self.scan_id or 'N/A'}</p>
    </div>
    
    <div class="summary">
        <h2>Scan Summary</h2>
        <p><strong>Total Vulnerabilities Found:</strong> {total_vulns}</p>
        <p><strong>Hosts Scanned:</strong> {results.get('hosts_scanned', 0)}</p>
        <p><strong>Hosts Up:</strong> {results.get('hosts_up', 0)}</p>
        <p><strong>Open Ports:</strong> {results.get('open_ports', 0)}</p>
        
        <h3>Vulnerability Breakdown:</h3>
        <ul>
            <li class="critical">Critical: {results.get('critical', 0)}</li>
            <li class="high">High: {results.get('high', 0)}</li>
            <li class="medium">Medium: {results.get('medium', 0)}</li>
            <li class="low">Low: {results.get('low', 0)}</li>
            <li>Informational: {results.get('info', 0)}</li>
        </ul>
    </div>
"""
            
            # Add vulnerabilities section
            if results.get('vulnerabilities'):
                html_content += """
    <div class="vulnerabilities">
        <h2>Discovered Vulnerabilities</h2>
"""
                for vuln in results['vulnerabilities']:
                    severity_class = vuln.get('severity', 'low')
                    html_content += f"""
        <div class="vuln-item">
            <h4 class="{severity_class}">{vuln.get('severity', 'Unknown').upper()} - {vuln.get('host', 'Unknown Host')}</h4>
            <p><strong>Source:</strong> {vuln.get('source', 'Unknown')}</p>
            <p><strong>Description:</strong> {vuln.get('description', 'No description available')}</p>
        </div>
"""
                html_content += "    </div>\n"
            
            # Add services section
            if results.get('services'):
                html_content += """
    <div class="services">
        <h2>Discovered Services</h2>
"""
                for service in results['services']:
                    html_content += f"""
        <div class="service-item">
            <strong>{service.get('host', 'Unknown')}:{service.get('port', 'Unknown')}</strong> - 
            {service.get('service', 'Unknown Service')} ({service.get('state', 'Unknown')})
        </div>
"""
                html_content += "    </div>\n"
            
            html_content += """
</body>
</html>
"""
            
            with open(file_path, 'w') as f:
                f.write(html_content)
                
            logger.info(f"HTML report generated: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error generating HTML report: {str(e)}")
            return None
    
    def _generate_json_report(self, file_path: str) -> str:
        """Generate JSON format report"""
        try:
            report_data = {
                'scan_info': {
                    'scan_id': self.scan_id,
                    'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                    'scanner': 'CyberShield Fallback Scanner'
                },
                'results': self.scan_results
            }
            
            with open(file_path, 'w') as f:
                json.dump(report_data, f, indent=2)
                
            logger.info(f"JSON report generated: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error generating JSON report: {str(e)}")
            return None
    
    def _generate_text_report(self, file_path: str) -> str:
        """Generate text format report"""
        try:
            results = self.scan_results
            total_vulns = results.get('critical', 0) + results.get('high', 0) + results.get('medium', 0) + results.get('low', 0)
            
            report_content = f"""
CyberShield Security Scan Report
===============================

Generated on: {time.strftime("%Y-%m-%d %H:%M:%S")}
Scan ID: {self.scan_id or 'N/A'}

SCAN SUMMARY
============
Total Vulnerabilities Found: {total_vulns}
Hosts Scanned: {results.get('hosts_scanned', 0)}
Hosts Up: {results.get('hosts_up', 0)}
Open Ports: {results.get('open_ports', 0)}

Vulnerability Breakdown:
- Critical: {results.get('critical', 0)}
- High: {results.get('high', 0)}
- Medium: {results.get('medium', 0)}
- Low: {results.get('low', 0)}
- Informational: {results.get('info', 0)}

"""
            
            # Add vulnerabilities
            if results.get('vulnerabilities'):
                report_content += "\nDISCOVERED VULNERABILITIES\n"
                report_content += "=" * 26 + "\n\n"
                for vuln in results['vulnerabilities']:
                    report_content += f"Severity: {vuln.get('severity', 'Unknown').upper()}\n"
                    report_content += f"Host: {vuln.get('host', 'Unknown')}\n"
                    report_content += f"Source: {vuln.get('source', 'Unknown')}\n"
                    report_content += f"Description: {vuln.get('description', 'No description')}\n"
                    report_content += "-" * 50 + "\n\n"
            
            # Add services
            if results.get('services'):
                report_content += "\nDISCOVERED SERVICES\n"
                report_content += "=" * 19 + "\n\n"
                for service in results['services']:
                    report_content += f"{service.get('host', 'Unknown')}:{service.get('port', 'Unknown')} - "
                    report_content += f"{service.get('service', 'Unknown')} ({service.get('state', 'Unknown')})\n"
            
            with open(file_path, 'w') as f:
                f.write(report_content)
                
            logger.info(f"Text report generated: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error generating text report: {str(e)}")
            return None

def main():
    """Test the fallback scanner"""
    scanner = FallbackScanner()
    
    print("Available security tools:")
    tools = scanner.get_available_tools()
    for tool, available in tools.items():
        status = "✅" if available else "❌"
        print(f"  {status} {tool}")
    
    # Test scan
    result = scanner.start_scan("127.0.0.1", "Test_Scan")
    print(f"Scan started: {result}")

if __name__ == "__main__":
    main()
