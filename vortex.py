import os
import sys
import time
import shutil
import hashlib
import threading
import psutil
import numpy as np
import tensorflow as tf
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
    QMenu,
    QAction
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QThread, Signal

# === Antivirus Core ===
SIGNATURES = {
    "44d88612fea8a8f36de82e1278abb02f": "EICAR-Test-File"
}
QUARANTINE_DIR = os.path.join(os.getcwd(), "quarantine")
LOG_FILE = "antivirus_log.txt"
MACHINE_LEARNING_MODEL_PATH = "ml_model.h5"  # Machine learning model for file classification
THREAT_DATABASE_URL = "https://example.com/api/threats"  # Placeholder for cloud threat database

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
    except Exception as e:
        log(f"[!] Failed to quarantine {path}: {e}")

def load_ml_model():
    try:
        model = tf.keras.models.load_model(MACHINE_LEARNING_MODEL_PATH)
        log("[*] Machine learning model loaded successfully.")
        return model
    except Exception as e:
        log(f"[!] Failed to load machine learning model: {e}")
        return None

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
        prediction = model.predict(np.array([extract_features(path)]))
        if prediction > 0.5:  # Example threshold
            log(f"[!!] Machine Learning threat detected: {path}")
            quarantine_file(path)
    else:
        log(f"[!] No threats detected: {path}")

def extract_features(path):
    file_size = os.path.getsize(path)
    with open(path, "rb") as f:
        data = f.read()
    byte_frequencies = np.array([data.count(i) for i in range(256)])  # Byte frequency histogram
    return np.concatenate([byte_frequencies, [file_size]])

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
