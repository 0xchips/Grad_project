#!/usr/bin/env python3
"""
Real-time NIDS Testing Script
Generate real-time attack simulations to test dashboard updates
"""

import subprocess
import requests
import time
import json
import random
import string
import threading
from datetime import datetime

class RealTimeNIDSTest:
    def __init__(self):
        self.base_url = "http://localhost:5053"
        self.attack_count = 0
        self.running = True
    
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def generate_dga_domain(self):
        """Generate random DGA-like domain"""
        length = random.randint(8, 16)
        domain = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
        tld = random.choice(['.com', '.net', '.org', '.biz', '.info'])
        return domain + tld
    
    def dns_attack_wave(self):
        """Generate a wave of suspicious DNS queries"""
        suspicious_domains = [
            "malware-c2-command.evil.com",
            "botnet-controller.suspicious.net", 
            "crypto-mining-pool.coinhive.org",
            "phishing-bank-fake.malicious.biz",
            "data-exfiltration.tunnel.info"
        ]
        
        # Add some DGA domains
        for _ in range(5):
            suspicious_domains.append(self.generate_dga_domain())
        
        self.log(f"🔍 Starting DNS attack wave with {len(suspicious_domains)} queries")
        
        for domain in suspicious_domains:
            try:
                subprocess.run(['nslookup', domain], 
                             capture_output=True, timeout=3)
                time.sleep(0.5)
            except:
                pass
        
        self.attack_count += len(suspicious_domains)
    
    def http_attack_wave(self):
        """Generate HTTP-based attacks"""
        payloads = [
            "' OR '1'='1' --",
            "'; DROP TABLE users; --",
            "<script>alert('XSS')</script>",
            "../../../../etc/passwd",
            "SELECT * FROM information_schema.tables",
            "UNION SELECT password FROM users",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')"
        ]
        
        user_agents = [
            "sqlmap/1.0",
            "Nikto/2.1.6",
            "w3af.org",
            "Nessus",
            "OpenVAS",
            "Burp Suite Professional"
        ]
        
        self.log(f"🌐 Starting HTTP attack wave with {len(payloads)} payloads")
        
        for i, payload in enumerate(payloads):
            try:
                headers = {'User-Agent': random.choice(user_agents)}
                params = {'q': payload, 'search': payload}
                
                response = requests.get(
                    f"{self.base_url}/api/ping",
                    params=params,
                    headers=headers,
                    timeout=5
                )
                time.sleep(0.3)
            except:
                pass
        
        self.attack_count += len(payloads)
    
    def port_scan_attack(self):
        """Simulate port scanning"""
        self.log("🔍 Starting port scan simulation")
        
        # Quick port scan
        common_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995]
        for port in common_ports:
            try:
                subprocess.run(['nc', '-z', '-w1', '127.0.0.1', str(port)], 
                             capture_output=True, timeout=2)
                time.sleep(0.1)
            except:
                pass
        
        self.attack_count += len(common_ports)
    
    def check_dashboard_response(self):
        """Check if dashboard is detecting our attacks"""
        try:
            response = requests.get(f"{self.base_url}/api/nids-status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                total_alerts = data.get('total_alerts', 0)
                total_dns = data.get('total_dns_logs', 0)
                self.log(f"📊 Dashboard Status: {total_alerts} alerts, {total_dns} DNS logs")
                return True
        except Exception as e:
            self.log(f"❌ Dashboard check failed: {e}")
        return False
    
    def run_continuous_test(self, duration_minutes=5):
        """Run continuous attack simulation"""
        self.log("🚀 Starting real-time NIDS testing")
        self.log(f"⏱️  Duration: {duration_minutes} minutes")
        self.log("=" * 50)
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        wave_count = 0
        
        while time.time() < end_time and self.running:
            wave_count += 1
            self.log(f"🌊 Attack Wave {wave_count}")
            
            # Randomize attack types
            attack_types = [
                self.dns_attack_wave,
                self.http_attack_wave,
                self.port_scan_attack
            ]
            
            # Run 1-2 random attack types per wave
            selected_attacks = random.sample(attack_types, random.randint(1, 2))
            
            for attack in selected_attacks:
                attack()
                time.sleep(1)
            
            # Check dashboard response
            self.check_dashboard_response()
            
            # Wait between waves
            wave_delay = random.randint(10, 20)
            self.log(f"⏳ Waiting {wave_delay} seconds for next wave...")
            time.sleep(wave_delay)
        
        self.log("=" * 50)
        self.log(f"🏁 Testing completed!")
        self.log(f"📈 Total simulated attacks: {self.attack_count}")
        self.log(f"🌊 Total attack waves: {wave_count}")
        
        # Final dashboard check
        time.sleep(10)  # Wait for processing
        self.log("🔍 Final dashboard check...")
        self.check_dashboard_response()

def main():
    try:
        tester = RealTimeNIDSTest()
        
        print("Real-time NIDS Dashboard Testing")
        print("This will generate continuous attack simulations")
        print("to test real-time detection and dashboard updates")
        print()
        
        duration = input("Enter test duration in minutes (default 3): ").strip()
        if not duration:
            duration = 3
        else:
            duration = int(duration)
        
        tester.run_continuous_test(duration)
        
    except KeyboardInterrupt:
        print("\n🛑 Testing stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
