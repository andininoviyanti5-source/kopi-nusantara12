# Kopi Nusantara — Website E-Commerce UMKM

Website demo e-commerce kopi lokal berbasis **Python Flask + MySQL**.

## Fitur yang tersedia
- Homepage responsif, katalog, pencarian, kategori, pengurutan, dan detail produk.
- Registrasi, login, logout, dan password hashing.
- Keranjang belanja dengan update/hapus item.
- Checkout, pembuatan pesanan, simulasi pembayaran, dan riwayat pesanan.
- Dashboard admin ringkas dan perubahan status pesanan.
- Database MySQL dan data contoh produk.

> Catatan: pembayaran belum terhubung ke payment gateway sungguhan. Foto produk memakai URL gambar Unsplash sehingga membutuhkan internet. Fitur admin/produk lanjutan seperti CRUD produk dan laporan grafik dapat dikembangkan berikutnya.

## 1. Persiapan
Install Python 3.10+, MySQL Server atau XAMPP (MySQL), dan Visual Studio Code.

Buka folder project di VS Code. Buat virtual environment:

### Windows PowerShell
```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Jika PowerShell memblokir aktivasi, gunakan Command Prompt:
```bat
venv\\Scripts\\activate.bat
pip install -r requirements.txt
```

## 2. Buat database
1. Jalankan MySQL dari XAMPP atau MySQL Server.
2. Buka phpMyAdmin atau MySQL Workbench.
3. Import file `database/kopi_nusantara.sql`.
4. Salin `.env.example` menjadi `.env`.
5. Sesuaikan DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME di `.env`.

## 3. Buat akun admin
Daftarkan akun melalui halaman `/daftar`. Setelah itu, jalankan query berikut di phpMyAdmin untuk mengubah akun menjadi admin:

```sql
USE kopi_nusantara;
UPDATE users SET role='admin' WHERE email='email-kamu@example.com';
```

Logout lalu login kembali. Menu Admin akan muncul.

## 4. Jalankan website
```bash
python app.py
```
Buka browser: http://127.0.0.1:5000

## Struktur penting
- `app.py`: route dan logika aplikasi.
- `config.py`: konfigurasi.
- `db.py`: koneksi dan query MySQL.
- `database/kopi_nusantara.sql`: skema dan data contoh.
- `templates/`: halaman HTML Jinja2.
- `static/css/style.css`: desain.
- `static/js/main.js`: interaksi frontend.

## Catatan keamanan sebelum produksi
Ganti `SECRET_KEY`, gunakan HTTPS, nonaktifkan debug, tambahkan proteksi CSRF untuk seluruh form, validasi dan sanitasi lebih ketat, gunakan transaksi database untuk checkout, serta integrasikan payment gateway resmi jika menerima pembayaran sungguhan. Project ini ditujukan untuk pengembangan dan pengujian lokal.
