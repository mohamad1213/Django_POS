from django.db import models
import django.utils.timezone
from customers.models import Customer
from products.models import Product
from datetime import date
import random
import string
from django.db import models
from django.utils import timezone
from zetaapp.models import Transaksi, HutangPiutang
from django.contrib.auth.models import User

class Sale(models.Model):
    date_added = models.DateTimeField(default=django.utils.timezone.now)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    customer = models.ForeignKey(
        Customer,on_delete=models.SET_NULL, null=True, blank=True, db_column='customer')
    transaction_number = models.CharField(max_length=20, unique=True)
    sub_total = models.FloatField(default=0)
    grand_total = models.FloatField(default=0)
    amount_payed = models.FloatField(default=0)
    amount_change = models.FloatField(default=0)
    dp_amount = models.FloatField(default=0)
    is_afkiran = models.BooleanField(default=False)

    class Meta:
        db_table = 'Sales'

    def __str__(self) -> str:
        return "Sale ID: " + str(self.id) + " | Sub Total: " + str(self.sub_total) + " | Datetime: " + str(self.date_added)

    def sum_items(self):
        details = SaleDetail.objects.filter(sale=self.id)
        return sum([d.quantity for d in details])

    @property
    def is_lunas(self):
        return (self.amount_payed or 0) >= (self.sub_total or 0)

    def has_afkiran_items(self):
        for detail in self.saledetail_set.select_related('product').all():
            if detail.product and detail.product.name:
                name = detail.product.name.lower()
                if 'ps kaca' in name or 'ps warna' in name:
                    return True
        return False

    @property
    def wa_link(self):
        if not self.customer or not self.customer.phone:
            return None
        import re, urllib.parse
        p = ''.join(re.findall(r'\d+', str(self.customer.phone)))
        if not p:
            return None
        if p.startswith('0'):
            p = '62' + p[1:]
        elif not p.startswith('62'):
            p = '62' + p

        cust_name = self.customer.first_name or "Pelanggan"
        paid_val = self.amount_payed or self.sub_total
        subtotal_val = float(self.sub_total or 0)
        paid_float = float(paid_val or 0)

        msg = (
            f"Halo {cust_name},\n\n"
            f"Berikut rincian Nota Transaksi Barang Masuk #{self.transaction_number}:\n"
            f"• Tanggal: {self.date_added.strftime('%d-%m-%Y')}\n"
            f"• Subtotal Barang: Rp {int(subtotal_val):,}\n"
            f"• Dibayar (Kas): Rp {int(paid_float):,}\n"
        )
        sisa = subtotal_val - paid_float
        if sisa > 0:
            msg += f"• Sisa (Hutang): Rp {int(sisa):,}\n"
        else:
            msg += f"• Status: LUNAS\n"

        msg += "\nTerima kasih! — POS PPJ Pralon"
        encoded_msg = urllib.parse.quote(msg)
        return f"https://api.whatsapp.com/send?phone={p}&text={encoded_msg}"

    def save(self, *args, **kwargs):
        if not self.transaction_number:
            self.transaction_number = self.generate_invoice_number()
        creating = self.pk is None  # Cek apakah ini sale baru
        super().save(*args, **kwargs)  # Simpan sale dulu

        if creating:
            try:
                # 1. Catat Pengeluaran Kas HANYA sebesar nominal yang benar-benar DIBAYAR (amount_payed)
                actual_paid = float(self.amount_payed or 0)
                if actual_paid > 0:
                    Transaksi.objects.create(
                        owner=self.owner,
                        jumlah=actual_paid,
                        tanggal=self.date_added.date(),
                        keterangan=f"Barang Masuk (Beli) {self.transaction_number}",
                        transaksi_choice=Transaksi.PENGELUARAN,
                        kategori=None,
                    )

                # 2. Jika Bayar < Subtotal, selisih menjadi HUTANG (POS belum melunasi ke Seller/Supplier)
                unpaid_balance = float(self.sub_total or 0) - actual_paid
                if unpaid_balance > 0:
                    cust_name = self.customer.first_name if self.customer else "Umum"
                    HutangPiutang.objects.create(
                        owner=self.owner,
                        jumlah=unpaid_balance,
                        tanggal=self.date_added.date(),
                        hutang_choice=HutangPiutang.HUTANG,
                        keterangan=f"Hutang Pembelian Barang Masuk {self.transaction_number} ({cust_name})",
                    )
            except Exception as e:
                print(f"Error saat membuat Kas Transaksi / Hutang: {e}")

    def generate_invoice_number(self):
        date_str = self.date_added.strftime('%Y%m%d')
        random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f'PPJ-{date_str}-{random_chars}'
    
    
class SaleDetail(models.Model):
    sale = models.ForeignKey(
        Sale, on_delete=models.CASCADE, db_column='sale')
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, db_column='product')
    price = models.FloatField()
    quantity = models.FloatField(default=0)
    total_detail = models.FloatField()

    class Meta:
        db_table = 'SaleDetails'

    def __str__(self) -> str:
        return "Detail ID: " + str(self.id) + " Sale ID: " + str(self.sale.id) + " Quantity: " + str(self.quantity)
