from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from datetime import date
from zetaapp.models import BiayaBulanan
from purchases.models import Purchase
from products.models import Product, Category


class BiayaBulananTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='owner1', password='password123')
        self.user2 = User.objects.create_user(username='owner2', password='password123')
        
        self.client1 = Client()
        self.client1.login(username='owner1', password='password123')

        self.client2 = Client()
        self.client2.login(username='owner2', password='password123')

        # Buat data biaya untuk user1 di Bulan 9 Tahun 2026
        self.biaya1 = BiayaBulanan.objects.create(
            owner=self.user1,
            tanggal=date(2026, 9, 5),
            kategori='Listrik & Air',
            nama_biaya='Token Listrik Gudang',
            nominal=Decimal('350000.00'),
            keterangan='Listrik operasional awal bulan'
        )
        self.biaya2 = BiayaBulanan.objects.create(
            owner=self.user1,
            tanggal=date(2026, 9, 15),
            kategori='Gaji Pegawai',
            nama_biaya='Gaji Operator Sortir',
            nominal=Decimal('1500000.00'),
            keterangan='Gaji 1 orang'
        )

        # Buat data biaya untuk user1 di Bulan 8 Tahun 2026 (bulan berbeda)
        self.biaya_agustus = BiayaBulanan.objects.create(
            owner=self.user1,
            tanggal=date(2026, 8, 20),
            kategori='Sewa Tempat',
            nama_biaya='Sewa Lahan',
            nominal=Decimal('2000000.00')
        )

        # Buat data biaya untuk user2 (user berbeda)
        self.biaya_user2 = BiayaBulanan.objects.create(
            owner=self.user2,
            tanggal=date(2026, 9, 10),
            kategori='Operasional',
            nama_biaya='Biaya Bensin User 2',
            nominal=Decimal('100000.00')
        )

    def test_model_fields_and_decimal(self):
        """Memastikan field model dan tipe DecimalField berfungsi sesuai spesifikasi."""
        self.assertEqual(self.biaya1.nominal, Decimal('350000.00'))
        self.assertIsInstance(self.biaya1.nominal, Decimal)
        self.assertEqual(self.biaya1.kategori, 'Listrik & Air')
        self.assertEqual(self.biaya1.nama_biaya, 'Token Listrik Gudang')
        self.assertEqual(self.biaya1.tanggal, date(2026, 9, 5))

    def test_user_isolation(self):
        """Memastikan data biaya hanya bisa diakses oleh request.user pemiliknya."""
        response1 = self.client1.get(reverse('biaya_bulanan_list') + '?bulan=9&tahun=2026')
        self.assertEqual(response1.status_code, 200)
        
        # User 1 hanya melihat biayanya sendiri
        biaya_names_user1 = [b.nama_biaya for b in response1.context['biaya_list']]
        self.assertIn('Token Listrik Gudang', biaya_names_user1)
        self.assertIn('Gaji Operator Sortir', biaya_names_user1)
        self.assertNotIn('Biaya Bensin User 2', biaya_names_user1)

        # User 2 hanya melihat biayanya sendiri
        response2 = self.client2.get(reverse('biaya_bulanan_list') + '?bulan=9&tahun=2026')
        biaya_names_user2 = [b.nama_biaya for b in response2.context['biaya_list']]
        self.assertIn('Biaya Bensin User 2', biaya_names_user2)
        self.assertNotIn('Token Listrik Gudang', biaya_names_user2)

    def test_monthly_filter_and_total_biaya(self):
        """Memastikan filter bulan dan tahun menghitung total biaya secara tepat."""
        # Filter September 2026
        response_sep = self.client1.get(reverse('biaya_bulanan_list') + '?bulan=9&tahun=2026')
        self.assertEqual(response_sep.status_code, 200)
        
        # Total Biaya September = 350.000 + 1.500.000 = 1.850.000 (tidak termasuk Agustus)
        total_biaya_sep = response_sep.context['total_biaya']
        self.assertEqual(Decimal(str(total_biaya_sep)), Decimal('1850000.00'))
        self.assertEqual(len(response_sep.context['biaya_list']), 2)

        # Filter Agustus 2026
        response_aug = self.client1.get(reverse('biaya_bulanan_list') + '?bulan=8&tahun=2026')
        total_biaya_aug = response_aug.context['total_biaya']
        self.assertEqual(Decimal(str(total_biaya_aug)), Decimal('2000000.00'))
        self.assertEqual(len(response_aug.context['biaya_list']), 1)

    def test_create_biaya(self):
        """Memastikan fitur Tambah Biaya berhasil dan terasosiasi ke request.user."""
        data = {
            'tanggal': '2026-09-25',
            'kategori': 'Transportasi & BBM',
            'nama_biaya': 'Solar Truk Angkut',
            'nominal': '250000',
            'keterangan': 'Pengisian solar 25L'
        }
        response = self.client1.post(reverse('biaya_bulanan_create'), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        created = BiayaBulanan.objects.filter(nama_biaya='Solar Truk Angkut', owner=self.user1).first()
        self.assertIsNotNone(created)
        self.assertEqual(created.nominal, Decimal('250000.00'))
        self.assertEqual(created.owner, self.user1)

    def test_update_biaya(self):
        """Memastikan fitur Edit Biaya berhasil dan user lain tidak bisa mengedit."""
        # User 1 mengedit biayanya
        update_data = {
            'tanggal': '2026-09-05',
            'kategori': 'Listrik & Air',
            'nama_biaya': 'Token Listrik Gudang (Revisi)',
            'nominal': '400000',
            'keterangan': 'Revisi nominal'
        }
        response = self.client1.post(reverse('biaya_bulanan_update', args=[self.biaya1.id]), data=update_data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        self.biaya1.refresh_from_db()
        self.assertEqual(self.biaya1.nominal, Decimal('400000.00'))
        self.assertEqual(self.biaya1.nama_biaya, 'Token Listrik Gudang (Revisi)')

        # User 2 mencoba mengedit biaya milik User 1 -> harus 404
        response_unauth = self.client2.post(reverse('biaya_bulanan_update', args=[self.biaya1.id]), data=update_data)
        self.assertEqual(response_unauth.status_code, 404)

    def test_delete_biaya(self):
        """Memastikan fitur Hapus Biaya berhasil dan user lain tidak bisa menghapus."""
        # User 2 mencoba hapus biaya milik User 1 -> harus 404
        response_unauth = self.client2.post(reverse('biaya_bulanan_delete', args=[self.biaya1.id]))
        self.assertEqual(response_unauth.status_code, 404)
        self.assertTrue(BiayaBulanan.objects.filter(id=self.biaya1.id).exists())

        # User 1 menghapus biayanya sendiri
        response = self.client1.post(reverse('biaya_bulanan_delete', args=[self.biaya1.id]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(BiayaBulanan.objects.filter(id=self.biaya1.id).exists())

    def test_profit_bersih_calculation(self):
        """
        Memastikan integrasi perhitungan:
        Profit Bersih = Profit Kotor - Total Biaya Bulanan
        pada bulan yang sama.
        """
        # Buat transaksi penjualan/keluar pada September 2026 dengan Profit Kotor Rp 5.000.000
        cat = Category.objects.create(name='Pralon', owner=self.user1)
        prod = Product.objects.create(name='Pralon Bening', price=10000, selling_price=15000, owner=self.user1, category=cat)

        from django.utils import timezone
        import datetime

        Purchase.objects.create(
            owner=self.user1,
            supplier_name='Pabrik Daur Ulang',
            sub_total=15000000,
            grand_total=15000000,
            amount_payed=15000000,
            profit_kotor=5000000.0,
            net_profit=5000000.0,
            date_added=timezone.make_aware(datetime.datetime(2026, 9, 12, 10, 0, 0))
        )

        response = self.client1.get(reverse('biaya_bulanan_list') + '?bulan=9&tahun=2026')
        self.assertEqual(response.status_code, 200)

        profit_kotor = response.context['profit_kotor']
        total_biaya = response.context['total_biaya']
        profit_bersih = response.context['profit_bersih']

        # Total Biaya Sept = 350.000 + 1.500.000 = 1.850.000
        # Profit Kotor Sept = 5.000.000
        # Profit Bersih Sept = 5.000.000 - 1.850.000 = 3.150.000
        self.assertEqual(float(profit_kotor), 5000000.0)
        self.assertEqual(float(total_biaya), 1850000.0)
        self.assertEqual(float(profit_bersih), 3150000.0)
