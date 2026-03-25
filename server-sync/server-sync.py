import socket
import os
import struct

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
                header = b""
                while len(header) < 4:
                    header += conn.recv(4 - len(header))
                size = struct.unpack(">I", header)[0]
                file_data = b""
                while len(file_data) < size:
                    file_data += conn.recv(min(4096, size - len(file_data)))
                with open(os.path.join(FILES_DIR, filename), "wb") as f:
                    f.write(file_data)
                conn.sendall(b"OK")
                print(f"[+] Uploaded: {filename}")
                print(f"[BROADCAST] File baru tersedia: '{filename}' (diupload oleh {addr[0]})")

            elif data.startswith("/download"):
                filename = data.split()[1]
                filepath = os.path.join(FILES_DIR, filename)
                if not os.path.exists(filepath):
                    conn.sendall(struct.pack(">I", 0))
                else:
                    with open(filepath, "rb") as f:
                        file_data = f.read()
                    conn.sendall(struct.pack(">I", len(file_data)))
                    conn.sendall(file_data)
                    print(f"[+] Downloaded: {filename}")

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
