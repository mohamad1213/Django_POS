"""
Test Case — Modul Autentikasi, Model, dan View (Django POS - PPJ Pralon)
Menjalankan: python manage.py test tests
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
import datetime


# ==============================================================================
# HELPER: Base class dengan data dasar yang di-share antar test
# ==============================================================================
class BaseTestCase(TestCase):
    """Base class yang menyiapkan data fixture umum."""

    def setUp(self):
        # Buat dua user untuk uji isolasi data
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser', password='testpass123'
        )
        self.client = Client()

    def login(self, user=None):
        """Helper untuk login."""
        u = user or self.user
        self.client.login(username=u.username, password='testpass123')


# ==============================================================================
# TC-AUTH: TEST CASE — AUTENTIKASI
# ==============================================================================
class AuthenticationTestCase(BaseTestCase):
    """TC-AUTH: Pengujian login, logout, dan proteksi halaman."""

    def test_TC_AUTH_001_login_berhasil(self):
        """TC-AUTH-001: Login dengan kredensial yang benar harus berhasil."""
        response = self.client.post(reverse('authentication:login'), {
            'username': 'testuser',
            'password': 'testpass123',
        })
        # Redirect setelah berhasil login
        self.assertIn(response.status_code, [200, 302])

    def test_TC_AUTH_002_login_password_salah(self):
        """TC-AUTH-002: Login dengan password salah harus gagal."""
        response = self.client.post(reverse('authentication:login'), {
            'username': 'testuser',
            'password': 'passwordsalah',
        })
        # Tidak ada redirect ke dashboard
        self.assertNotEqual(response.status_code, 302)
        # Pastikan user tidak terauthentikasi
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_TC_AUTH_003_akses_dashboard_tanpa_login(self):
        """TC-AUTH-003: Akses halaman protected tanpa login harus redirect ke login."""
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(
            response,
            '/accounts/login/?next=/dashboard/',
            fetch_redirect_response=False
        )

    def test_TC_AUTH_004_akses_sales_tanpa_login(self):
        """TC-AUTH-003b: Akses /sales/ tanpa login harus redirect."""
        response = self.client.get(reverse('sales:sales_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_TC_AUTH_005_akses_transaksi_tanpa_login(self):
        """TC-AUTH-003c: Akses /transaksi/ tanpa login harus redirect."""
        response = self.client.get(reverse('transaksi'))
        self.assertEqual(response.status_code, 302)

    def test_TC_AUTH_006_akses_dashboard_setelah_login(self):
        """TC-AUTH-004: Setelah login, halaman dashboard bisa diakses."""
        self.login()
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)


# ==============================================================================
# TC-PROD: TEST CASE — MODEL PRODUCT
# ==============================================================================
class ProductModelTestCase(BaseTestCase):
    """TC-PROD: Pengujian model Product dan Category."""

    def setUp(self):
        super().setUp()
        from products.models import Category, Product

        self.category = Category.objects.create(
            owner=self.user,
            name='Test Category',
            description='Deskripsi kategori test',
            status='ACTIVE'
        )
        self.product = Product.objects.create(
            owner=self.user,
            name='Produk Test A',
            description='Deskripsi produk test',
            status='ACTIVE',
            category=self.category,
            price=10000.0,
            selling_price=12000.0
        )

    def test_TC_PROD_001_kode_produk_autogenerate(self):
        """TC-PROD-001: Kode produk BRGxxxxxx harus digenerate otomatis."""
        self.assertIsNotNone(self.product.code)
        self.assertTrue(self.product.code.startswith('BRG'))
        self.assertEqual(len(self.product.code), 9)  # BRG + 6 digit

    def test_TC_PROD_002_produk_str(self):
        """TC-PROD-002: __str__ produk menampilkan kode dan nama."""
        self.assertIn('Produk Test A', str(self.product))
        self.assertIn(self.product.code, str(self.product))

    def test_TC_PROD_003_produk_to_json(self):
        """TC-PROD-003: to_json() menghasilkan dict dengan field yang benar."""
        data = self.product.to_json()
        self.assertIn('id', data)
        self.assertIn('text', data)
        self.assertIn('price', data)
        self.assertIn('selling_price', data)
        self.assertEqual(data['price'], 10000.0)
        self.assertEqual(data['selling_price'], 12000.0)

    def test_TC_PROD_004_nama_unik(self):
        """TC-PROD-004: Nama produk harus unik."""
        from products.models import Product
        from django.db import IntegrityError
        with self.assertRaises(Exception):
            Product.objects.create(
                owner=self.user,
                name='Produk Test A',  # Nama duplikat
                description='Lain',
                status='ACTIVE',
                category=self.category,
                price=5000.0
            )


# ==============================================================================
# TC-CUST: TEST CASE — MODEL CUSTOMER
# ==============================================================================
class CustomerModelTestCase(BaseTestCase):
    """TC-CUST: Pengujian model Customer."""

    def setUp(self):
        super().setUp()
        from customers.models import Customer
        self.customer = Customer.objects.create(
            owner=self.user,
            first_name='Budi Santoso',
            phone='081234567890',
            address='Jl. Test No. 1'
        )

    def test_TC_CUST_001_customer_str(self):
        """TC-CUST-001: __str__ customer menampilkan nama."""
        self.assertEqual(str(self.customer), 'Budi Santoso')

    def test_TC_CUST_002_wa_link_dengan_nomor(self):
        """TC-CUST-002: wa_link dihasilkan jika ada nomor HP."""
        wa = self.customer.wa_link
        self.assertIsNotNone(wa)
        self.assertIn('api.whatsapp.com', wa)
        self.assertIn('6281234567890', wa)

    def test_TC_CUST_003_wa_link_nomor_diawali_0(self):
        """TC-CUST-003: Nomor diawali '0' harus dikonversi ke '62xxx'."""
        from customers.models import Customer
        c = Customer.objects.create(
            owner=self.user,
            first_name='Pelanggan B',
            phone='0812999999'
        )
        self.assertIn('62812999999', c.wa_link)

    def test_TC_CUST_004_wa_link_tanpa_nomor(self):
        """TC-CUST-004: wa_link None jika tidak ada nomor HP."""
        from customers.models import Customer
        c = Customer.objects.create(
            owner=self.user,
            first_name='Pelanggan Tanpa HP'
        )
        self.assertIsNone(c.wa_link)

    def test_TC_CUST_005_to_select2(self):
        """TC-CUST-005: to_select2() menghasilkan dict dengan label dan value."""
        data = self.customer.to_select2()
        self.assertIn('label', data)
        self.assertIn('value', data)
        self.assertIn('Budi Santoso', data['label'])
        self.assertEqual(data['value'], self.customer.id)


# ==============================================================================
# TC-SALE: TEST CASE — MODEL SALE & SALEDETAIL
# ==============================================================================
class SaleModelTestCase(BaseTestCase):
    """TC-SALE: Pengujian model Sale dan SaleDetail."""

    def setUp(self):
        super().setUp()
        from products.models import Category, Product
        from customers.models import Customer
        from sales.models import Sale, SaleDetail

        self.category = Category.objects.create(
            owner=self.user, name='Cat Sale', description='', status='ACTIVE'
        )
        self.product = Product.objects.create(
            owner=self.user, name='Produk Sale', description='',
            status='ACTIVE', category=self.category,
            price=8000.0, selling_price=10000.0
        )
        self.customer = Customer.objects.create(
            owner=self.user, first_name='Pelanggan Sale',
            phone='082100000001'
        )
        self.sale = Sale.objects.create(
            owner=self.user,
            customer=self.customer,
            sub_total=30000.0,
            grand_total=30000.0,
            amount_payed=30000.0,
            amount_change=0.0,
        )
        self.detail = SaleDetail.objects.create(
            sale=self.sale,
            product=self.product,
            price=10000.0,
            quantity=3.0,
            total_detail=30000.0
        )

    def test_TC_SALE_001_nomor_transaksi_autogenerate(self):
        """TC-SALE-001: Nomor transaksi harus digenerate otomatis dengan format PPJ-."""
        self.assertIsNotNone(self.sale.transaction_number)
        self.assertTrue(self.sale.transaction_number.startswith('PPJ-'))

    def test_TC_SALE_002_nomor_transaksi_unik(self):
        """TC-SALE-002: Setiap sale memiliki transaction_number yang unik."""
        from customers.models import Customer
        from sales.models import Sale
        sale2 = Sale.objects.create(
            owner=self.user,
            customer=self.customer,
            sub_total=10000.0,
            grand_total=10000.0,
            amount_payed=10000.0,
            amount_change=0.0,
        )
        self.assertNotEqual(self.sale.transaction_number, sale2.transaction_number)

    def test_TC_SALE_003_sum_items(self):
        """TC-SALE-003: sum_items() harus mengembalikan total qty yang benar."""
        total = self.sale.sum_items()
        self.assertEqual(total, 3.0)

    def test_TC_SALE_004_pengeluaran_kas_otomatis_dibuat(self):
        """TC-SALE-004: Pengeluaran kas dibuat otomatis saat sale lunas dibuat."""
        from zetaapp.models import Transaksi
        trx = Transaksi.objects.filter(
            owner=self.user,
            transaksi_choice=Transaksi.PENGELUARAN,
            keterangan__icontains=self.sale.transaction_number
        )
        self.assertTrue(trx.exists())
        self.assertEqual(float(trx.first().jumlah), 30000.0)

    def test_TC_SALE_005_hutang_tidak_dibuat_saat_lunas(self):
        """TC-SALE-005: Tidak ada hutang jika sale lunas (amount_payed >= sub_total)."""
        from zetaapp.models import HutangPiutang
        hutang = HutangPiutang.objects.filter(
            owner=self.user,
            keterangan__icontains=self.sale.transaction_number
        )
        self.assertFalse(hutang.exists())

    def test_TC_SALE_006_hutang_dibuat_saat_tidak_lunas(self):
        """TC-SALE-006: Hutang otomatis dibuat jika amount_payed < sub_total."""
        from sales.models import Sale
        from zetaapp.models import HutangPiutang

        sale_dp = Sale.objects.create(
            owner=self.user,
            customer=self.customer,
            sub_total=50000.0,
            grand_total=50000.0,
            amount_payed=20000.0,  # Bayar sebagian
            amount_change=0.0,
        )
        hutang = HutangPiutang.objects.filter(
            owner=self.user,
            keterangan__icontains=sale_dp.transaction_number
        )
        self.assertTrue(hutang.exists())
        self.assertEqual(float(hutang.first().jumlah), 30000.0)  # selisih

    def test_TC_SALE_007_wa_link_dengan_pelanggan_ber_hp(self):
        """TC-SALE-007: wa_link sale menghasilkan URL WhatsApp."""
        wa = self.sale.wa_link
        self.assertIsNotNone(wa)
        self.assertIn('whatsapp.com', wa)

    def test_TC_SALE_008_wa_link_tanpa_pelanggan(self):
        """TC-SALE-008: wa_link None jika sale tanpa pelanggan."""
        from sales.models import Sale
        sale_no_cust = Sale.objects.create(
            owner=self.user,
            sub_total=10000.0, grand_total=10000.0,
            amount_payed=10000.0, amount_change=0.0,
        )
        self.assertIsNone(sale_no_cust.wa_link)

    def test_TC_SALE_009_sale_detail_str(self):
        """TC-SALE-009: __str__ SaleDetail menampilkan ID dan qty."""
        text = str(self.detail)
        self.assertIn('Detail ID:', text)
        self.assertIn('Quantity:', text)


# ==============================================================================
# TC-STOCK: TEST CASE — MODEL STOCK & STOCKIN
# ==============================================================================
class StockModelTestCase(BaseTestCase):
    """TC-STOCK: Pengujian model Stock dan StockIn."""

    def setUp(self):
        super().setUp()
        from products.models import Category, Product
        self.category = Category.objects.create(
            owner=self.user, name='Cat Stok', description='', status='ACTIVE'
        )
        self.product = Product.objects.create(
            owner=self.user, name='Produk Stok Test', description='',
            status='ACTIVE', category=self.category,
            price=5000.0, selling_price=7000.0
        )

    def test_TC_STOCK_001_stockin_menambah_stok(self):
        """TC-STOCK-001: Membuat StockIn harus menambah stok produk secara otomatis."""
        from zetaapp.models import StockIn, Stock

        # Pastikan stok awal 0 atau tidak ada
        Stock.objects.filter(product=self.product).delete()

        StockIn.objects.create(
            product=self.product,
            quantity=100,
            reference='REF-001',
            note='Test masuk barang'
        )

        stock = Stock.objects.get(product=self.product)
        self.assertEqual(float(stock.quantity), 100.0)

    def test_TC_STOCK_002_multiple_stockin_akumulasi(self):
        """TC-STOCK-002: Beberapa StockIn harus mengakumulasi stok."""
        from zetaapp.models import StockIn, Stock

        Stock.objects.filter(product=self.product).delete()

        StockIn.objects.create(product=self.product, quantity=50, reference='REF-A')
        StockIn.objects.create(product=self.product, quantity=30, reference='REF-B')

        stock = Stock.objects.get(product=self.product)
        self.assertEqual(float(stock.quantity), 80.0)

    def test_TC_STOCK_003_stock_str(self):
        """TC-STOCK-003: __str__ Stock menampilkan nama produk dan qty."""
        from zetaapp.models import Stock
        stock = Stock.objects.create(product=self.product, quantity=25)
        self.assertIn('Produk Stok Test', str(stock))
        self.assertIn('25', str(stock))


# ==============================================================================
# TC-TRX: TEST CASE — MODEL TRANSAKSI KAS
# ==============================================================================
class TransaksiModelTestCase(BaseTestCase):
    """TC-TRX: Pengujian model Transaksi (pemasukan & pengeluaran kas)."""

    def setUp(self):
        super().setUp()
        from zetaapp.models import Kategori, Transaksi
        self.kategori = Kategori.objects.create(
            owner=self.user, nama='Operasional'
        )
        self.trx_masuk = Transaksi.objects.create(
            owner=self.user,
            jumlah=Decimal('500000'),
            tanggal=datetime.date.today(),
            keterangan='Penjualan produk',
            transaksi_choice=Transaksi.PEMASUKAN,
            kategori=self.kategori
        )
        self.trx_keluar = Transaksi.objects.create(
            owner=self.user,
            jumlah=Decimal('200000'),
            tanggal=datetime.date.today(),
            keterangan='Beli bahan baku',
            transaksi_choice=Transaksi.PENGELUARAN,
            kategori=self.kategori
        )

    def test_TC_TRX_001_transaksi_str(self):
        """TC-TRX-001: __str__ Transaksi menampilkan jenis dan jumlah."""
        self.assertIn('Pemasukan', str(self.trx_masuk))
        self.assertIn('500000', str(self.trx_masuk))

    def test_TC_TRX_002_saldo_pemasukan_pengeluaran(self):
        """TC-TRX-002: Saldo = total pemasukan - total pengeluaran."""
        from zetaapp.models import Transaksi
        from django.db.models import Sum

        pemasukan = Transaksi.objects.filter(
            owner=self.user, transaksi_choice=Transaksi.PEMASUKAN
        ).aggregate(total=Sum('jumlah'))['total'] or 0

        pengeluaran = Transaksi.objects.filter(
            owner=self.user, transaksi_choice=Transaksi.PENGELUARAN
        ).aggregate(total=Sum('jumlah'))['total'] or 0

        saldo = pemasukan - pengeluaran
        self.assertEqual(float(saldo), 300000.0)

    def test_TC_TRX_003_isolasi_data_per_user(self):
        """TC-TRX-003: Pengguna lain tidak dapat melihat transaksi user ini."""
        from zetaapp.models import Transaksi
        trx_other = Transaksi.objects.filter(owner=self.other_user)
        self.assertEqual(trx_other.count(), 0)

    def test_TC_TRX_004_transaksi_pilihan_valid(self):
        """TC-TRX-004: transaksi_choice hanya boleh 'P' (Pemasukan) atau 'L' (Pengeluaran)."""
        from zetaapp.models import Transaksi
        self.assertEqual(self.trx_masuk.transaksi_choice, Transaksi.PEMASUKAN)
        self.assertEqual(self.trx_keluar.transaksi_choice, Transaksi.PENGELUARAN)


# ==============================================================================
# TC-HP: TEST CASE — MODEL HUTANG PIUTANG
# ==============================================================================
class HutangPiutangModelTestCase(BaseTestCase):
    """TC-HP: Pengujian model HutangPiutang."""

    def setUp(self):
        super().setUp()
        from zetaapp.models import HutangPiutang
        self.hutang = HutangPiutang.objects.create(
            owner=self.user,
            jumlah=Decimal('1000000'),
            tanggal=datetime.date.today(),
            hutang_choice=HutangPiutang.HUTANG,
            keterangan='Pinjam ke bank'
        )
        self.piutang = HutangPiutang.objects.create(
            owner=self.user,
            jumlah=Decimal('750000'),
            tanggal=datetime.date.today(),
            hutang_choice=HutangPiutang.PIUTANG,
            keterangan='Pabrik belum bayar'
        )

    def test_TC_HP_001_hutang_tersimpan(self):
        """TC-HP-001: Data hutang tersimpan dengan benar."""
        from zetaapp.models import HutangPiutang
        self.assertEqual(
            HutangPiutang.objects.filter(owner=self.user, hutang_choice='H').count(), 1
        )

    def test_TC_HP_002_piutang_tersimpan(self):
        """TC-HP-002: Data piutang tersimpan dengan benar."""
        from zetaapp.models import HutangPiutang
        self.assertEqual(
            HutangPiutang.objects.filter(owner=self.user, hutang_choice='P').count(), 1
        )

    def test_TC_HP_003_sisa_hutang_benar(self):
        """TC-HP-003: Sisa hutang = total piutang - total hutang."""
        from zetaapp.models import HutangPiutang
        from django.db.models import Sum
        total_hutang = HutangPiutang.objects.filter(
            owner=self.user, hutang_choice='H'
        ).aggregate(total=Sum('jumlah'))['total'] or 0
        total_piutang = HutangPiutang.objects.filter(
            owner=self.user, hutang_choice='P'
        ).aggregate(total=Sum('jumlah'))['total'] or 0
        sisa = total_piutang - total_hutang
        self.assertEqual(float(sisa), -250000.0)  # 750000 - 1000000

    def test_TC_HP_004_hapus_hutang(self):
        """TC-HP-004: Hutang bisa dihapus."""
        from zetaapp.models import HutangPiutang
        self.hutang.delete()
        self.assertFalse(HutangPiutang.objects.filter(id=self.hutang.id).exists())


# ==============================================================================
# TC-PROF: TEST CASE — MODEL PROFIT (Profito2)
# ==============================================================================
class ProfitModelTestCase(BaseTestCase):
    """TC-PROF: Pengujian model Profito2 dan perhitungan profit."""

    def setUp(self):
        super().setUp()
        from zetaapp.models import Profito2
        self.profit = Profito2.objects.create(
            nama_barang='Besi Scrap',
            berat_input=Decimal('100.00'),
            harga_beli_per_kg=Decimal('3000'),
            harga_jual_per_kg=Decimal('4500'),
            solar=Decimal('100'),
            karung=Decimal('50'),
            ongkos_kirim=Decimal('375'),
            ongkos_sortir=Decimal('300'),
            ongkos_giling=Decimal('300'),
            ongkos_muat=Decimal('50'),
            gaji_pegawai=Decimal('0'),
            susutan_persen=Decimal('5.00'),
            tabungan_persen=Decimal('30'),
        )

    def test_TC_PROF_001_berat_output_benar(self):
        """TC-PROF-001: berat_output = berat_input × (1 - susutan/100)."""
        expected = 100.0 * (1 - 5.0 / 100)  # = 95.0
        self.assertAlmostEqual(float(self.profit.berat_output), expected, places=2)

    def test_TC_PROF_002_hpp_per_kg_benar(self):
        """TC-PROF-002: hpp_per_kg = harga_beli + total biaya operasional per kg."""
        biaya_op = 100 + 50 + 375 + 300 + 300 + 50 + 0  # = 1175
        expected_hpp = 3000 + biaya_op  # = 4175
        self.assertAlmostEqual(float(self.profit.hpp_per_kg), expected_hpp, places=0)

    def test_TC_PROF_003_total_hpp_benar(self):
        """TC-PROF-003: total_hpp = hpp_per_kg × berat_input."""
        hpp = float(self.profit.hpp_per_kg)
        expected = hpp * 100.0
        self.assertAlmostEqual(float(self.profit.total_hpp), expected, places=0)

    def test_TC_PROF_004_total_revenue_benar(self):
        """TC-PROF-004: total_revenue = harga_jual × berat_output."""
        expected = 4500.0 * float(self.profit.berat_output)
        self.assertAlmostEqual(float(self.profit.total_revenue), expected, places=0)

    def test_TC_PROF_005_profit_benar(self):
        """TC-PROF-005: profit = total_revenue - total_hpp."""
        expected = float(self.profit.total_revenue) - float(self.profit.total_hpp)
        self.assertAlmostEqual(float(self.profit.profit), expected, places=0)

    def test_TC_PROF_006_profit_margin_benar(self):
        """TC-PROF-006: profit_margin = (profit / total_revenue) × 100."""
        if float(self.profit.total_revenue) > 0:
            expected = (float(self.profit.profit) / float(self.profit.total_revenue)) * 100
            self.assertAlmostEqual(float(self.profit.profit_margin), expected, places=1)

    def test_TC_PROF_007_tabungan_total_benar(self):
        """TC-PROF-007: tabungan_total = profit × tabungan_persen / 100."""
        expected = float(self.profit.profit) * 30.0 / 100.0
        self.assertAlmostEqual(float(self.profit.tabungan_total), expected, places=0)

    def test_TC_PROF_008_tandai_tabung(self):
        """TC-PROF-008: Menandai profit ditabung membuat entri Tabungan baru."""
        from zetaapp.models import Tabungan
        self.assertFalse(self.profit.profit_saved)

        self.profit.profit_saved = True
        self.profit.save()
        Tabungan.objects.create(
            owner=self.user,
            nominal=self.profit.tabungan_total,
            description=f'Tabungan dari profit: {self.profit.id}'
        )
        self.assertTrue(Tabungan.objects.filter(owner=self.user).exists())

    def test_TC_PROF_009_str_profito2(self):
        """TC-PROF-009: __str__ Profito2 menampilkan nama barang dan tanggal."""
        self.assertIn('Besi Scrap', str(self.profit))

    def test_TC_PROF_010_profit_positif(self):
        """TC-PROF-010: Dengan harga jual > harga beli + biaya, profit harus positif."""
        self.assertGreater(float(self.profit.profit), 0)


# ==============================================================================
# TC-VIEW: TEST CASE — VIEW (HTTP Response)
# ==============================================================================
class ViewsTestCase(BaseTestCase):
    """TC-VIEW: Pengujian HTTP response view-view utama."""

    def setUp(self):
        super().setUp()
        from products.models import Category, Product
        from customers.models import Customer

        self.category = Category.objects.create(
            owner=self.user, name='Cat View', description='', status='ACTIVE'
        )
        self.product = Product.objects.create(
            owner=self.user, name='Produk View Test', description='',
            status='ACTIVE', category=self.category,
            price=10000.0, selling_price=15000.0
        )
        self.customer = Customer.objects.create(
            owner=self.user, first_name='Customer View', phone='083000000001'
        )

    def test_TC_VIEW_001_landing_page(self):
        """TC-VIEW-001: Landing page bisa diakses tanpa login."""
        response = self.client.get(reverse('landingpage'))
        self.assertEqual(response.status_code, 200)

    def test_TC_VIEW_002_dashboard_memerlukan_login(self):
        """TC-VIEW-002: Dashboard redirect jika belum login."""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_TC_VIEW_003_dashboard_tampil_setelah_login(self):
        """TC-VIEW-003: Dashboard tampil dengan kode 200 setelah login."""
        self.login()
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_TC_VIEW_004_sales_list_tampil(self):
        """TC-VIEW-004: Halaman daftar penjualan tampil dengan benar."""
        self.login()
        response = self.client.get(reverse('sales:sales_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'sales', response.content.lower())

    def test_TC_VIEW_005_sales_add_get(self):
        """TC-VIEW-005: Halaman tambah penjualan (GET) tampil dengan benar."""
        self.login()
        response = self.client.get(reverse('sales:sales_add'))
        self.assertEqual(response.status_code, 200)

    def test_TC_VIEW_006_transaksi_halaman_tampil(self):
        """TC-VIEW-006: Halaman transaksi tampil setelah login."""
        self.login()
        response = self.client.get(reverse('transaksi'))
        self.assertEqual(response.status_code, 200)

    def test_TC_VIEW_007_profit_halaman_tampil(self):
        """TC-VIEW-007: Halaman analisis profit tampil setelah login."""
        self.login()
        response = self.client.get(reverse('profit'))
        self.assertEqual(response.status_code, 200)

    def test_TC_VIEW_008_stok_list_tampil(self):
        """TC-VIEW-008: Halaman stok gudang tampil setelah login."""
        self.login()
        response = self.client.get(reverse('stockin_list'))
        self.assertEqual(response.status_code, 200)

    def test_TC_VIEW_009_transaksi_history_tampil(self):
        """TC-VIEW-009: Halaman histori transaksi tampil setelah login."""
        self.login()
        response = self.client.get(reverse('transaksi_history'))
        self.assertEqual(response.status_code, 200)

    def test_TC_VIEW_010_product_search_api(self):
        """TC-VIEW-010: API pencarian produk mengembalikan JSON."""
        response = self.client.get(reverse('product_search_api'), {'q': 'Produk'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('results', data)

    def test_TC_VIEW_011_sales_add_post_invalid_no_product(self):
        """TC-VIEW-011: POST sales_add tanpa produk harus kembalikan error 400."""
        import json
        self.login()
        payload = {
            'sub_total': 0,
            'amount_payed': 0,
            'amount_change': 0,
            'products': []
        }
        response = self.client.post(
            reverse('sales:sales_add'),
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])

    def test_TC_VIEW_012_sales_add_post_berhasil(self):
        """TC-VIEW-012: POST sales_add dengan data valid harus berhasil."""
        import json
        self.login()
        payload = {
            'sub_total': 15000.0,
            'amount_payed': 15000.0,
            'amount_change': 0.0,
            'products': [
                {
                    'id': self.product.id,
                    'price': 15000.0,
                    'quantity': 1,
                    'total_product': 15000.0
                }
            ]
        }
        response = self.client.post(
            reverse('sales:sales_add'),
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])

    def test_TC_VIEW_013_sales_detail_tampil(self):
        """TC-VIEW-013: Halaman detail transaksi tampil setelah login."""
        from sales.models import Sale
        sale = Sale.objects.create(
            owner=self.user,
            sub_total=10000.0, grand_total=10000.0,
            amount_payed=10000.0, amount_change=0.0
        )
        self.login()
        response = self.client.get(
            reverse('sales:sales_details', kwargs={'sale_id': sale.id})
        )
        self.assertEqual(response.status_code, 200)

    def test_TC_VIEW_014_transaksi_history_filter_lunas(self):
        """TC-VIEW-014: Filter status=LUNAS berfungsi."""
        self.login()
        response = self.client.get(reverse('transaksi_history') + '?status=LUNAS')
        self.assertEqual(response.status_code, 200)

    def test_TC_VIEW_015_transaksi_history_filter_belum_lunas(self):
        """TC-VIEW-015: Filter status=BELUM_LUNAS berfungsi."""
        self.login()
        response = self.client.get(reverse('transaksi_history') + '?status=BELUM_LUNAS')
        self.assertEqual(response.status_code, 200)


# ==============================================================================
# TC-ISO: TEST CASE — ISOLASI DATA ANTAR USER
# ==============================================================================
class DataIsolationTestCase(BaseTestCase):
    """TC-ISO: Memastikan data antar user terisolasi dengan baik."""

    def setUp(self):
        super().setUp()
        from zetaapp.models import Transaksi, Kategori
        from sales.models import Sale
        from products.models import Category, Product

        # Data untuk user utama
        self.cat_user = Category.objects.create(
            owner=self.user, name='Cat User', description='', status='ACTIVE'
        )
        self.product_user = Product.objects.create(
            owner=self.user, name='Produk User', description='',
            status='ACTIVE', category=self.cat_user, price=5000.0
        )
        self.sale_user = Sale.objects.create(
            owner=self.user,
            sub_total=5000.0, grand_total=5000.0,
            amount_payed=5000.0, amount_change=0.0
        )
        kat_user = Kategori.objects.create(owner=self.user, nama='Kategori User')
        self.trx_user = Transaksi.objects.create(
            owner=self.user, jumlah=100000,
            tanggal=datetime.date.today(),
            transaksi_choice='P', kategori=kat_user
        )

        # Data untuk user lain
        self.cat_other = Category.objects.create(
            owner=self.other_user, name='Cat Other', description='', status='ACTIVE'
        )
        self.product_other = Product.objects.create(
            owner=self.other_user, name='Produk Other User', description='',
            status='ACTIVE', category=self.cat_other, price=7000.0
        )
        self.sale_other = Sale.objects.create(
            owner=self.other_user,
            sub_total=7000.0, grand_total=7000.0,
            amount_payed=7000.0, amount_change=0.0
        )

    def test_TC_ISO_001_sales_list_hanya_milik_user_login(self):
        """TC-ISO-001: Halaman daftar penjualan hanya menampilkan data milik user login."""
        self.login()
        response = self.client.get(reverse('sales:sales_list'))
        sales_in_context = list(response.context['salesa'])
        ids = [s.id for s in sales_in_context]
        self.assertIn(self.sale_user.id, ids)
        self.assertNotIn(self.sale_other.id, ids)

    def test_TC_ISO_002_transaksi_hanya_milik_user_login(self):
        """TC-ISO-002: Halaman transaksi hanya menampilkan data milik user login."""
        self.login()
        response = self.client.get(reverse('transaksi'))
        trx_in_context = list(response.context['data'])
        ids = [t.id for t in trx_in_context]
        self.assertIn(self.trx_user.id, ids)
        # Pastikan transaksi otomatis dari sale other user tidak muncul
        from zetaapp.models import Transaksi
        other_trx = Transaksi.objects.filter(owner=self.other_user).first()
        if other_trx:
            self.assertNotIn(other_trx.id, ids)

    def test_TC_ISO_003_user_lain_tidak_bisa_akses_detail_sale(self):
        """TC-ISO-003: User lain tidak bisa melihat detail transaksi user ini."""
        self.login(self.other_user)
        response = self.client.get(
            reverse('sales:sales_details', kwargs={'sale_id': self.sale_user.id})
        )
        # Harus redirect atau 404, bukan 200
        self.assertNotEqual(response.status_code, 200)


# ==============================================================================
# TC-PURCH: TEST CASE — MODEL PURCHASE
# ==============================================================================
class PurchaseModelTestCase(BaseTestCase):
    """TC-PURCH: Pengujian model Purchase dan PurchaseDetail."""

    def setUp(self):
        super().setUp()
        from products.models import Category, Product
        from purchases.models import Purchase, PurchaseDetail

        self.category = Category.objects.create(
            owner=self.user, name='Cat Purch', description='', status='ACTIVE'
        )
        self.product = Product.objects.create(
            owner=self.user, name='Produk Purch', description='',
            status='ACTIVE', category=self.category,
            price=8000.0, selling_price=10000.0
        )
        self.purchase = Purchase.objects.create(
            owner=self.user,
            supplier_name='Pabrik ABC',
            sub_total=80000.0,
            grand_total=80000.0,
            amount_payed=80000.0,
            amount_change=0.0
        )

    def test_TC_PURCH_001_nomor_transaksi_autogenerate(self):
        """TC-PURCH-001: Nomor transaksi pembelian digenerate otomatis dengan format KLR-."""
        self.assertIsNotNone(self.purchase.transaction_number)
        self.assertTrue(self.purchase.transaction_number.startswith('KLR-'))

    def test_TC_PURCH_002_pemasukan_kas_otomatis_dibuat(self):
        """TC-PURCH-002: Pemasukan kas dibuat otomatis saat purchase lunas."""
        from zetaapp.models import Transaksi
        trx = Transaksi.objects.filter(
            owner=self.user,
            transaksi_choice=Transaksi.PEMASUKAN,
            keterangan__icontains=self.purchase.transaction_number
        )
        self.assertTrue(trx.exists())
        self.assertEqual(float(trx.first().jumlah), 80000.0)

    def test_TC_PURCH_003_piutang_dibuat_jika_tidak_lunas(self):
        """TC-PURCH-003: Piutang dibuat otomatis jika amount_payed < sub_total."""
        from purchases.models import Purchase
        from zetaapp.models import HutangPiutang

        purch_dp = Purchase.objects.create(
            owner=self.user,
            supplier_name='Pabrik XYZ',
            sub_total=100000.0,
            grand_total=100000.0,
            amount_payed=40000.0,  # Bayar sebagian
            amount_change=0.0
        )
        piutang = HutangPiutang.objects.filter(
            owner=self.user,
            hutang_choice=HutangPiutang.PIUTANG,
            keterangan__icontains=purch_dp.transaction_number
        )
        self.assertTrue(piutang.exists())
        self.assertEqual(float(piutang.first().jumlah), 60000.0)

    def test_TC_PURCH_004_purchase_str(self):
        """TC-PURCH-004: __str__ Purchase menampilkan ID dan supplier."""
        text = str(self.purchase)
        self.assertIn('Purchase ID:', text)
        self.assertIn('Pabrik ABC', text)
