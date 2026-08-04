from django.db import models
from django.utils import timezone
from products.models import Product
from zetaapp.models import Transaksi, Stock
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import F
import random
import string


class Purchase(models.Model):
    date_added = models.DateTimeField(default=timezone.now)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    supplier_name = models.CharField(max_length=255, blank=True, null=True, default="Umum")
    transaction_number = models.CharField(max_length=50, unique=True)
    sub_total = models.FloatField(default=0)
    grand_total = models.FloatField(default=0)
    note = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'Purchases'

    def __str__(self) -> str:
        return f"Purchase ID: {self.id} | Supplier: {self.supplier_name} | Sub Total: {self.sub_total} | Datetime: {self.date_added}"

    @property
    def wa_link(self):
        import re
        text = f"{self.supplier_name or ''} {self.note or ''}"
        p = ''.join(re.findall(r'\d+', text))
        if len(p) >= 9:
            if p.startswith('0'):
                p = '62' + p[1:]
            elif not p.startswith('62'):
                p = '62' + p
            return f"https://api.whatsapp.com/send?phone={p}"
        return None

    def sum_items(self):
        details = PurchaseDetail.objects.filter(purchase=self.id)
        return sum([d.quantity for d in details])

    def generate_invoice_number(self):
        date_str = timezone.now().strftime('%Y%m%d')
        # Buat loop untuk menjamin transaction_number selalu unik
        while True:
            random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            new_code = f'KLR-{date_str}-{random_chars}'
            if not Purchase.objects.filter(transaction_number=new_code).exists():
                return new_code
    def save(self, *args, **kwargs):
        if not self.transaction_number:
            self.transaction_number = self.generate_invoice_number()
            
        creating = self.pk is None
        super().save(*args, **kwargs)

        if creating:
            try:
                owner_user = self.owner
                if isinstance(owner_user, int):
                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    owner_user = User.objects.filter(pk=owner_user).first()

                if owner_user:
                    Transaksi.objects.create(
                        owner=owner_user,
                        jumlah=self.sub_total,
                        tanggal=self.date_added.date() if hasattr(self, 'date_added') and self.date_added else timezone.now().date(),
                        keterangan=f"Barang Keluar (Jual) {self.transaction_number} (Tujuan: {self.supplier_name or 'Pabrik'})",
                        transaksi_choice=Transaksi.PEMASUKAN,
                    )
            except Exception as e:
                print(f"Error saat membuat Kas Transaksi: {e}")


class PurchaseDetail(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, db_column='purchase')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, db_column='product')
    cost_price = models.FloatField()
    quantity = models.FloatField(default=0)
    total_detail = models.FloatField()

    class Meta:
        db_table = 'PurchaseDetails'

    def __str__(self) -> str:
        return f"Detail ID: {self.id} Purchase ID: {self.purchase.id} Quantity: {self.quantity}"
