from scapy.all import ARP, Ether, srp

# Function to resolve MAC address for a given IP address
def resolve_mac(ip):
    # Create an ARP request packet
    arp_request = ARP(pdst=ip)
    # Create an Ethernet frame
    broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
    # Combine Ethernet frame and ARP request
    arp_request_broadcast = broadcast / arp_request

    # Send the packet and get the response
    answered_list = srp(arp_request_broadcast, timeout=2, verbose=False)[0]

    if answered_list:
        # Return the MAC address from the response
        return answered_list[0][1].hwsrc
    else:
        return None

# Example usage
if __name__ == "__main__":
    target_ip = input("Enter target IP address: ")
    mac_address = resolve_mac(target_ip)

    if mac_address:
        print(f"MAC address for {target_ip} is {mac_address}")
    else:
        print(f"Could not resolve MAC address for {target_ip}")