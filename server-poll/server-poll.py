import socket
import select
import os
import struct

HOST = '127.0.0.1'
PORT = 6969
FILES_DIR = 'server_files'
os.makedirs(FILES_DIR, exist_ok=True)

server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_sock.bind((HOST, PORT))
server_sock.listen(5)
server_sock.setblocking(False)

poll_obj = select.poll()
poll_obj.register(server_sock.fileno(), select.POLLIN)

fd_map = {server_sock.fileno(): server_sock}
addr_map = {}

print(f"[SERVER-POLL]")

while True:
    events = poll_obj.poll()
    
    for fd, event in events:
        sock = fd_map[fd]

        if sock is server_sock:
            conn, addr = server_sock.accept()
            conn.setblocking(True) 
            cfd = conn.fileno()
            fd_map[cfd] = conn
            addr_map[cfd] = addr
            poll_obj.register(cfd, select.POLLIN)
            print(f"[+] {addr} terhubung")
            continue

        elif event & select.POLLIN:
            try:
                data = sock.recv(1024).decode().strip()
                if not data: raise Exception()
            except:
                poll_obj.unregister(fd)
                sock.close()
                print(f"[-] {addr_map[fd]} terputus")
                del fd_map[fd]
                del addr_map[fd]
                continue

            # 1. PERINTAH /list
            if data == "/list":
                files = os.listdir(FILES_DIR)
                resp = "[SERVER] Daftar file: " + (", ".join(files) if files else "Kosong")
                sock.sendall(resp.encode())

            # 2. PERINTAH /upload <filename>
            elif data.startswith("/upload"):
                raw_filename = data.split()[1]
                filename = os.path.basename(raw_filename)
                sock.sendall(b"READY") 
                
                # Baca header 4 byte untuk mendapatkan 'length'
                header = sock.recv(4)
                if not header: continue
                filesize = struct.unpack(">I", header)[0]
                
                # Baca payload (data file) sesuai 'length' yang didapat
                file_data = b""
                while len(file_data) < filesize:
                    # Pastikan tidak membaca lebih dari sisa yang dibutuhkan
                    chunk = sock.recv(min(4096, filesize - len(file_data)))
                    if not chunk: break
                    file_data += chunk
                
                # Simpan ke folder server
                with open(os.path.join(FILES_DIR, filename), "wb") as f:
                    f.write(file_data)
                
                # Konfirmasi ke pengupload
                sock.sendall(f"SUCCESS: {filename} telah terupload".encode())
                print(f"[FILE] {addr_map[fd]} berhasil upload {filename}")

                # BROADCAST
                broadcast_msg = f"\n[PEMBERITAHUAN] File baru tersedia: '{filename}' (diupload oleh {addr_map[fd]})\n"
                for c_fd, c_sock in fd_map.items():
                    try:
                        c_sock.sendall(broadcast_msg.encode())
                    except:
                        pass

            # 3. PERINTAH /download <filename>
            elif data.startswith("/download"):
                filename = data.split()[1]
                filepath = os.path.join(FILES_DIR, filename)
                if os.path.exists(filepath):
                    filesize = os.path.getsize(filepath)

                    # Kirim header 4 byte biner 
                    header = struct.pack(">I", filesize)
                    sock.sendall(header)
                    
                    # Kirim isi file
                    with open(filepath, "rb") as f:
                        sock.sendall(f.read())
                    print(f"[SEND] {filename} berhasil dikirim ke {addr_map[fd]}")

                else:
                    # Kirim header 0 sebagai tanda file tidak ada/error
                    sock.sendall(struct.pack(">I", 0))

            # 4. PESAN BIASA (Abaikan atau print di server saja, jangan di-broadcast)
            else:
                print(f"[INFO] {addr_map[fd]} mengirim pesan non-perintah: {data}")