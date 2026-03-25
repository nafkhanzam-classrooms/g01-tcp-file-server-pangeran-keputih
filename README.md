[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/mRmkZGKe)
# Network Programming - Assignment G01

## Anggota Kelompok
| Nama           | NRP        | Kelas     |
| ---            | ---        | ----------|
| Christian Mikaxelo               |    5025241178        |   C        |
|                |            |           |

## Link Youtube (Unlisted)
Link ditaruh di bawah ini
```

```

## Penjelasan Program

### server-sync.py
Server synchronous (blocking) hanya melayani satu client dalam satu waktu.
- `socket.listen(1)` hanya antri 1 koneksi
- `accept()` blocking, menunggu client masuk
- `conn.recv()` blocking, menunggu data dari client
- `handle_client()` memproses semua command client hingga disconnect, baru terima client berikutnya


### server-select.py
Server non-blocking menggunakan I/O multiplexing bisa melayani banyak client sekaligus dalam satu thread.
- `select.select(sockets, [], [])` untuk cek semua socket, return yang sudah ready
- `sockets` list berisi server socket dan semua client socket yang aktif
- `server.accept()` dipanggil hanya ketika `select` mendeteksi koneksi client baru
- `conn.recv()` dipanggil hanya ketika `select` mendeteksi data masuk
- setelah upload berhasil, server iterasi semua socket aktif dan kirim notifikasi ke semua client lain

## Screenshot Hasil

### Server Sync
![sync](/assets/sync.png)

dari test berikut dapat dilihat bahwa server hanya memberikan response kepada 1 client saja, sementara client yang mencoba connect, tidak bisa karena blocking dari server. Bahkan mencoba /list saja tidak bisa. Dengan ini, maka sesuai dengan implementasi sync yaitu blocking

### Server Select
![select](/assets/select.png)

dari test berikut dapat dilihat bahwa client 1 dan 2 dapat connect ke server dan setiap requestnya dapat diproses secara synchronous. Namun, delay nya tidak terasa karena request yang dilakukan sederhana dan terjadi di local sehingga sangat cepat.

Dapat dilihat juga server broadcast ke semua client lain ketika ada file yang di-upload. Client menggunakan background thread untuk menerima broadcast, namun untuk menghindari race condition, digunakan `threading.Event` (`command_active`) broadcast thread di-pause saat main thread sedang mengeksekusi command, lalu diaktifkan kembali setelah selesai.

Untuk transfer file, digunakan **length prefix** (4-byte big-endian header) sebagai framing server kirim ukuran file terlebih dahulu, lalu client baca sejumlah byte tersebut, sehingga data antar pesan tidak tercampur.