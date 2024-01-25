from django.forms import ModelForm
from .models import Coupon, ProductOffer, CategoryOffer

class CouponForm(ModelForm):
    class Meta:
        model = Coupon
        fields = '__all__'


class ProductOfferForm(ModelForm):
    class Meta:
        model = ProductOffer
        fields = '__all__'


class CategoryOfferForm(ModelForm):
    class Meta:
        model = CategoryOffer
        fields = '__all__'
        