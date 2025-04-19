import os
import base64
import marshal
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes

BLOCK_SIZE = 16       # AES block size
KEY_SIZE = 32         # AES-256 key size
SECTOR_SIZE = 512     # Disk sector size
PBKDF2_ITER = 100_000 # Key derivation iterations

class VaultLocker:
    def __init__(self, pin, salt=None):
        self.pin = pin
        self.salt = salt or get_random_bytes(16)
        self.key = self.generate_key(pin, self.salt)

    def generate_key(self, pin, salt):
        return PBKDF2(pin, salt, dkLen=KEY_SIZE, count=PBKDF2_ITER)

    def encrypt_disk(self, disk_path):
        with open(disk_path, 'r+b') as disk:
            while True:
                sector = disk.read(SECTOR_SIZE)
                if not sector:
                    break
                if len(sector) < SECTOR_SIZE:
                    sector += b'\x00' * (SECTOR_SIZE - len(sector))

                iv = get_random_bytes(BLOCK_SIZE)
                cipher = AES.new(self.key, AES.MODE_CBC, iv)
                encrypted_sector = cipher.encrypt(sector)

                disk.seek(-SECTOR_SIZE, os.SEEK_CUR)
                disk.write(iv + encrypted_sector)  # Write IV + encrypted data

    def create_vault_reader(self, output_path):
        encrypted_key_blob = marshal.dumps({
            'salt': self.salt,
            'pbkdf2_iter': PBKDF2_ITER
        })
        encoded_blob = base64.b64encode(encrypted_key_blob).decode()

        vault_reader_code = f'''\
import os
import base64
import marshal
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2

BLOCK_SIZE = 16
SECTOR_SIZE = 512
KEY_SIZE = 32

def decrypt_disk(disk_path, pin, salt, iterations):
    key = PBKDF2(pin, salt, dkLen=KEY_SIZE, count=iterations)
    with open(disk_path, 'r+b') as disk:
        while True:
            iv = disk.read(BLOCK_SIZE)
            if not iv:
                break
            encrypted_sector = disk.read(SECTOR_SIZE)
            if len(encrypted_sector) < SECTOR_SIZE:
                break  # corrupted or incomplete
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted_sector = cipher.decrypt(encrypted_sector)
            disk.seek(-SECTOR_SIZE - BLOCK_SIZE, os.SEEK_CUR)
            disk.write(decrypted_sector)

def main():
    metadata = base64.b64decode("{encoded_blob}")
    params = marshal.loads(metadata)
    pin = input("Enter PIN to unlock USB: ")
    path = input("Enter the USB device path (e.g., /dev/sdb): ")
    decrypt_disk(path, pin, params['salt'], params['pbkdf2_iter'])
    print("USB unlocked successfully!")

if __name__ == "__main__":
    main()
'''

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
    output_path = input("Enter the path to save VaultReader (e.g., vault_reader.py): ")
    locker.create_vault_reader(output_path)
    print(f"VaultReader created at {output_path}")
