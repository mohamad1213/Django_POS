import time
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from django.contrib.auth import get_user_model
from zetaapp.models import Kategori
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

# Ganti dengan lokasi ChromeDriver yang sudah diunduh
# PATH_TO_CHROMEDRIVER = "D:\template\template\zetaapp\tests\chromedriver.exe"

# service = Service(PATH_TO_CHROMEDRIVER)
# driver = webdriver.Chrome(service=service)
User = get_user_model()

class TransaksiTest(StaticLiveServerTestCase):
    def setUp(self):
        # Setup WebDriver (gunakan Chrome)
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        self.driver.maximize_window()

        # Buat user untuk login
        self.user = User.objects.create_user(username="tatam", password="tatam")
        
        # Buat kategori transaksi
        self.kategori = Kategori.objects.create(nama="Makanan")

    def tearDown(self):
        self.driver.quit()

    def test_tambah_transaksi(self):
        self.driver.get(f"{self.live_server_url}/accounts/login/")

        # 🔹 1. Login
        username_input = self.driver.find_element(By.NAME, "username")
        password_input = self.driver.find_element(By.NAME, "password")
        login_button = self.driver.find_element(By.TAG_NAME, "button")

        username_input.send_keys("tatam")
        password_input.send_keys("tatam")
        login_button.click()
        time.sleep(2)  # Tunggu halaman load

        # 🔹 2. Buka halaman transaksi
        self.driver.get(f"{self.live_server_url}/transaksi/")  
        time.sleep(2)

        # 🔹 3. Klik tombol "Tambah Transaksi"
        tambah_button = self.driver.find_element(By.XPATH, "//button[contains(text(),'Tambah Transaksi')]")
        tambah_button.click()
        time.sleep(2)

        # 🔹 4. Isi Form Transaksi
        tanggal_input = self.driver.find_element(By.NAME, "tanggal")
        transaksi_choice_input = self.driver.find_element(By.NAME, "transaksi_choice")
        kategori_input = self.driver.find_element(By.NAME, "kategori")
        jumlah_input = self.driver.find_element(By.NAME, "jumlah")
        keterangan_input = self.driver.find_element(By.NAME, "keterangan")
        submit_button = self.driver.find_element(By.XPATH, "//button[contains(text(),'Submit')]")

        tanggal_input.send_keys("10-03-2025")
        transaksi_choice_input.send_keys("Pemasukan")
        kategori_input.send_keys(self.kategori.nama)
        jumlah_input.send_keys("100000")
        keterangan_input.send_keys("Testing transaksi")

        # 🔹 5. Submit Form
        submit_button.click()
        time.sleep(2)

        # 🔹 6. Verifikasi apakah transaksi berhasil ditambahkan
        self.driver.get(f"{self.live_server_url}/transaksi/")
        time.sleep(2)
        body_text = self.driver.find_element(By.TAG_NAME, "body").text
        self.assertIn("Testing transaksi", body_text)
