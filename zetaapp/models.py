from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import F
from django.utils import timezone
from django.conf import settings


# Create your models here.

class Task(models.Model):
    title = models.CharField(max_length=200)
    complete = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    


class Product(models.Model):
    sku = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.name}"


class Stock(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="stock")
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.name}: {self.quantity}"


class StockIn(models.Model):
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="stock_in_history")
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    reference = models.CharField(max_length=200, blank=True)  # No. nota/invoice (opsional)
    note = models.TextField(blank=True)
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    received_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"IN {self.product.name} x {self.quantity}"

    def save(self, *args, **kwargs):
        # ketika barang masuk, update stok otomatis
        with transaction.atomic():
            stock_obj, created = Stock.objects.select_for_update().get_or_create(
                product=self.product,
                defaults={"quantity": 0}
            )
            stock_obj.quantity = F("quantity") + self.quantity
            stock_obj.save()
            stock_obj.refresh_from_db()

            super().save(*args, **kwargs)

class ExcelUpload(models.Model):
    excel_files = models.FileField()
class Kategori(models.Model):
    nama = models.CharField(max_length=255)

    def __str__(self):
        return self.nama


class Karyawan(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class HutPegawai(models.Model):
    HUTANG = 'H'
    PIUTANG = 'P'

    JENIS_CHOICES = [
        (HUTANG, 'Hutang'),
        (PIUTANG, 'Piutang'),
    ]
    pegawai = models.ForeignKey('Karyawan', on_delete=models.CASCADE)
    jumlah = models.DecimalField(max_digits=20, decimal_places=2)
    tanggal = models.DateField()
    hutang_choice= models.CharField(max_length=1, choices=JENIS_CHOICES)

    keterangan = models.TextField(blank=True, null=True)
    
class Transaksi(models.Model):
    PEMASUKAN = 'P'
    PENGELUARAN = 'L'

    JENIS_CHOICES = [
        (PEMASUKAN, 'Pemasukan'),
        (PENGELUARAN, 'Pengeluaran'),
    ]
    owner = models.ForeignKey(User,null=True, on_delete = models.DO_NOTHING,related_name='transaksi')
    jumlah = models.DecimalField(max_digits=20, decimal_places=2)
    tanggal = models.DateField()
    keterangan = models.TextField(blank=True, null=True)
    transaksi_choice= models.CharField(max_length=1, choices=JENIS_CHOICES, blank=True, null=True)
    kategori = models.ForeignKey(Kategori, on_delete=models.CASCADE, blank=True, null=True)
    def calculate_profit_loss(self):
        buy_transaction = Transaksi.objects.filter(
            transaksi_choice='L',
            tanggal__lte=self.tanggal
        ).order_by('-tanggal').first()

        if self.transaksi_choice == 'P' and buy_transaction:
            profit_loss = self.jumlah - buy_transaction.jumlah
            return profit_loss
        return 0

    def __str__(self):
        return f"{self.get_transaksi_choice_display()} - {self.jumlah} on {self.tanggal}"


class HutangPiutang(models.Model):
    HUTANG = 'H'
    PIUTANG = 'P'

    JENIS_CHOICES = [
        (HUTANG, 'Hutang'),
        (PIUTANG, 'Piutang'),
    ]
    owner = models.ForeignKey(User,null=True, on_delete = models.DO_NOTHING,related_name='hutang')
    jumlah = models.DecimalField(max_digits=20, decimal_places=2)
    tanggal = models.DateField()
    hutang_choice= models.CharField(max_length=1, choices=JENIS_CHOICES)
    keterangan = models.TextField(blank=True, null=True)
    def __str__(self):
            return f"{self.get_name_display()} ({self.hutang_choice})"

class Profito(models.Model):
    nama_suplayer = models.TextField()
    description = models.TextField()
    date = models.DateField()
    jumlah_brg = models.DecimalField(max_digits=20, decimal_places=2)
    harga_jual = models.DecimalField(max_digits=20, decimal_places=2)
    harga_beli = models.DecimalField(max_digits=20, decimal_places=2)
    def calculate_profit(self):
        return (self.harga_jual - self.harga_beli) * self.jumlah_brg

    def __str__(self):
        return f"Jumlah: {self.jumlah_brg}, Harga Jual: {self.harga_jual}, Harga Beli: {self.harga_beli}"

class Profito2(models.Model):

    tanggal = models.DateField(auto_now_add=True)
    nama_barang = models.CharField(max_length=100)

    # Input dari user
    berat_input = models.DecimalField(max_digits=10, decimal_places=2)  # kg masuk
    harga_beli_per_kg = models.DecimalField(max_digits=15, decimal_places=0)
    harga_jual_per_kg = models.DecimalField(max_digits=15, decimal_places=0)

    # Biaya per kg (tetap)
    solar = models.DecimalField(max_digits=15, decimal_places=0, default=100)
    karung = models.DecimalField(max_digits=15, decimal_places=0, default=50)
    ongkos_kirim = models.DecimalField(max_digits=15, decimal_places=0, default=375)
    ongkos_sortir = models.DecimalField(max_digits=15, decimal_places=0, default=300)
    ongkos_giling = models.DecimalField(max_digits=15, decimal_places=0, default=300)
    ongkos_muat = models.DecimalField(max_digits=15, decimal_places=0, default=50)
    susutan_persen = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)  # susut 5%

    # Hasil otomatis
    berat_output = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    hpp_per_kg = models.DecimalField(max_digits=15, decimal_places=0, blank=True, null=True)
    total_hpp = models.DecimalField(max_digits=15, decimal_places=0, blank=True, null=True)
    total_revenue = models.DecimalField(max_digits=15, decimal_places=0, blank=True, null=True)
    profit = models.DecimalField(max_digits=15, decimal_places=0, blank=True, null=True)
    profit_margin = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    tabungan_persen = models.DecimalField(max_digits=5, decimal_places=2, default=30)  # default 30%
    tabungan_total = models.DecimalField(max_digits=15, decimal_places=0, blank=True, null=True)
    
    keterangan = models.TextField(blank=True, null=True)
    class Meta:
        ordering = ['-tanggal']

    def save(self, *args, **kwargs):

        # 1. Hitung berat output setelah susut
        self.berat_output = float(self.berat_input) * (1 - float(self.susutan_persen) / 100)

        # 2. Total biaya operasional per kg
        biaya_operasional_per_kg = (
            float(self.solar) +
            float(self.karung) +
            float(self.ongkos_kirim) +
            float(self.ongkos_sortir) +
            float(self.ongkos_giling) +
            float(self.ongkos_muat)
        )

        # 3. HPP per kg
        self.hpp_per_kg = float(self.harga_beli_per_kg) + biaya_operasional_per_kg

        # 4. Total HPP (menggunakan berat input)
        self.total_hpp = self.hpp_per_kg * float(self.berat_input)

        # 5. Total pendapatan (pakai berat output)
        self.total_revenue = float(self.harga_jual_per_kg) * float(self.berat_output)

        # 6. Profit
        self.profit = self.total_revenue - self.total_hpp

        # 7. Profit margin %
        self.profit_margin = (self.profit / self.total_revenue * 100) if self.total_revenue > 0 else 0
        
         # Hitung tabungan otomatis
        self.tabungan_total = self.profit * float(self.tabungan_persen)/100

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nama_barang} - {self.tanggal}"

class Tabungan(models.Model):
    PEMASUKAN = 'P'
    PENGELUARAN = 'L'

    JENIS_CHOICES = [
        (PEMASUKAN, 'Pemasukan'),
        (PENGELUARAN, 'Pengeluaran'),
    ]
    transaksi_choice= models.CharField(max_length=1, choices=JENIS_CHOICES)
    nominal = models.DecimalField(max_digits=20, decimal_places=2)
    description = models.TextField()
    date = models.DateField()

class Pegawai(models.Model):
    nama = models.CharField(max_length=100)
    nip = models.CharField(max_length=20, unique=True)
    jabatan = models.CharField(max_length=50)
    gaji = models.DecimalField(max_digits=10, decimal_places=2)
    tanggal_masuk = models.DateField()

    def __str__(self):
        return self.nama
