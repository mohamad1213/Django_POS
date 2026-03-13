from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

class TransaksiSeleniumTests(StaticLiveServerTestCase):
    def setUp(self):
        """Inisialisasi Selenium WebDriver."""
        self.driver = webdriver.Chrome()  # Ganti sesuai WebDriver yang digunakan
        self.driver.maximize_window()
    
    def tearDown(self):
        """Tutup browser setelah pengujian selesai."""
        self.driver.quit()

    def test_transaksi_flow(self):
        """
        Uji alur transaksi: 
        1. Login
        2. Tambah pengeluaran
        3. Tambah pemasukan
        4. Periksa hasil perhitungan
        """
        driver = self.driver
        driver.get(f"{self.live_server_url}/accounts/login/")  # Sesuaikan dengan URL login
        
        # **1️⃣ Login sebagai pengguna**
        username_input = driver.find_element(By.NAME, "username")
        password_input = driver.find_element(By.NAME, "password")
        username_input.send_keys("tatam")  # Gantilah dengan username yang valid
        password_input.send_keys("tatam")
        password_input.send_keys(Keys.RETURN)
        time.sleep(2)  # Tunggu redirect

        # **2️⃣ Tambah Pengeluaran**
        driver.get(f"{self.live_server_url}/transaksi/add/")  # Sesuaikan dengan URL form transaksi
        driver.find_element(By.NAME, "jumlah").send_keys("100000")  # Rp100.000
        driver.find_element(By.NAME, "tanggal").send_keys("2024-03-01")
        driver.find_element(By.NAME, "transaksi_choice").send_keys("Pengeluaran")
        driver.find_element(By.NAME, "keterangan").send_keys("Pembelian bahan baku")
        driver.find_element(By.ID, "submit").click()
        time.sleep(2)

        # **3️⃣ Tambah Pemasukan**
        driver.get(f"{self.live_server_url}/transaksi/")
        driver.find_element(By.NAME, "jumlah").send_keys("150000")  # Rp150.000
        driver.find_element(By.NAME, "tanggal").send_keys("2024-03-05")
        driver.find_element(By.NAME, "transaksi_choice").send_keys("Pemasukan")
        driver.find_element(By.NAME, "keterangan").send_keys("Penjualan produk")
        driver.find_element(By.ID, "submit").click()
        time.sleep(2)

        # **4️⃣ Cek Hasil Perhitungan**
        driver.get(f"{self.live_server_url}/transaksi/")  # Halaman daftar transaksi
        profit_loss_element = driver.find_element(By.ID, "profit_loss")  # Pastikan ada elemen ini di template
        self.assertIn("50,000", profit_loss_element.text)  # Cek apakah keuntungannya benar
