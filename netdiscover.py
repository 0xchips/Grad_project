import subprocess
import re
import socket
import ipaddress
import sys
import json
# from tabulate import tabulate

def list_devices(interface="wlan0"):
    try:
        print(f"[+] Scanning network on interface: {interface}...")
        
        # Try multiple scanning methods
        output = ""
        devices = []
        
        # Method 1: Try arp-scan with sudo (if available)
        try:
            output = subprocess.check_output(
                f"sudo -n arp-scan --interface={interface} --localnet 2>/dev/null", shell=True
            ).decode()
            print("[+] Using arp-scan method")
        except subprocess.CalledProcessError:
            # Method 2: Try nmap without sudo
            try:
                # Get network range
                network_cmd = f"ip route | grep {interface} | grep '/' | head -1 | awk '{{print $1}}'"
                network = subprocess.check_output(network_cmd, shell=True).decode().strip()
                if network:
                    output = subprocess.check_output(
                        f"nmap -sn {network}", shell=True
                    ).decode()
                    print("[+] Using nmap method")
                else:
                    raise subprocess.CalledProcessError(1, "network detection")
            except subprocess.CalledProcessError:
                # Method 3: Parse ARP table
                try:
                    output = subprocess.check_output("arp -a", shell=True).decode()
                    print("[+] Using ARP table method")
                except subprocess.CalledProcessError:
                    print("[!] Error: Unable to scan network. No scanning methods available.")
                    return

        seen_macs = set()
        seen_ips = set()

        # Parse arp-scan output
        for line in output.splitlines():
            line = line.strip()
            if not line:
                continue
                
            # Parse arp-scan format: IP MAC
            match = re.match(r"(\d+\.\d+\.\d+\.\d+)\s+([0-9A-Fa-f:]{17})", line)
            if match:
                ip, mac = match.groups()
                mac = mac.upper()
                if mac in seen_macs or ip in seen_ips:
                    continue
                seen_macs.add(mac)
                seen_ips.add(ip)
            else:
                # Parse nmap format: "Nmap scan report for hostname (IP)"
                nmap_match = re.search(r"Nmap scan report for.*\((\d+\.\d+\.\d+\.\d+)\)", line)
                if nmap_match:
                    ip = nmap_match.group(1)
                    if ip in seen_ips:
                        continue
                    seen_ips.add(ip)
                    mac = "N/A"
                else:
                    # Parse ARP table format: "hostname (IP) at MAC"
                    arp_match = re.search(r"\((\d+\.\d+\.\d+\.\d+)\) at ([0-9A-Fa-f:]{17})", line)
                    if arp_match:
                        ip, mac = arp_match.groups()
                        mac = mac.upper()
                        if mac in seen_macs or ip in seen_ips:
                            continue
                        seen_macs.add(mac)
                        seen_ips.add(ip)
                    else:
                        continue

            # Try to resolve hostname for all discovered IPs
            try:
                hostname = socket.gethostbyaddr(ip)[0]
            except socket.herror:
                hostname = "Unknown"

            devices.append({
                "ip": ip,
                "mac": mac,
                "hostname": hostname
            })

        # Sort by IP address
        if devices:
            devices.sort(key=lambda x: ipaddress.IPv4Address(x["ip"]))

        # Output results
        if devices:
            print(f"\n[+] Found {len(devices)} devices:")
            for device in devices:
                print(f"IP: {device['ip']:<15} | MAC: {device['mac']:<17} | Hostname: {device['hostname']}")
            
            # Also output as JSON for web interface
            print(f"\n[JSON_START]{json.dumps(devices)}[JSON_END]")
        else:
            print("[!] No devices found on the network.")
            print(f"\n[JSON_START]{json.dumps([])}[JSON_END]")

    except Exception as e:
        print(f"[!] Error during network scan: {e}")
        sys.exit(1)

if __name__ == "__main__":
    list_devices()
