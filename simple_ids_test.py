#!/usr/bin/env python3
"""
Simple IDS Testing Script
"""

import subprocess
import time
import requests
from datetime import datetime

print("="*60)
print("STARTING SIMPLE IDS ATTACK TESTING")
print("="*60)

# Test 1: DNS suspicious queries
print("\n--- DNS Suspicious Queries ---")
suspicious_domains = [
    "malware-c2-server.evil.com",
    "botnet-command.malicious.net",
    "crypto-miner.coinhive.com",
    f"{'a' * 50}.tunnel.bad",
    "phishing-site.fake-bank.org"
]

for domain in suspicious_domains:
    try:
        print(f"Querying: {domain}")
        result = subprocess.run(f"nslookup {domain}", shell=True, capture_output=True, timeout=5)
        time.sleep(1)
    except Exception as e:
        print(f"Error with {domain}: {e}")

# Test 2: Port scanning
print("\n--- Port Scanning ---")
try:
    print("Starting port scan...")
    result = subprocess.run("nmap -sS -T4 -p 80,443,22,21,23 127.0.0.1", shell=True, capture_output=True, timeout=30)
    print("Port scan completed")
except Exception as e:
    print(f"Port scan error: {e}")

# Test 3: HTTP attacks on our Flask app
print("\n--- HTTP Attack Simulation ---")
sql_payloads = [
    "' OR '1'='1",
    "'; DROP TABLE users; --",
    "admin'/*"
]

for payload in sql_payloads:
    try:
        print(f"Testing SQL injection: {payload}")
        url = f"http://127.0.0.1:5053/api/nids-status?test={payload}"
        response = requests.get(url, timeout=3)
        print(f"Response status: {response.status_code}")
        time.sleep(1)
    except Exception as e:
        print(f"HTTP attack error: {e}")

# Test 4: Suspicious User-Agents
print("\n--- Suspicious User-Agents ---")
suspicious_agents = ["Nikto", "sqlmap", "Nessus", "w3af"]

for agent in suspicious_agents:
    try:
        print(f"Using User-Agent: {agent}")
        headers = {'User-Agent': agent}
        response = requests.get("http://127.0.0.1:5053", headers=headers, timeout=3)
        print(f"Response status: {response.status_code}")
        time.sleep(1)
    except Exception as e:
        print(f"User-Agent test error: {e}")

print("\n" + "="*60)
print("SIMPLE IDS TESTING COMPLETED")
print("="*60)
print("Waiting 15 seconds for Suricata to process events...")
time.sleep(15)
print("Check dashboard for new alerts!")
