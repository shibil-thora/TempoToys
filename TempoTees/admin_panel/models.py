from django.db import models
from django.core.validators import MinValueValidator
from register.models import TempoUser as User
from decimal import Decimal



class Brand(models.Model):
    name = models.CharField(max_length=100)
    is_listed = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    

class Gender(models.Model):
    name = models.CharField(max_length=10)

    def __str__(self):
        return self.name
    

class Categories(models.Model):
    category_name = models.CharField(max_length=100)
    is_listed = models.BooleanField(default=True)

    def __str__(self):
        return self.category_name


class Products(models.Model):
    product_name = models.CharField(max_length=300)
    product_desc = models.TextField()
    product_desc_detailed = models.TextField()
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='products')
    stock = models.IntegerField()
    price = models.DecimalField(max_digits=20, decimal_places=2)
    category = models.ForeignKey(Categories, null=True, on_delete=models.SET_NULL, related_name='products')
    is_listed = models.BooleanField(default=True, null=False)

    def get_cat_offer_price(self):
        try:
            offer_price = self.price - (Decimal(str(self.price)) *
                                             (Decimal(self.category.offer_cat.offer_percent / 100)))
            return int(offer_price)
        except:
            return self.price
     
    def __str__(self):
        return self.product_name


class Variants(models.Model):
    size = models.CharField(max_length=10)
    color = models.CharField(max_length=50)
    product = models.ForeignKey(Products, on_delete=models.CASCADE, related_name='variants')
    
    def __str__(self):
        return f'{self.size} {self.color}'


class ProductImages(models.Model):
    image = models.ImageField(upload_to='uploads/')
    product = models.ForeignKey(Products, on_delete=models.CASCADE, related_name='images')


class Banner(models.Model):
    caption = models.CharField(max_length=100)
    image = models.ImageField(upload_to='uploads/')


class Coupon(models.Model):
    coupon_code = models.CharField(max_length=10, blank=False)
    discount_price = models.DecimalField(max_digits=20, decimal_places=2)
    min_price = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    days_valid = models.IntegerField(null=True)
    activated = models.BooleanField(default=True)
    promoter = models.CharField(max_length=100, null=True)

    def __str__(self):
        return self.coupon_code
    

class UsedCoupon(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='used_coupons')
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.coupon.coupon_code


class ProductOffer(models.Model):
    product = models.OneToOneField(Products, on_delete=models.CASCADE, related_name='offer')
    offer_percent = models.IntegerField()

    def get_offer_price(self):
        try:
            offer_price = self.product.price - (Decimal(str(self.product.price)) * (Decimal(self.offer_percent / 100)))
            return int(offer_price)
        except:
            return self.product.price
    

    

class CategoryOffer(models.Model):
    category = models.OneToOneField(Categories, on_delete=models.CASCADE, related_name='offer_cat')
    offer_percent = models.IntegerField()


class Wallet(models.Model):
    balance = models.DecimalField(max_digits=20, decimal_places=2)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')

    def __str__(self):
        return self.user.username


class WalletHistory(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='histories')
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    payment_mode = models.CharField(max_length=20)
    date = models.DateTimeField(auto_now_add=True)


class CancelReason(models.Model):
    product = models.ForeignKey(Products, on_delete=models.CASCADE, related_name='reasons')
    reason = models.CharField(max_length=500)
