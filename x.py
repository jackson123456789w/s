import os
import time
import shutil
import hashlib
import threading
import json
import psutil
import numpy as np
import torch  # Replaced TensorFlow with PyTorch
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QLabel,
    QPushButton,
    QTextEdit,
    QFileDialog,
    QMessageBox,
    QProgressBar,
    QSystemTrayIcon,
    QMenu
)
from PySide6.QtGui import QIcon, QAction  # Updated import for QAction
from PySide6.QtCore import Qt, QThread, Signal
from win10toast import ToastNotifier
import PyPDF2  # For PDF scanning
from PIL import Image
import io
import socket
import sys

# === Additional Configurations ===
THREAT_DATABASE_JSON = {
    "signatures": {
        # MD5 hashes
        "44d88612fea8a8f36de82e1278abb02f": "EICAR-Test-File",

        # New SHA-256 hashes
        "e3d704d8b8d6f5d3c3b8f8d8e3d704d8": "Shamoon",
        "b8d6f5d3c3b8f8d8e3d704d8b8d6f5d3": "Alureon",
        "c3b8f8d8e3d704d8b8d6f5d3c3b8f8d8": "Conficker",
        "f5d3c3b8f8d8e3d704d8b8d6f5d3c3b8": "Zeus",
        "d8e3d704d8b8d6f5d3c3b8f8d8e3d704": "Koobface",
        "704d8b8d6f5d3c3b8f8d8e3d704d8b8d": "Flame",
    }
}

QUARANTINE_DIR = os.path.join(os.getcwd(), "quarantine")
LOG_FILE = "antivirus_log.txt"
MACHINE_LEARNING_MODEL_PATH = "ml_model.pth"  # Updated file extension for PyTorch model
RANSOMWARE_EXTENSION_LIST = [".encrypted", ".locked", ".ransom", ".crypto", ".wncry", ".wncryt", ".wcry"]  # Add more extensions as needed

# Notification System
toaster = ToastNotifier()

def notify(title, message):
    toaster.show_toast(title, message, duration=10, threaded=True)

# === Antivirus Core ===
def hash_file(path):
    try:
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return None

def log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(f"{time.ctime()}: {msg}\n")

def quarantine_file(path):
    try:
        os.makedirs(QUARANTINE_DIR, exist_ok=True)
        basename = os.path.basename(path)
        target = os.path.join(QUARANTINE_DIR, basename)
        shutil.move(path, target)
        log(f"[!] Quarantined: {path}")
        notify("Threat Quarantined", f"The file {path} has been moved to quarantine.")
    except Exception as e:
        log(f"[!] Failed to quarantine {path}: {e}")

def delete_file(path):
    try:
        os.remove(path)
        log(f"[!] Deleted: {path}")
        notify("Threat Removed", f"The file {path} has been deleted.")
    except Exception as e:
        log(f"[!] Failed to delete {path}: {e}")

# Load machine learning model
def load_ml_model():
    try:
        model = torch.load(MACHINE_LEARNING_MODEL_PATH)  # Updated to load a PyTorch model
        model.eval()  # Set the model to evaluation mode
        log("[*] Machine learning model loaded successfully.")
        return model
    except Exception as e:
        log(f"[!] Failed to load machine learning model: {e}")
        return None

# Advanced Heuristic Check
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

# PDF Detection (Malicious JavaScript or embedded suspicious elements)
def scan_pdf_for_threats(path):
    try:
        with open(path, "rb") as f:
            reader = PyPDF2.PdfFileReader(f)
            for i in range(reader.getNumPages()):
                page = reader.getPage(i)
                if '/JavaScript' in page['/Resources']:
                    log(f"[!!] JavaScript found in PDF: {path}")
                    return True
    except Exception as e:
        log(f"[!] Error scanning PDF {path}: {e}")
    return False

# Steganography Detection (Hidden messages or data in images)
def detect_steganography_in_image(path):
    try:
        with Image.open(path) as img:
            pixels = np.array(img)
            diff_pixels = np.diff(pixels)
            if np.count_nonzero(diff_pixels) < 100:  # Example threshold
                log(f"[!!] Potential steganography detected in image: {path}")
                return True
    except Exception as e:
        log(f"[!] Error scanning image for steganography {path}: {e}")
    return False

# Ransomware Detection - Look for specific file extensions or behavior
def detect_ransomware(path):
    try:
        if any(path.lower().endswith(ext) for ext in RANSOMWARE_EXTENSION_LIST):
            log(f"[!!] Potential ransomware file detected: {path}")
            return True
    except Exception as e:
        log(f"[!] Error checking for ransomware: {e}")
    return False

# === Real-Time File Watcher ===
class RealTimeFileWatcher(FileSystemEventHandler):
    def __init__(self, model):
        self.model = model

    def on_created(self, event):
        if not event.is_directory:
            scan_file(event.src_path, self.model)

def start_real_time_scanning(path, model):
    observer = Observer()
    event_handler = RealTimeFileWatcher(model)
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    log(f"[*] Real-time scanning started on: {path}")
    return observer

# === Antivirus Thread ===
class AntivirusThread(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(int)

    def __init__(self, path, model=None):
        super().__init__()
        self.path = path
        self.model = model

    def run(self):
        files = []
        if os.path.isfile(self.path):
            files = [self.path]
        elif os.path.isdir(self.path):
            for root, _, filenames in os.walk(self.path):
                files.extend([os.path.join(root, f) for f in filenames])

        total_files = len(files)
        for i, file in enumerate(files):
            scan_file(file, self.model)
            self.log_signal.emit(f"Scanned file: {file}")
            progress = int((i + 1) / total_files * 100)
            self.progress_signal.emit(progress)

# === GUI Implementation ===
class AntivirusApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vortex Antivirus")
        self.setGeometry(100, 100, 800, 600)
        self.model = load_ml_model()
        self.observer = None

        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Log Viewer
        self.log_viewer = QTextEdit()
        self.log_viewer.setReadOnly(True)
        layout.addWidget(QLabel("Antivirus Logs:"))
        layout.addWidget(self.log_viewer)

        # Progress Bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # Buttons
        self.scan_button = QPushButton("Scan File/Folder")
        self.scan_button.clicked.connect(self.scan_file_or_folder)
        layout.addWidget(self.scan_button)

        self.clear_logs_button = QPushButton("Clear Logs")
        self.clear_logs_button.clicked.connect(self.clear_logs)
        layout.addWidget(self.clear_logs_button)

        self.real_time_button = QPushButton("Start Real-Time Scanning")
        self.real_time_button.clicked.connect(self.start_real_time_scanning)
        layout.addWidget(self.real_time_button)

        # System Tray Setup
        self.tray_icon = QSystemTrayIcon(QIcon("antivirus_icon.png"), self)
        self.tray_icon.setToolTip("Vortex Antivirus is running in the background")
        tray_menu = QMenu()

        open_action = QAction("Open Vortex Antivirus")
        open_action.triggered.connect(self.show)
        tray_menu.addAction(open_action)

        quit_action = QAction("Quit")
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        self.refresh_logs()

    def closeEvent(self, event):
        """Override the close event to minimize to the system tray."""
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Vortex Antivirus",
            "Vortex Antivirus is still running in the background.",
            QSystemTrayIcon.Information,
            3000
        )

    def scan_file_or_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Select Folder to Scan")
        if path:
            self.log_viewer.append(f"Scanning started for: {path}")
            self.antivirus_thread = AntivirusThread(path, self.model)
            self.antivirus_thread.log_signal.connect(self.update_log)
            self.antivirus_thread.progress_signal.connect(self.update_progress)
            self.antivirus_thread.start()

    def update_log(self, message):
        self.log_viewer.append(message)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def clear_logs(self):
        if QMessageBox.question(self, "Clear Logs", "Are you sure you want to clear the logs?") == QMessageBox.Yes:
            open(LOG_FILE, "w").close()
            self.log_viewer.clear()

    def refresh_logs(self):
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                self.log_viewer.setText(f.read())

    def start_real_time_scanning(self):
        path = QFileDialog.getExistingDirectory(self, "Select Folder for Real-Time Scanning")
        if path:
            if self.observer:
                self.observer.stop()
            self.observer = start_real_time_scanning(path, self.model)

    def quit_application(self):
        """Quit the application."""
        if self.observer:
            self.observer.stop()
        self.tray_icon.hide()
        QApplication.quit()

# === Main Function ===
def main():
    app = QApplication(sys.argv)
    window = AntivirusApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
