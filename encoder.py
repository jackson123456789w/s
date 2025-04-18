import marshal
import base64

def encrypt_file(file_path):
    with open(file_path, 'r') as f:
        source = f.read()

    code = compile(source, file_path, 'exec')
    marshalled = marshal.dumps(code)
    encoded = base64.b64encode(marshalled).decode('utf-8')

    output = f"""import marshal, base64

def run_encrypted():
    data = base64.b64decode({repr(encoded)})
    code = marshal.loads(data)
    exec(code)

if __name__ == '__main__':
    run_encrypted()
"""

    output_file = file_path.replace('.py', 'x.py')
    with open(output_file, 'w') as f:
        f.write(output)

    print(f'Encrypted file saved as: {output_file}')

if __name__ == '__main__':
    file_to_encrypt = input("Enter the file to encrypt: ")
    encrypt_file(file_to_encrypt)
