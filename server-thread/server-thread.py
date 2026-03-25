import socket
import threading
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
server_sock.setblocking(True) 

clients = []
clients_lock = threading.Lock()

print(f"[SERVER-THREAD]")

def handle_client(conn, addr):
    """Handle individual client connection"""
    print(f"[+] {addr} terhubung")
    
    try:
        while True:
            try:
                data = conn.recv(1024).decode().strip()
                if not data: 
                    raise Exception()
            except:
                # Clean up this client
                with clients_lock:
                    if conn in clients:
                        clients.remove(conn)
                conn.close()
                print(f"[-] {addr} terputus")
                break

            # 1. PERINTAH /list
            if data == "/list":
                files = os.listdir(FILES_DIR)
                resp = "[SERVER] Daftar file: " + (", ".join(files) if files else "Kosong")
                conn.sendall(resp.encode())

            # 2. PERINTAH /upload <filename>
            elif data.startswith("/upload"):
                raw_filename = data.split()[1]
                filename = os.path.basename(raw_filename)
                conn.sendall(b"READY") 
                
                # Baca header 4 byte untuk mendapatkan 'length'
                header = conn.recv(4)
                if not header: continue
                filesize = struct.unpack(">I", header)[0]
                
                # Baca payload (data file) sesuai 'length' yang didapat
                file_data = b""
                while len(file_data) < filesize:
                    # Pastikan tidak membaca lebih dari sisa yang dibutuhkan
                    chunk = conn.recv(min(4096, filesize - len(file_data)))
                    if not chunk: break
                    file_data += chunk
                
                # Simpan ke folder server
                with open(os.path.join(FILES_DIR, filename), "wb") as f:
                    f.write(file_data)
                
                # Konfirmasi ke pengupload
                conn.sendall(f"SUCCESS: {filename} telah terupload".encode())
                print(f"[FILE] {addr} berhasil upload {filename}")

                # BROADCAST
                broadcast_msg = f"\n[PEMBERITAHUAN] File baru tersedia: '{filename}' (diupload oleh {addr})\n"
                with clients_lock:
                    for c in clients:
                        try:
                            if c != conn:  # Don't send to the uploader
                                c.sendall(broadcast_msg.encode())
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
                    conn.sendall(header)
                    
                    # Kirim isi file
                    with open(filepath, "rb") as f:
                        conn.sendall(f.read())
                    print(f"[SEND] {filename} berhasil dikirim ke {addr}")
                    
                else:
                    # Kirim header 0 sebagai tanda file tidak ada/error
                    conn.sendall(struct.pack(">I", 0))

            # 4. PESAN BIASA (Abaikan atau print di server saja, jangan di-broadcast)
            else:
                print(f"[INFO] {addr} mengirim pesan non-perintah: {data}")
                
    except Exception as e:
        print(f"[ERROR] {addr}: {e}")
    finally:
        # Ensure client is removed from list
        with clients_lock:
            if conn in clients:
                clients.remove(conn)
        conn.close()

while True:
    conn, addr = server_sock.accept()
    
    # Add to clients list
    with clients_lock:
        clients.append(conn)
    
    # Create thread for this client
    client_thread = threading.Thread(target=handle_client, args=(conn, addr))
    client_thread.daemon = True
    client_thread.start()