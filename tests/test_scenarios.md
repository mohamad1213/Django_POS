# 📋 TEST SCENARIO — Django POS Application (PPJ Pralon)

> **Versi:** 1.0 | **Tanggal:** 2026-09-01  
> **Aplikasi:** Django POS (Point of Sale) — PPJ Pralon  
> **Tujuan:** Memastikan semua fitur utama aplikasi berjalan dengan benar sesuai kebutuhan bisnis.

---

## 🗂️ DAFTAR MODUL

| No | Modul | Jumlah Skenario |
|----|-------|----------------|
| 1  | Autentikasi | 4 |
| 2  | Produk (Products) | 5 |
| 3  | Pelanggan (Customers) | 3 |
| 4  | Penjualan / POS (Sales) | 8 |
| 5  | Pembelian (Purchases) | 2 |
| 6  | Stok (Stock) | 3 |
| 7  | Transaksi Kas | 7 |
| 8  | Hutang & Piutang | 4 |
| 9  | Profit | 4 |
| 10 | Dashboard | 2 |
| 11 | Laporan (Reports) | 3 |
| **Total** | | **45** |

---

## 📦 SCENARIO 1 — AUTENTIKASI

### TS-AUTH-001: Login Pengguna Berhasil
- **Deskripsi:** Pengguna dapat login dengan username dan password valid.
- **Pre-condition:** Akun pengguna sudah terdaftar di sistem.
- **Langkah:**
  1. Buka `/accounts/login/`
  2. Masukkan username & password yang benar
  3. Klik tombol Login
- **Expected Result:** Login berhasil; diarahkan ke halaman dashboard.

### TS-AUTH-002: Login dengan Kredensial Salah
- **Deskripsi:** Login gagal jika username atau password salah.
- **Langkah:**
  1. Buka `/accounts/login/`
  2. Masukkan username/password yang salah
  3. Klik Login
- **Expected Result:** Pesan error tampil; pengguna tetap di halaman login.

### TS-AUTH-003: Proteksi Halaman (Login Required)
- **Deskripsi:** Halaman yang butuh autentikasi tidak dapat diakses tanpa login.
- **Pre-condition:** Pengguna belum login.
- **Langkah:**
  1. Akses langsung `/dashboard/`, `/sales/`, `/transaksi/`
- **Expected Result:** Redirect ke halaman login.

### TS-AUTH-004: Logout
- **Deskripsi:** Pengguna dapat logout dari sistem.
- **Pre-condition:** Pengguna sudah login.
- **Expected Result:** Sesi diakhiri; redirect ke halaman login.

---

## 📦 SCENARIO 2 — PRODUK

### TS-PROD-001: Tambah Produk Baru
- **Deskripsi:** Admin dapat menambah produk baru.
- **Pre-condition:** Pengguna login; kategori sudah ada.
- **Langkah:**
  1. Buka daftar produk → Klik "Tambah Produk"
  2. Isi nama, deskripsi, harga beli, harga jual, kategori, status
  3. Simpan
- **Expected Result:** Produk tersimpan; kode BRGxxxxxx di-generate otomatis.

### TS-PROD-002: Edit Produk
- **Deskripsi:** Pengguna dapat mengubah data produk.
- **Expected Result:** Data produk berhasil diperbarui.

### TS-PROD-003: Nonaktifkan Produk
- **Deskripsi:** Ubah status produk menjadi INACTIVE.
- **Expected Result:** Produk tidak muncul di daftar produk aktif.

### TS-PROD-004: Hapus Produk
- **Deskripsi:** Pengguna dapat menghapus produk.
- **Expected Result:** Produk terhapus dari sistem.

### TS-PROD-005: Pencarian Produk via API
- **Deskripsi:** API `/api/products/?q=<keyword>` mengembalikan produk yang sesuai.
- **Expected Result:** Response JSON berisi daftar produk dengan id & text.

---

## 📦 SCENARIO 3 — PELANGGAN

### TS-CUST-001: Tambah Pelanggan Baru
- **Deskripsi:** Pengguna dapat menambah data pelanggan.
- **Langkah:**
  1. Isi nama, nomor HP, alamat → Simpan
- **Expected Result:** Pelanggan tersimpan di daftar pelanggan milik user.

### TS-CUST-002: Generate Link WhatsApp
- **Deskripsi:** Sistem menghasilkan link WA untuk pelanggan yang memiliki nomor HP.
- **Expected Result:** Link `https://api.whatsapp.com/send?phone=62xxx` benar.

### TS-CUST-003: Edit Data Pelanggan
- **Deskripsi:** Pengguna dapat mengubah data pelanggan.
- **Expected Result:** Data pelanggan berhasil diperbarui.

---

## 📦 SCENARIO 4 — PENJUALAN (POS / SALES)

### TS-SALE-001: Transaksi Penjualan Lunas
- **Deskripsi:** Transaksi di mana pelanggan membayar penuh.
- **Pre-condition:** Produk & pelanggan ada; user login.
- **Langkah:**
  1. Buka `/sales/add/`
  2. Pilih produk + kuantitas, pilih pelanggan
  3. Masukkan jumlah bayar ≥ sub-total
  4. Submit via AJAX
- **Expected Result:**
  - Sale berhasil dibuat; nomor `PPJ-YYYYMMDD-XXXXXX` digenerate
  - Stok produk berkurang sesuai qty
  - Transaksi pengeluaran kas otomatis tercatat
  - Tidak ada hutang dibuat

### TS-SALE-002: Transaksi Penjualan Bayar DP (Tidak Lunas)
- **Deskripsi:** Pelanggan hanya membayar sebagian.
- **Expected Result:**
  - Transaksi tersimpan; stok berkurang
  - Pengeluaran kas = jumlah dibayar
  - Hutang otomatis dibuat sebesar selisih yang belum terbayar

### TS-SALE-003: Buat Pelanggan Baru Saat Transaksi
- **Deskripsi:** Sistem membuat pelanggan baru secara otomatis saat transaksi.
- **Langkah:**
  1. Isi field `new_customer_name` saat membuat transaksi
- **Expected Result:** Pelanggan baru terbuat otomatis; transaksi berhasil.

### TS-SALE-004: Lihat Daftar Penjualan
- **Deskripsi:** Pengguna melihat semua transaksi miliknya dengan pagination.
- **Expected Result:** Hanya data milik user yang tampil; 20 per halaman.

### TS-SALE-005: Lihat Detail Transaksi Penjualan
- **Deskripsi:** Lihat rincian produk, qty, harga, dan total per transaksi.
- **Expected Result:** Data detail tampil dengan benar.

### TS-SALE-006: Hapus Transaksi Penjualan
- **Deskripsi:** Menghapus transaksi dan mengembalikan stok.
- **Expected Result:** Transaksi terhapus; stok dikembalikan.

### TS-SALE-007: Cetak Nota PDF
- **Deskripsi:** Mencetak nota transaksi dalam format PDF.
- **Expected Result:** PDF berhasil dirender dengan data transaksi yang benar.

### TS-SALE-008: Transaksi Tanpa Produk Gagal
- **Deskripsi:** Submit tanpa memilih produk harus gagal.
- **Expected Result:** Response `400 Bad Request` dengan pesan error.

---

## 📦 SCENARIO 5 — PEMBELIAN (PURCHASES)

### TS-PURCH-001: Buat Transaksi Pembelian Baru
- **Deskripsi:** Catat transaksi pembelian (barang keluar ke pabrik/pembeli).
- **Expected Result:**
  - Transaksi tersimpan; nomor `KLR-YYYYMMDD-XXXXXX` digenerate
  - Pemasukan kas dicatat otomatis sebesar amount_payed

### TS-PURCH-002: Pembelian Tidak Lunas → Piutang Terbuat
- **Deskripsi:** Jika amount_payed < sub_total, piutang dibuat otomatis.
- **Expected Result:** Piutang terbuat di HutangPiutang sebesar selisih.

---

## 📦 SCENARIO 6 — STOK

### TS-STOCK-001: Lihat Laporan Stok
- **Deskripsi:** Melihat saldo stok semua produk aktif milik user.
- **Expected Result:** Total masuk, keluar, dan saldo tampil benar; KPI total jenis, total kg, nilai estimasi tepat.

### TS-STOCK-002: Tambah Stok Masuk (StockIn)
- **Deskripsi:** Mencatat barang masuk ke gudang.
- **Langkah:**
  1. Buka `/stok/create/` → Pilih produk, isi qty & referensi → Simpan
- **Expected Result:** StockIn tersimpan; stok bertambah otomatis via `StockIn.save()`.

### TS-STOCK-003: Hapus Data StockIn
- **Deskripsi:** Pengguna dapat menghapus catatan barang masuk.
- **Expected Result:** Data StockIn terhapus.

---

## 📦 SCENARIO 7 — TRANSAKSI KAS

### TS-TRX-001: Tambah Pemasukan Manual
- **Deskripsi:** Catat pemasukan kas secara manual.
- **Pre-condition:** Kategori transaksi sudah ada.
- **Langkah:**
  1. Buka `/transaksi/` → Isi form (jumlah, tanggal, kategori, keterangan)
  2. Pilih "Pemasukan" → Submit
- **Expected Result:** Pemasukan tersimpan; saldo bertambah.

### TS-TRX-002: Tambah Pengeluaran Manual
- **Deskripsi:** Catat pengeluaran kas secara manual.
- **Expected Result:** Pengeluaran tersimpan; saldo berkurang.

### TS-TRX-003: Edit Transaksi
- **Deskripsi:** Edit data transaksi yang sudah ada.
- **Expected Result:** Data berhasil diperbarui.

### TS-TRX-004: Hapus Satu Transaksi
- **Deskripsi:** Hapus satu transaksi kas.
- **Expected Result:** Transaksi terhapus.

### TS-TRX-005: Hapus Banyak Transaksi (Bulk Delete)
- **Deskripsi:** Hapus beberapa transaksi sekaligus.
- **Expected Result:** Semua transaksi yang dipilih terhapus.

### TS-TRX-006: Import via Excel (Berhasil)
- **Deskripsi:** Import data transaksi dari file Excel .xlsx.
- **Kolom yang dibutuhkan:** tanggal, keterangan, pemasukan, pengeluaran, kategori_id, owner
- **Expected Result:** Semua baris valid diimport; transaksi terbuat.

### TS-TRX-007: Import Excel dengan Tanggal Tidak Valid
- **Deskripsi:** Sistem menangani baris Excel dengan format tanggal salah.
- **Expected Result:** Baris salah dilewati; baris valid tetap diimport; warning tampil.

---

## 📦 SCENARIO 8 — HUTANG & PIUTANG

### TS-HP-001: Tambah Hutang Manual
- **Deskripsi:** Pengguna mencatat hutang secara manual.
- **Expected Result:** Hutang tersimpan; tampil di daftar.

### TS-HP-002: Tambah Piutang Manual
- **Deskripsi:** Pengguna mencatat piutang secara manual.
- **Expected Result:** Piutang tersimpan; tampil di daftar.

### TS-HP-003: Hapus Data Hutang/Piutang
- **Deskripsi:** Pengguna dapat menghapus data hutang/piutang.
- **Expected Result:** Data terhapus.

### TS-HP-004: Import Hutang/Piutang via Excel
- **Deskripsi:** Sistem mengimport data dari file Excel dengan kolom: tanggal, keterangan, pemasukan, pengeluaran.
- **Expected Result:** Data terimport dengan jenis hutang/piutang ditentukan otomatis.

---

## 📦 SCENARIO 9 — PROFIT

### TS-PROF-001: Input Data Profit (Multiple Items)
- **Deskripsi:** Input analisis profit dengan beberapa item sekaligus.
- **Langkah:**
  1. Buka `/profit/create/`
  2. Isi formset item (nama, berat, harga beli, harga jual)
  3. Isi global cost (solar, karung, ongkos kirim, dll)
  4. Submit
- **Expected Result:** Semua item tersimpan; semua field kalkulasi terisi otomatis.

### TS-PROF-002: Validasi Perhitungan Profit
- **Deskripsi:** Formula kalkulasi pada model `Profito2` menghasilkan nilai yang benar.
- **Formula:**
  - `berat_output = berat_input × (1 - susutan_persen / 100)`
  - `hpp_per_kg = harga_beli + Σ biaya_operasional`
  - `total_hpp = hpp_per_kg × berat_input`
  - `total_revenue = harga_jual × berat_output`
  - `profit = total_revenue - total_hpp`
  - `profit_margin = (profit / total_revenue) × 100`
  - `tabungan_total = profit × tabungan_persen / 100`
- **Expected Result:** Semua nilai sesuai formula di atas.

### TS-PROF-003: Tandai Profit Ditabung
- **Deskripsi:** Pengguna menandai profit sebagai sudah ditabung.
- **Expected Result:**
  - `profit_saved = True`
  - Entri Tabungan otomatis terbuat sebesar `tabungan_total`

### TS-PROF-004: Cegah Duplikasi Tabungan
- **Deskripsi:** Profit yang sudah ditabung tidak bisa ditabung lagi.
- **Expected Result:** Pesan "Profit sudah pernah ditabung" muncul; tidak ada entri baru.

---

## 📦 SCENARIO 10 — DASHBOARD

### TS-DASH-001: Tampilan Data Dashboard
- **Deskripsi:** Dashboard menampilkan ringkasan yang benar.
- **Expected Result:**
  - KPI pemasukan/pengeluaran harian, bulanan, tahunan benar
  - Saldo kas (pemasukan - pengeluaran) benar
  - Data hutang/piutang tampil
  - Chart produk terjual tampil

### TS-DASH-002: Isolasi Data per User
- **Deskripsi:** User hanya melihat data miliknya sendiri.
- **Expected Result:** Data user A tidak terlihat oleh user B.

---

## 📦 SCENARIO 11 — LAPORAN

### TS-LAP-001: Halaman Laporan
- **Deskripsi:** Pengguna dapat mengakses halaman laporan.
- **Expected Result:** Halaman tampil dengan ringkasan data yang benar.

### TS-LAP-002: Histori Transaksi Penjualan
- **Deskripsi:** Melihat histori semua transaksi penjualan.
- **Expected Result:** Data tampil lengkap; KPI (total transaksi, total pendapatan, rata-rata) benar.

### TS-LAP-003: Filter Status Pembayaran
- **Deskripsi:** Filter transaksi berdasarkan status LUNAS / BELUM LUNAS.
- **Langkah:**
  1. Buka `/transaksi-history/?status=LUNAS`
  2. Coba juga `?status=BELUM_LUNAS`
- **Expected Result:** Hanya transaksi dengan status yang sesuai yang tampil.

---

*Total: 45 Test Scenarios | Dokumen ini menjadi dasar pembuatan Test Case detail.*
