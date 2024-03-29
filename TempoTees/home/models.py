from django.db import models
from admin_panel.models import Coupon, Products, Gender
from register.models import TempoUser


class Cart(models.Model):
    product = models.ForeignKey(Products, on_delete=models.CASCADE, related_name='cart')
    user = models.ForeignKey(TempoUser, on_delete=models.CASCADE, related_name='cart')
    quantity = models.IntegerField(default=1)
    total_price = models.DecimalField(max_digits=20, decimal_places=2, null=True)


class Wishlist(models.Model):
    product = models.ForeignKey(Products, on_delete=models.CASCADE, related_name='wishlist')
    user = models.ForeignKey(TempoUser, on_delete=models.CASCADE, related_name='wishlist')


class referral_code(models.Model):
    user = models.OneToOneField(TempoUser, on_delete=models.CASCADE, related_name='referral_code')
    code = models.CharField(max_length=10)

    def __str__(self):
        return self.code
    

class Profile(models.Model):
    user = models.OneToOneField(TempoUser, on_delete=models.CASCADE, related_name='profile')
    mobile_number = models.CharField(max_length=200, null=True)
    gender_category = models.ForeignKey(Gender, null=True, on_delete=models.SET_NULL)
    age = models.IntegerField(null=True)
    referred_code = models.ForeignKey(referral_code, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.user.username    


class State(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Address(models.Model):
    name = models.CharField(max_length=100)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='address')
    area_desc = models.TextField()
    city = models.CharField(max_length=50)
    state = models.ForeignKey(State, null=True, on_delete=models.SET_NULL)
    mobile_number = models.CharField(max_length=10)
    is_default = models.BooleanField(null=True)
    pincode = models.CharField(max_length=6, null=True)

    def __str__(self):
        return self.name
    

class OrderStatus(models.Model):
    status = models.CharField(max_length=20)

    def __str__(self):
        return self.status
    

class PaymentModes(models.Model):
    mode = models.CharField(max_length=20)

    def __str__(self):
        return self.mode
    

class Orders(models.Model):
    order_id = models.CharField(max_length=20, null=True)
    address = models.CharField(max_length=1000, null=True)
    total_amount = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    user = models.ForeignKey(TempoUser, on_delete=models.CASCADE, related_name='orders')
    date = models.DateTimeField(auto_now_add=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    paid = models.BooleanField(default=False)
    order_status = models.ForeignKey(OrderStatus, on_delete=models.RESTRICT, related_name='orders')
    payment_mode = models.ForeignKey(PaymentModes, on_delete=models.RESTRICT, related_name='orders')
    order_notes = models.TextField(null=True)
    coupon_featured_by = models.CharField(max_length=100, null=True)
    coupon_discount = models.DecimalField(max_digits=20, decimal_places=2, null=True)


class OrderItem(models.Model):
    order = models.ForeignKey(Orders, on_delete=models.CASCADE, related_name='order_items')
    item = models.ForeignKey(Products, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    is_listed = models.BooleanField(default=True)
    quantity = models.IntegerField(default=1)
    









    


