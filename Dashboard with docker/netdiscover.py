import subprocess
import re
import socket
import ipaddress
from tabulate import tabulate

def list_devices(interface="wlan0"):
    try:
        print(f"[+] Scanning network on interface: {interface}...\n")
        output = subprocess.check_output(
            f"sudo arp-scan --interface={interface} --localnet", shell=True
        ).decode()

        seen_macs = set()
        devices = []

        for line in output.splitlines():
            match = re.match(r"(\d+\.\d+\.\d+\.\d+)\s+([0-9A-Fa-f:]{17})", line)
            if match:
                ip, mac = match.groups()
                mac = mac.upper()

                # Skip duplicate MACs
                if mac in seen_macs:
                    continue
                seen_macs.add(mac)

                # Try to resolve hostname
                try:
                    hostname = socket.gethostbyaddr(ip)[0]
                except socket.herror:
                    hostname = "Unknown"

                devices.append((ip, mac, hostname))

        # Sort by IP address
        devices.sort(key=lambda x: ipaddress.IPv4Address(x[0]))

        if devices:
            print(tabulate(devices, headers=["IP Address", "MAC Address", "Hostname"], tablefmt="fancy_grid"))
        else:
            print("[!] No devices found.")

    except subprocess.CalledProcessError as e:
        print("[!] Error running arp-scan:", e)

if __name__ == "__main__":
    list_devices()
