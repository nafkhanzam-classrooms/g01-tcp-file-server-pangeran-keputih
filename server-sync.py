import socket
import os

HOST = "0.0.0.0"
PORT = 6969
FILES_DIR = "files"
os.makedirs(FILES_DIR, exist_ok=True)


def handle_client(conn, addr):
    print(f"[+] Connected: {addr}")
    try:
        while True:
            data = conn.recv(1024).decode().strip()
            if not data:
                break

            if data == "/list":
                files = os.listdir(FILES_DIR)
                reply = "\n".join(files) if files else "(no files)"
                conn.sendall(reply.encode())

            elif data.startswith("/upload"):
                filename = data.split()[1]
                conn.sendall(b"READY")
                size = int(conn.recv(1024).decode())
                file_data = b""
                while len(file_data) < size:
                    file_data += conn.recv(4096)
                with open(os.path.join(FILES_DIR, filename), "wb") as f:
                    f.write(file_data)
                conn.sendall(b"OK")
                print(f"[+] Uploaded: {filename}")

            elif data.startswith("/download"):
                filename = data.split()[1]
                filepath = os.path.join(FILES_DIR, filename)
                if not os.path.exists(filepath):
                    conn.sendall(b"ERROR")
                else:
                    size = os.path.getsize(filepath)
                    conn.sendall(str(size).encode())
                    conn.recv(1024)
                    with open(filepath, "rb") as f:
                        conn.sendfile(f)
                    print(f"[+] Downloaded: {filename}")

            elif data.startswith("/broadcast"):
                msg = data[len("/broadcast "):].strip()
                print(f"[BROADCAST] {msg}")
                conn.sendall(b"OK")

            elif data == "/quit":
                break

    except Exception as e:
        print(f"[!] Error from {addr}: {e}")
    finally:
        conn.close()
        print(f"[-] Disconnected: {addr}")


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(1)
print(f"[*] Sync server on {HOST}:{PORT}")

while True:
    conn, addr = server.accept()
    handle_client(conn, addr)
