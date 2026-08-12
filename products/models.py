from django.db import models
from django.forms import model_to_dict

from django.contrib.auth.models import User
class Category(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    
    STATUS_CHOICES = (  # new
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive")
    )
    name = models.CharField(max_length=256,)
    description = models.TextField(max_length=256)
    status = models.CharField(
        choices=STATUS_CHOICES,
        max_length=100,
        verbose_name="Status of the category",
    )

    class Meta:
        # Table's name
        db_table = "Category"
        verbose_name_plural = "Categories"

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    
    STATUS_CHOICES = (  # new
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive")
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        null=True,
        blank=True
    )
    name = models.CharField(max_length=256, unique=True)
    description = models.TextField(max_length=256)
    status = models.CharField(
        choices=STATUS_CHOICES,
        max_length=100,
        verbose_name="Status of the product",
    )
    category = models.ForeignKey(
        Category, related_name="category", on_delete=models.CASCADE, db_column='category')

    price = models.FloatField(default=0)
    selling_price = models.FloatField(default=0, verbose_name="Harga Jual")

    class Meta:
        # Table's name
        db_table = "Product"

    def save(self, *args, **kwargs):
        if not self.code:
            last = Product.objects.filter(code__isnull=False).order_by("-id").first()

            if last and last.code:
                try:
                    number = int(last.code.replace("BRG", "")) + 1
                except ValueError:
                    number = Product.objects.count() + 1
            else:
                number = 1

            self.code = f"BRG{number:06d}"

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"

    def to_json(self):
        item = model_to_dict(self)
        item['id'] = self.id
        item['text'] = self.name
        item['category'] = self.category.name
        item['price'] = self.price
        item['selling_price'] = self.selling_price
        item['quantity'] = 1
        item['total_product'] = 0
        return item
