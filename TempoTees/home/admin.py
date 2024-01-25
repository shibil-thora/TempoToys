from django.contrib import admin
from .models import Cart, Profile, State, Address, OrderItem, referral_code
from .models import PaymentModes, OrderStatus, Orders

admin.site.register(Cart)
admin.site.register(Address)
admin.site.register(State)
admin.site.register(Profile)
admin.site.register(OrderStatus)
admin.site.register(PaymentModes)
admin.site.register(Orders)
admin.site.register(OrderItem)
admin.site.register(referral_code)


