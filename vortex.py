import os
import sys
import time
import shutil
import hashlib
import threading
import winreg
import psutil
import numpy as np
import tensorflow as tf
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from stegpy import analyze

# === Config ===
SIGNATURES = {
    "44d88612fea8a8f36de82e1278abb02f": "EICAR-Test-File"
}
WATCH_PATH = "C:\\Users"
QUARANTINE_DIR = os.path.join(os.getcwd(), "quarantine")
LOG_FILE = "antivirus_log.txt"
SCRIPT_EXTENSIONS = [".bat", ".vbs", ".ps1", ".cmd", ".exe", ".cpp", ".py"]
MACHINE_LEARNING_MODEL_PATH = "ml_model.h5"  # Machine learning model for file classification
NETWORK_MONITOR = True

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

# === Machine Learning Detection ===
def load_ml_model():
    try:
        model = tf.keras.models.load_model(MACHINE_LEARNING_MODEL_PATH)
        log("[*] Machine learning model loaded successfully.")
        return model
    except Exception as e:
        log(f"[!] Failed to load machine learning model: {e}")
        return None

def ml_predict(path, model):
    # Extract features like file byte sequences, metadata, etc.
    file_features = extract_features(path)
    prediction = model.predict(np.array([file_features]))  # Assuming the model accepts this format
    return prediction

# === Feature Extraction for Machine Learning ===
def extract_features(path):
    # Example of feature extraction: file size, byte frequency, etc.
    file_size = os.path.getsize(path)
    file_hash = hash_file(path)
    with open(path, "rb") as f:
        data = f.read()
    byte_frequencies = np.array([data.count(i) for i in range(256)])  # Byte frequency histogram
    return np.concatenate([byte_frequencies, [file_size], [file_hash]], axis=0)

# === Heuristic Detection ===
def advanced_heuristic_check(path):
    suspicious_patterns = [
        b"VirtualAllocEx", b"CreateRemoteThread", b"WinExec", b"LoadLibraryA", b"GetProcAddress", b"SetWindowsHookEx"
    ]
    
    try:
        with open(path, "rb") as f:
            data = f.read()
            for pattern in suspicious_patterns:
                if pattern in data:
                    return True
    except Exception as e:
        log(f"[!] Error scanning file with advanced heuristic: {e}")
    return False

# === Real-Time Network Monitoring ===
def network_monitor():
    if NETWORK_MONITOR:
        # Monitor outgoing connections for suspicious activity
        connections = psutil.net_connections(kind='inet')
        for conn in connections:
            if conn.status == "ESTABLISHED" and conn.raddr:
                remote_ip = conn.raddr[0]
                log(f"[Network Alert] Outbound connection to suspicious IP: {remote_ip}")

# === Memory Scanning (Processes and Open Handles) ===
def memory_scan():
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            proc_name = proc.info['name']
            if proc_name in ['powershell', 'cmd', 'python']:
                # Further analysis can be added here based on process behavior
                log(f"[Memory Scan] Suspicious process detected: {proc_name} (PID: {proc.info['pid']})")
        except psutil.NoSuchProcess:
            pass

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

# === Scanner ===
def scan_file(path, model=None):
    md5 = hash_file(path)
    if not md5:
        return
    if md5 in SIGNATURES:
        log(f"[!!] Signature match ({SIGNATURES[md5]}): {path}")
        quarantine_file(path)
    elif advanced_heuristic_check(path):
        log(f"[!!] Advanced heuristic threat detected: {path}")
        quarantine_file(path)
    elif model:
        prediction = ml_predict(path, model)
        if prediction > 0.5:  # Example threshold, tune based on model
            log(f"[!!] Machine Learning threat detected: {path}")
            quarantine_file(path)
    elif any(path.endswith(ext) for ext in SCRIPT_EXTENSIONS):
        scan_script(path)  # Check for suspicious scripts
    elif path.lower().endswith((".exe", ".cpp", ".py")):  # Added support for .exe, .cpp, .py
        log(f"[*] Scanning executable/script file: {path}")
        scan_executable(path)  # Check for malicious executables or scripts
    else:
        log(f"[!] Unknown file type: {path}")

# === Script Detection ===
def scan_script(path):
    try:
        with open(path, "r", encoding="latin-1") as f:
            data = f.read()
            # Check for common commands in scripts that are often used in malicious files
            if "powershell" in data or "cmd.exe" in data or "wscript" in data:
                log(f"[!!] Potential malicious script detected: {path}")
                quarantine_file(path)
    except Exception as e:
        log(f"[!] Error scanning script {path}: {e}")

# === Executable (EXE) Detection ===
def scan_executable(path):
    try:
        with open(path, "rb") as f:
            data = f.read()
            # Look for common signs of malicious executables like embedded payloads or unusual API calls
            if b"CreateRemoteThread" in data or b"VirtualAllocEx" in data:
                log(f"[!!] Malicious executable detected: {path}")
                quarantine_file(path)
    except Exception as e:
        log(f"[!] Error scanning executable {path}: {e}")

def scan_directory(path, model=None):
    for root, _, files in os.walk(path):
        for file in files:
            scan_file(os.path.join(root, file), model)

# === Main Function ===
def main():
    log("\n===== Python Ultra-Advanced Antivirus Started =====")
    add_to_startup()

    model = load_ml_model()  # Load machine learning model for file classification
    t1 = threading.Thread(target=scan_directory, args=(WATCH_PATH, model), daemon=True)
    t2 = threading.Thread(target=watch_directory, args=(WATCH_PATH,), daemon=True)
    t3 = threading.Thread(target=network_monitor, daemon=True)
    t4 = threading.Thread(target=memory_scan, daemon=True)
    
    t1.start()
    t2.start()
    t3.start()
    t4.start()

    while True:
        time.sleep(10)

if __name__ == "__main__":
    main()
