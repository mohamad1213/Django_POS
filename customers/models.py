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

    @property
    def wa_link(self):
        if not self.phone:
            return None
        import re
        p = ''.join(re.findall(r'\d+', str(self.phone)))
        if not p:
            return None
        if p.startswith('0'):
            p = '62' + p[1:]
        elif not p.startswith('62'):
            p = '62' + p
        return f"https://api.whatsapp.com/send?phone={p}"

    def to_select2(self):
        label = self.first_name
        if self.phone:
            label += f" | {self.phone}"
        if self.address:
             label += f" | {self.address}"
        item = {
            "label": label,
            "value": self.id
        }
        return item
