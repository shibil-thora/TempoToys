from django.db import models
from django.contrib.auth.models import AbstractUser


class TempoUser(AbstractUser):
    pass


class TempSpace(models.Model):
    user = models.OneToOneField(TempoUser, on_delete=models.CASCADE, related_name='tempspace')
    address_gb = models.IntegerField(null=True)
    payment_mode_gb = models.IntegerField(null=True)
    order_notes_gb = models.CharField(max_length=1000, null=True)
    total_amount = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    coupon_gb = models.IntegerField(null=True)

    def __str__(self):
        return f'{self.user}, {self.address_gb}, {self.payment_mode_gb}, {self.order_notes_gb}'