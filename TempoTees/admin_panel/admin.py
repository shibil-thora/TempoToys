from django.contrib import admin
from .models import Brand, CancelReason, UsedCoupon, Variants, Products, ProductImages, Categories, Gender
from .models import Coupon, ProductOffer, CategoryOffer
from .models import Wallet, WalletHistory


class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'id']


class VarientsAdmin(admin.ModelAdmin):
    list_display = ['size', 'color', 'id', 'product']


class ProductsAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'id',  'product_desc', 'product_desc_detailed', 'brand', 'stock', 'category', 'price']


class ProductImagesAdmin(admin.ModelAdmin):
    list_display = ['image', 'id', 'product']


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['category_name', 'id']


admin.site.register(Brand, BrandAdmin)
admin.site.register(Variants, VarientsAdmin)
admin.site.register(Products, ProductsAdmin)
admin.site.register(ProductImages)
admin.site.register(Categories, CategoryAdmin)
admin.site.register(Gender)
admin.site.register(Coupon)
admin.site.register(UsedCoupon)
admin.site.register(CategoryOffer)
admin.site.register(ProductOffer)
admin.site.register(Wallet)
admin.site.register(WalletHistory)
admin.site.register(CancelReason)
