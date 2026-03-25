import socket
import select
import os

HOST = "0.0.0.0"
PORT = 6969
FILES_DIR = "files"
os.makedirs(FILES_DIR, exist_ok=True)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(5)
print(f"[*] Select server on {HOST}:{PORT}")

sockets = [server]



while True:
    read_ready = select.select(sockets, [], [])[0]

    for conn in read_ready:
        if conn == server:
            conn, addr = server.accept()
            sockets.append(conn)
            print(f"[+] Connected: {addr}")

        else:
            try:
                data = conn.recv(1024).decode().strip()

                if not data:
                    sockets.remove(conn)
                    conn.close()
                    print(f"[-] Disconnected")
                    continue

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
                    broadcast_msg = f"[SERVER] {addr[0]} uploaded file: {filename}"
                    for s in sockets:
                        if s != server and s != conn:
                            try:
                                s.sendall(broadcast_msg.encode())
                            except:
                                pass

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

            except Exception as e:
                print(f"[!] Error: {e}")
                sockets.remove(conn)
                conn.close()
