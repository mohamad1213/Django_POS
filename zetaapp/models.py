from django.db import models
from django.contrib.auth.models import User


# Create your models here.

class Task(models.Model):
    title = models.CharField(max_length=200)
    complete = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    

from django.db import models

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
    tanggal = models.DateTimeField()
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
    tanggal = models.DateTimeField()
    keterangan = models.TextField(blank=True, null=True)
    transaksi_choice= models.CharField(max_length=1, choices=JENIS_CHOICES)
    kategori = models.ForeignKey(Kategori, on_delete=models.CASCADE)
    def calculate_profit_loss(self):
        # Assuming the buy and sell transactions are related by date
        buy_transaction = Transaksi.objects.filter(
            transaksi_choice='L',
            tanggal__lte=self.tanggal
        ).order_by('-tanggal').first()

        if self.transaksi_choice == 'P' and buy_transaction:
            # Calculate profit or loss
            profit_loss = self.jumlah - buy_transaction.jumlah
            return profit_loss
        else:
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
