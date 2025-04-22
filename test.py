import random
import sys

# XOR encoding function with polymorphism (feedback mechanism)
def xor_encode(shellcode, key):
    encoded_shellcode = bytearray()
    feedback_key = key
    for byte in shellcode:
        encoded_byte = byte ^ feedback_key
        encoded_shellcode.append(encoded_byte)
        # Add feedback to modify the XOR key after each byte is encoded
        feedback_key = (feedback_key + encoded_byte) & 0xFF  # Ensure key stays within byte range (0-255)
    return encoded_shellcode

# Function to get shellcode as input (binary data)
def get_shellcode_input():
    print("Enter the path to your shellcode binary file:")
    file_path = input("> ").strip()
    
    try:
        with open(file_path, 'rb') as f:
            shellcode = f.read()
        print(f"Successfully loaded shellcode from {file_path}")
        return shellcode
    except Exception as e:
        print(f"Error reading shellcode from file: {e}")
        sys.exit(1)

# Function to generate polymorphic XOR encoded shellcode
def generate_shellcode(shellcode, key=0xAA):
    print("Encoding the shellcode...")
    encoded_shellcode = xor_encode(shellcode, key)
    return encoded_shellcode

# Function to prompt the user for the file name and save the shellcode
def save_shellcode(encoded_shellcode):
    print("Enter the filename to save the encoded shellcode (e.g., encoded_shellcode.bin):")
    file_name = input("> ").strip()
    
    try:
        with open(file_name, 'wb') as f:
            f.write(encoded_shellcode)
        print(f"Encoded shellcode saved as {file_name}")
    except Exception as e:
        print(f"Error saving file: {e}")
        sys.exit(1)

# Main function to execute the encoding process
def main():
    # Step 1: Get the shellcode from user input
    shellcode = get_shellcode_input()
    
    # Step 2: Ask for the platform (Windows or Linux)
    platform = input("Choose platform (windows/linux): ").strip().lower()
    if platform not in ['windows', 'linux']:
        print("Invalid platform. Exiting...")
        sys.exit(1)
    
    # Step 3: Choose a random key for XOR encoding (you can also specify your own key)
    key = random.randint(0, 255)  # Random key for XOR encoding
    
    # Step 4: Generate the polymorphic XOR encoded shellcode
    encoded_shellcode = generate_shellcode(shellcode, key)
    
    # Step 5: Save the encoded shellcode to a file
    save_shellcode(encoded_shellcode)

# Run the main function
if __name__ == "__main__":
    main()
