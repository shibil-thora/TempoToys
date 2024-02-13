from django.contrib import admin
from .models import Cart, Profile, State, Address, OrderItem, referral_code
from .models import PaymentModes, OrderStatus, Orders, Wishlist

admin.site.register(Cart)


class AddressAdmin(admin.ModelAdmin):
    list_display = ['id', 'profile', 'area_desc']
    


admin.site.register(Address, AddressAdmin)
admin.site.register(State)
admin.site.register(Profile)
admin.site.register(OrderStatus)
admin.site.register(PaymentModes)
admin.site.register(Orders)
admin.site.register(OrderItem)
admin.site.register(referral_code)
admin.site.register(Wishlist)


