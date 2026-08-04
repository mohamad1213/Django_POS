from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

JENIS_BARANG_CHOICES = [
    ('ps kaca', 'PS Kaca'),
    ('ps warna', 'PS Warna'),
    ('cd', 'CD'),
    ('akralik', 'Akralik'),
    ('pc', 'PC'),
    ('as item', 'AS'),
    ('dop', 'Dop'),
    ('krasan', 'Krasan'),
]

STATUS_CHOICES = [
    ('PENDING', 'Menunggu Pelunasan'),
    ('LUNAS', 'Sudah Lunas'),
]

class Afkiran(models.Model):
    sale = models.OneToOneField(
        'sales.Sale',
        on_delete=models.CASCADE,
        related_name='afkiran',
        verbose_name='Nota Barang Masuk'
    )
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='User'
    )
    dp_amount = models.FloatField(default=0, verbose_name='DP (Uang Muka)')
    total_nota = models.FloatField(default=0, verbose_name='Total Nota PS Kaca')
    total_sortir = models.FloatField(default=0, verbose_name='Total Nilai Sortir')
    selisih = models.FloatField(default=0, verbose_name='Selisih (Nota - Sortir)')
    sisa_bayar = models.FloatField(default=0, verbose_name='Sisa Bayar (Selisih - DP)')
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name='Status'
    )
    date_created = models.DateTimeField(default=timezone.now)
    catatan = models.TextField(blank=True, default='', verbose_name='Catatan')

    class Meta:
        db_table = 'Afkiran'
        verbose_name = 'Afkiran'
        verbose_name_plural = 'Daftar Afkiran'
        ordering = ['-date_created']

    def __str__(self):
        return f"Afkiran #{self.pk} — Nota {self.sale.transaction_number}"

    def recalculate(self):
        total = sum(d.total for d in self.afkirandetail_set.all())
        self.total_sortir = total
        self.selisih = self.total_nota - total
        self.sisa_bayar = self.selisih - self.dp_amount
        self.save(update_fields=['total_sortir', 'selisih', 'sisa_bayar'])


class AfkiranDetail(models.Model):
    afkiran = models.ForeignKey(
        Afkiran, on_delete=models.CASCADE, verbose_name='Afkiran'
    )
    nama_barang = models.CharField(
        max_length=50,
        choices=JENIS_BARANG_CHOICES,
        verbose_name='Jenis Barang'
    )
    quantity = models.FloatField(default=0, verbose_name='Jumlah (kg)')
    harga = models.FloatField(default=0, verbose_name='Harga/kg')
    total = models.FloatField(default=0, verbose_name='Total')

    class Meta:
        db_table = 'AfkiranDetail'

    def save(self, *args, **kwargs):
        self.total = self.quantity * self.harga
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_nama_barang_display()} — {self.quantity} kg"
