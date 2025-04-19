import os
import sys
import time
import shutil
import hashlib
import threading
import winreg
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# === Config ===
SIGNATURES = {
    "44d88612fea8a8f36de82e1278abb02f": "EICAR-Test-File"
}
WATCH_PATH = "C:\\Users"
QUARANTINE_DIR = os.path.join(os.getcwd(), "quarantine")
LOG_FILE = "antivirus_log.txt"

# === Utilities ===
def hash_file(path):
    try:
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return None

def log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(f"{time.ctime()}: {msg}\n")
    print(msg)

def add_to_startup():
    try:
        exe_path = sys.executable
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "PythonAntivirus", 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(key)
        log("[*] Added to startup.")
    except Exception as e:
        log(f"[!] Failed to add to startup: {e}")

def quarantine_file(path):
    try:
        os.makedirs(QUARANTINE_DIR, exist_ok=True)
        basename = os.path.basename(path)
        target = os.path.join(QUARANTINE_DIR, basename)
        shutil.move(path, target)
        log(f"[!] Quarantined: {path}")
    except Exception as e:
        log(f"[!] Failed to quarantine {path}: {e}")

# === Heuristic Detection ===
def heuristic_check(path):
    score = 0
    try:
        with open(path, "rb") as f:
            data = f.read()
            if b"powershell" in data: score += 2
            if b"cmd.exe" in data: score += 1
            if b"CreateRemoteThread" in data: score += 3
            if b"VirtualAllocEx" in data: score += 3
            if b"WinExec" in data: score += 1
    except:
        pass
    return score

# === Scanner ===
def scan_file(path):
    md5 = hash_file(path)
    if not md5:
        return
    if md5 in SIGNATURES:
        log(f"[!!] Signature match ({SIGNATURES[md5]}): {path}")
        quarantine_file(path)
    else:
        score = heuristic_check(path)
        if score >= 5:
            log(f"[!!] Heuristic threat (score={score}): {path}")
            quarantine_file(path)

def scan_directory(path):
    for root, _, files in os.walk(path):
        for file in files:
            scan_file(os.path.join(root, file))

# === Real-time Watcher ===
class ThreatWatcher(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            scan_file(event.src_path)

def watch_directory(path):
    observer = Observer()
    handler = ThreatWatcher()
    observer.schedule(handler, path, recursive=True)
    observer.start()
    log(f"[*] Watching directory: {path}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

# === Main Function ===
def main():
    log("\n===== Python Advanced Antivirus Started =====")
    add_to_startup()
    t1 = threading.Thread(target=scan_directory, args=(WATCH_PATH,), daemon=True)
    t2 = threading.Thread(target=watch_directory, args=(WATCH_PATH,), daemon=True)
    t1.start()
    t2.start()
    while True:
        time.sleep(10)

if __name__ == "__main__":
    main()
