from Crypto.Cipher import XOR
import os
import random

def xor_with_feedback(shellcode, key):
    encoded_shellcode = bytearray()
    feedback = 0

    for i in range(len(shellcode)):
        byte = shellcode[i]
        xor_byte = byte ^ key ^ feedback
        encoded_shellcode.append(xor_byte)

        # Additive feedback (simple example: feedback based on the XORed byte)
        feedback = (xor_byte + feedback) % 256  # Ensure feedback stays within byte range

        # Polymorphism: Modify key after each byte
        key = (key + random.randint(1, 255)) % 256

    return bytes(encoded_shellcode)

def save_encoded_shellcode(encoded_shellcode, save_path):
    with open(save_path, "wb") as f:
        f.write(encoded_shellcode)
    print(f"Shellcode saved to {save_path}")

def generate_shellcode_for_os():
    print("Enter your shellcode in hexadecimal format (e.g., 90 90 90 ...):")
    shellcode_input = input().strip()
    shellcode = bytes.fromhex(shellcode_input.replace(" ", ""))
    return shellcode

def main():
    print("Is the shellcode for Windows or Linux?")
    os_type = input("Enter 'Windows' or 'Linux': ").strip().lower()
    if os_type not in ['windows', 'linux']:
        print("Invalid choice! Please enter 'Windows' or 'Linux'.")
        return

    shellcode = generate_shellcode_for_os()

    # Generate a random key for XOR encoding (within byte range)
    key = random.randint(0, 255)

    # XOR and Additive Feedback encoding
    encoded_shellcode = xor_with_feedback(shellcode, key)

    # Save the encoded shellcode to a file
    print("Where would you like to save the encoded shellcode?")
    save_path = input("Enter the file path (e.g., encoded_shellcode.bin): ").strip()

    save_encoded_shellcode(encoded_shellcode, save_path)

if __name__ == "__main__":
    main()
