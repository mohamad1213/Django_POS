from django.test import LiveServerTestCase
from selenium.webdriver.chrome.webdriver import WebDriver
from zetaapp.models import *
from products.models import *
from sales.models import *
from customers.models import *

from django.contrib.auth.models import User

class FunctionalTest(LiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.selenium = WebDriver()
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def setUp(self):
        # Buat pengguna baru
        self.user = User.objects.create_user(username='testuser', password='password')
        self.karyawan = Karyawan.objects.create(name=self.user.username)
    def test_screenshot(self):
        # Membuat data
        task = Task.objects.create(title='Task 1', complete=False)
        kategori = Kategori.objects.create(nama='Kategori 1')
        hut_pegawai = HutPegawai.objects.create(pegawai=self.karyawan, jumlah=100, tanggal='2023-01-01', hutang_choice='H')
        transaksi = Transaksi.objects.create(owner=self.user, jumlah=200, tanggal='2023-01-01', keterangan='Transaksi 1', transaksi_choice='P', kategori=kategori)
        hutang_piutang = HutangPiutang.objects.create(owner=self.user, jumlah=300, tanggal='2023-01-01', hutang_choice='H')
        profito = Profito.objects.create(nama_suplayer='Suplayer 1', description='Description', date='2023-01-01', jumlah_brg=10, harga_jual=150, harga_beli=100)
        tabungan = Tabungan.objects.create(transaksi_choice='P', nominal=400, description='Description', date='2023-01-01')
        pegawai = Pegawai.objects.create(nama='Pegawai 1', nip='12345', jabatan='Jabatan 1', gaji=5000, tanggal_masuk='2023-01-01')
        
        # Buka halaman web yang ingin Anda uji
        self.selenium.get(self.live_server_url)  # Ganti URL sesuai kebutuhan Anda

        # Ambil tangkapan layar
        self.selenium.save_screenshot('screenshot.png')  # Menyimpan tangkapan layar sebagai screenshot.png
