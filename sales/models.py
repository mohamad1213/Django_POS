from django.db import models
import django.utils.timezone
from customers.models import Customer
from products.models import Product
from datetime import date
import random
import string
from django.db import models
from django.utils import timezone
from zetaapp.models import Transaksi

class CustomerCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)
class Sale(models.Model):
    date_added = models.DateTimeField(default=django.utils.timezone.now)
    
    customer = models.ForeignKey(
        Customer, models.DO_NOTHING, db_column='customer')
    transaction_number = models.CharField(max_length=20, unique=True)
    sub_total = models.FloatField(default=0)
    grand_total = models.FloatField(default=0)
    amount_payed = models.FloatField(default=0)
    amount_change = models.FloatField(default=0)

    class Meta:
        db_table = 'Sales'

    def __str__(self) -> str:
        return "Sale ID: " + str(self.id) + " | Sub Total: " + str(self.sub_total) + " | Datetime: " + str(self.date_added)

    def sum_items(self):
        details = SaleDetail.objects.filter(sale=self.id)
        return sum([d.quantity for d in details])
    def save(self, *args, **kwargs):
        if not self.transaction_number:
            self.transaction_number = self.generate_invoice_number()
        creating = self.pk is None  # Cek apakah ini sale baru
        super().save(*args, **kwargs)  # Simpan sale dulu

        if creating:
            # Buat transaksi pengeluaran otomatis
            Transaksi.objects.create(
                owner=None,  # Bisa diisi user yang membuat sale
                jumlah=self.sub_total,  # Jumlah pengeluaran = total penjualan
                tanggal=self.date_added.date(),
                keterangan=f"Pengeluaran dari penjualan {self.transaction_number}",
                transaksi_choice=Transaksi.PENGELUARAN,
                kategori=None  # Sesuaikan dengan kategori pengeluaran
            )

    def generate_invoice_number(self):
        date_str = self.date_added.strftime('%Y%m%d')
        random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f'PPJ-{date_str}-{random_chars}'
    
    
class SaleDetail(models.Model):
    sale = models.ForeignKey(
        Sale, models.DO_NOTHING, db_column='sale')
    product = models.ForeignKey(
        Product, models.DO_NOTHING, db_column='product')
    price = models.FloatField()
    quantity = models.IntegerField()
    total_detail = models.FloatField()

    class Meta:
        db_table = 'SaleDetails'

    def __str__(self) -> str:
        return "Detail ID: " + str(self.id) + " Sale ID: " + str(self.sale.id) + " Quantity: " + str(self.quantity)
