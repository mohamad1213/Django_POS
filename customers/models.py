from django.db import models
from django.contrib.auth.models import User

class Customer(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=256)
    address = models.TextField(max_length=256, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        db_table = 'Customers'

    def __str__(self) -> str:
        return self.first_name 

    def to_select2(self):
        item = {
            "text": self.first_name,
            "id": self.id
        }
        return item
