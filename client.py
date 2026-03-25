import socket
import os

HOST = "127.0.0.1"
PORT = 6969
os.makedirs("downloads", exist_ok=True)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))
print(f"[+] Connected to {HOST}:{PORT}")

while True:
    cmd = input(">>> ").strip()
    if not cmd:
        continue

    if cmd == "/list":
        sock.sendall(cmd.encode())
        reply = sock.recv(4096).decode()
        print(reply)

    elif cmd.startswith("/upload"):
        parts = cmd.split()
        if len(parts) < 2:
            print("Usage: /upload <filename>")
            continue
        filename = parts[1]
        if not os.path.exists(filename):
            print(f"File not found: {filename}")
            continue
        sock.sendall(cmd.encode())
        sock.recv(1024)
        size = os.path.getsize(filename)
        sock.sendall(str(size).encode())
        with open(filename, "rb") as f:
            sock.sendfile(f)
        reply = sock.recv(1024).decode()
        print(f"[+] Upload: {reply}")

    elif cmd.startswith("/download"):
        parts = cmd.split()
        if len(parts) < 2:
            print("Usage: /download <filename>")
            continue
        filename = parts[1]
        sock.sendall(cmd.encode())
        response = sock.recv(1024).decode().strip()
        if response == "ERROR":
            print(f"[!] File not found on server: {filename}")
        else:
            size = int(response)
            sock.sendall(b"ACK")
            file_data = b""
            while len(file_data) < size:
                file_data += sock.recv(4096)
            with open(os.path.join("downloads", filename), "wb") as f:
                f.write(file_data)
            print(f"[+] Downloaded '{filename}' -> downloads/{filename}")

    elif cmd == "/quit":
        break

    else:
        print("Unknown command")

sock.close()
print("[-] Disconnected.")
