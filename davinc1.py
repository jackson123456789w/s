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

# Function to get shellcode as input (Python payload as bytecode)
def get_python_shellcode():
    print("Enter the path to your Python shellcode (payload) file:")
    file_path = input("> ").strip()
    
    try:
        with open(file_path, 'r') as f:
            python_code = f.read()
        
        # Convert Python code to bytes (as a payload)
        python_bytes = python_code.encode('utf-8')
        print(f"Successfully loaded Python shellcode from {file_path}")
        return python_bytes
    except Exception as e:
        print(f"Error reading Python shellcode from file: {e}")
        sys.exit(1)

# Function to generate polymorphic XOR encoded shellcode
def generate_shellcode(shellcode, key=0xAA):
    print("Encoding the shellcode...")
    encoded_shellcode = xor_encode(shellcode, key)
    return encoded_shellcode

# Function to generate Python script to decode and execute the encoded shellcode
def generate_python_file(encoded_shellcode):
    print("Enter the filename to save the encoded Python shellcode (e.g., encoded_payload.py):")
    file_name = input("> ").strip()

    # Create a Python script to decode and execute the payload
    script_content = f"""
import base64

def decode_payload():
    # Encoded shellcode (XOR encoded with feedback)
    encoded_shellcode = {list(encoded_shellcode)}

    # XOR decoding function
    def xor_decode(encoded_data, key):
        decoded_data = bytearray()
        feedback_key = key
        for byte in encoded_data:
            decoded_byte = byte ^ feedback_key
            decoded_data.append(decoded_byte)
            # Add feedback to modify the XOR key after each byte is decoded
            feedback_key = (feedback_key + decoded_byte) & 0xFF  # Ensure key stays within byte range (0-255)
        return decoded_data

    # Decode the shellcode
    decoded_shellcode = xor_decode(encoded_shellcode, 0xAA)  # Using same key for decoding
    exec(decoded_shellcode.decode('utf-8'))  # Execute the decoded Python shellcode

# Run the payload decoder
decode_payload()
    """

    try:
        with open(file_name, 'w') as f:
            f.write(script_content)
        print(f"Encoded Python shellcode saved as {file_name}")
    except Exception as e:
        print(f"Error saving Python file: {e}")
        sys.exit(1)

# Main function to execute the encoding and saving process
def main():
    # Step 1: Get the Python shellcode (payload)
    python_shellcode = get_python_shellcode()
    
    # Step 2: Ask for the XOR key and encode the payload
    key = random.randint(0, 255)  # Random key for XOR encoding (can be customized)
    
    # Step 3: Generate the XOR encoded shellcode
    encoded_shellcode = generate_shellcode(python_shellcode, key)
    
    # Step 4: Save the encoded shellcode as a Python script
    generate_python_file(encoded_shellcode)

# Run the main function
if __name__ == "__main__":
    main()
