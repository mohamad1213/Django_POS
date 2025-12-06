from django.db import models


class Customer(models.Model):
    first_name = models.CharField(max_length=256)
    address = models.TextField(max_length=256, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        db_table = 'Customers'

    def __str__(self) -> str:
        return self.first_name 

    def to_select2(self):
        item = {
            "label": self.first_name,
            "value": self.id
        }
        return item
