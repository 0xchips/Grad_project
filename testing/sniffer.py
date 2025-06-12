from scapy.all import *

def process_packet(packet):
    if packet.haslayer(DNS) and packet.getlayer(DNS).qr == 0:
        print(f"[+] DNS Request: {packet[IP].src} asked for {packet[DNSQR].qname.decode()}")

sniff(filter="udp port 53", prn=process_packet, iface="eth0 ", store=0)
