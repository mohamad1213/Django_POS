from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


# Create your models here.

class Task(models.Model):
    title = models.CharField(max_length=200)
    complete = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    

from django.db import models
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
    # Info barang / transaksi
    tanggal = models.DateField(auto_now_add=True)
    nama_barang = models.CharField(max_length=100)
    
    # Harga beli & jual
    harga_beli = models.DecimalField(max_digits=15, decimal_places=0, validators=[MinValueValidator(0)])
    harga_jual = models.DecimalField(max_digits=15, decimal_places=0, validators=[MinValueValidator(0)])
    
    # Biaya operasional
    solar = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    karung = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    ongkos_kirim = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    ongkos_muat = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    ongkos_lain = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    ongkos_sortir = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    ongkos_giling = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    biaya_darurat_mesin = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    
    # Hasil perhitungan otomatis
    hpp = models.DecimalField(max_digits=15, decimal_places=0, blank=True, null=True)
    profit = models.DecimalField(max_digits=15, decimal_places=0, blank=True, null=True)
    profit_margin = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    
    keterangan = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-tanggal']

    def save(self, *args, **kwargs):
        # Hitung total biaya operasional
        total_biaya_operasional = (
            self.solar + self.karung + self.ongkos_kirim + self.ongkos_muat +
            self.ongkos_lain + self.ongkos_sortir + self.ongkos_giling + self.biaya_darurat_mesin
        )
        
        # Hitung HPP
        self.hpp = self.harga_beli + total_biaya_operasional
        
        # Hitung profit
        self.profit = self.harga_jual - self.hpp
        
        # Hitung profit margin
        self.profit_margin = (self.profit / self.harga_jual * 100) if self.harga_jual else 0
        
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
