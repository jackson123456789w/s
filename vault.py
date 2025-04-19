import os
import base64
import marshal
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes

BLOCK_SIZE = 16  # AES block size
KEY_SIZE = 32    # AES-256 key size
SECTOR_SIZE = 512  # Standard disk sector size

class VaultLocker:
    def __init__(self, pin):
        self.pin = pin
        self.key = self.generate_key(pin)

    def generate_key(self, pin):
        # Derive a 32-byte AES key from the PIN
        return base64.urlsafe_b64encode(pin.encode('utf-8')).ljust(KEY_SIZE)[:KEY_SIZE]

    def encrypt_disk(self, disk_path):
        # Encrypt the entire disk at the block level
        with open(disk_path, 'r+b') as disk:
            while True:
                sector = disk.read(SECTOR_SIZE)
                if not sector:  # End of disk
                    break
                if len(sector) < SECTOR_SIZE:
                    sector = pad(sector, SECTOR_SIZE)  # Pad the last sector if needed
                cipher = AES.new(self.key, AES.MODE_CBC)
                encrypted_sector = cipher.iv + cipher.encrypt(sector)
                disk.seek(-len(sector), os.SEEK_CUR)
                disk.write(encrypted_sector)

    def create_vault_reader(self, output_path):
        # Generate VaultReader code with the encrypted PIN
        encrypted_pin = base64.b64encode(marshal.dumps(self.key)).decode('utf-8')

        vault_reader_code = f"""
import os
import base64
import marshal
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

BLOCK_SIZE = 16
SECTOR_SIZE = 512

def decrypt_disk(disk_path, key):
    with open(disk_path, 'r+b') as disk:
        while True:
            iv = disk.read(BLOCK_SIZE)
            if not iv:  # End of disk
                break
            encrypted_sector = disk.read(SECTOR_SIZE)
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted_sector = unpad(cipher.decrypt(encrypted_sector), SECTOR_SIZE)
            disk.seek(-len(encrypted_sector) - BLOCK_SIZE, os.SEEK_CUR)
            disk.write(decrypted_sector)

def main():
    encrypted_key = "{encrypted_pin}"
    key = marshal.loads(base64.b64decode(encrypted_key))
    pin = input("Enter PIN to unlock USB: ")
    derived_key = base64.urlsafe_b64encode(pin.encode('utf-8')).ljust(32)[:32]
    if derived_key != key:
        print("Invalid PIN! Access denied.")
        return
    usb_path = input("Enter the USB device path to unlock (e.g., /dev/sdb): ")
    decrypt_disk(usb_path, key)
    print("USB unlocked successfully!")

if __name__ == "__main__":
    main()
"""

        with open(output_path, 'w') as f:
            f.write(vault_reader_code)

if __name__ == "__main__":
    usb_path = input("Enter the USB device path to encrypt (e.g., /dev/sdb): ")
    pin = input("Enter a PIN for decryption: ")
    locker = VaultLocker(pin)

    print("Encrypting USB...")
    locker.encrypt_disk(usb_path)
    print("Disk encryption complete!")

    print("Generating VaultReader...")
    output_path = input("Enter the path to save VaultReader (e.g., usbx-01.py): ")
    locker.create_vault_reader(output_path)
    print(f"VaultReader created at {output_path}")
