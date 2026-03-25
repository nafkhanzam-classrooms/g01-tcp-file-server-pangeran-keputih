import socket
import threading
import os
import struct
import select as _select

HOST = "127.0.0.1"
PORT = 6969
os.makedirs("downloads", exist_ok=True)

command_active = threading.Event()


def receive_broadcasts(sock):
    while True:
        try:
            if command_active.is_set():
                threading.Event().wait(0.01)
                continue
            ready = _select.select([sock], [], [], 0.1)[0]
            if ready and not command_active.is_set():
                msg = sock.recv(1024).decode().strip()
                if msg:
                    print(f"\n{msg}")
                    print(">>> ", end="", flush=True)
        except:
            break


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))
print(f"[+] Connected to {HOST}:{PORT}")

t = threading.Thread(target=receive_broadcasts, args=(sock,), daemon=True)
t.start()

while True:
    cmd = input(">>> ").strip()
    if not cmd:
        continue

    command_active.set()

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
        header = struct.pack(">I", size) 
        sock.sendall(header) 
        
        # Kirim isi file
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
        # Terima header 4 byte (Length Prefix)
        header = sock.recv(4)
        
        # Jika server mengirim pesan ERROR (biasanya string, bukan 4 byte biner yang valid)
        if not header or len(header) < 4:
            print(f"[!] Gagal menerima header dari server.")
            continue
            
        # Unpack header untuk mendapatkan ukuran file 
        # Jika header adalah indikator error (misal: 0), tangani di sini
        filesize = struct.unpack(">I", header)[0]
        
        if filesize == 0:
            print(f"[!] File tidak ditemukan di server")
        else:
            print(f"Mendownload {filename} ({filesize} bytes)...")
            file_data = b""
            while len(file_data) < filesize:
                # Membaca sisa byte yang diperlukan agar tidak mengambil data pesan lain 
                chunk = sock.recv(min(4096, filesize - len(file_data)))
                if not chunk: break
                file_data += chunk
            
            with open(os.path.join("downloads", filename), "wb") as f:
                f.write(file_data)
            print(f"[+] Downloaded '{filename}' -> downloads/{filename}")

    elif cmd == "/quit":
        command_active.clear()
        break

    else:
        print("Unknown command")

    command_active.clear()

sock.close()
print("[-] Disconnected.")