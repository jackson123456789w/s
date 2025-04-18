import marshal
import base64

def encrypt_file(file_path):
    with open(file_path, 'r') as f:
        source = f.read()

    # Compile the source code
    code = compile(source, file_path, 'exec')

    # Serialize and encode
    marshalled = marshal.dumps(code)
    encoded = base64.b64encode(marshalled).decode('utf-8')

    # Create the output file with decryption and execution logic
    output = f'''import marshal, base64

def run_encrypted():
    data = base64.b64decode({repr(encoded)})
    code = marshal.loads(data)
    exec(code, globals())  # Use globals so imports like argparse work properly

if __name__ == '__main__':
    run_encrypted()
'''

    # Save the encrypted file
    output_file = file_path.replace('.py', '_encrypted.py')
    with open(output_file, 'w') as f:
        f.write(output)
    
    print(f'Encrypted file saved as: {output_file}')

if __name__ == '__main__':
    file_to_encrypt = input("Enter the file to encrypt: ")
    encrypt_file(file_to_encrypt)
