from django.urls import path
from . import views


app_name = 'home_app'
urlpatterns = [
    path('', views.index, name='home'),
    path('shop/', views.shop, name='shop'),
    path('product_view/<pk>', views.product_view, name='product_view'),
    path('gender_filter_home/<q>', views.gender_filter_home, name='gender_filter_home'),
    path('gender_filter_shop/<q>', views.gender_filter_shop, name='gender_filter_shop'),
    path('gender_filter_brand/<q>', views.gender_filter_brand, name='gender_filter_brand'),
    path('prize_filter_shop/<q>', views.prize_filter_shop, name='prize_filter_shop'),
    path('cart/', views.cart, name='cart'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('checkout/', views.checkout, name='checkout'),
    path('profile/', views.profile, name='profile'),
    path('change_profile/', views.change_profile, name='change_profile'),
    path('orders/', views.my_orders, name='orders'),
    path('cancel_order_item/<item_id>/<order_id>', views.cancel_order_item, name='cancel_order_item'),
    path('add_to_cart/<product_id>', views.add_to_cart, name='add_to_cart'),
    path('remove_from_cart/<cart_id>', views.remove_from_cart, name='remove_from_cart'),
    path('remove_from_wishlist/<wish_id>', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('add_address/', views.add_address, name='add_address'),
    path('add_address_from_profile/', views.add_address_from_profile, name='add_address_from_profile'),
    path('edit_address/<pk>', views.edit_address, name='edit_address'),
    path('delete_address/<pk>', views.delete_address, name='delete_address'),
    path('add_cart_quantity/<int:cart_id>', views.add_cart_quantity, name='add_cart_quantity'),
    path('less_cart_quantity/<cart_id>', views.less_cart_quantity, name='less_cart_quantity'),
    path('clear_cart/', views.clear_cart, name='clear_cart'),
    path('place_order/', views.place_order, name='place_order'),
    path('order_details/<pk>', views.order_details, name='order_details'),
    path('success_order/', views.success_order, name='success_order'),
    path('payment_window/', views.payment_window, name='payment_window'),
    path('payment_status/', views.payment_status, name='payment_status'),
    path('payment_COD/', views.payment_COD, name='payment_COD'),
    path('payment_wallet/', views.payment_wallet, name='payment_wallet'),
    path('apply_coupon/<code>', views.apply_coupon, name='apply_coupon'),
    path('wallet/', views.wallet, name='wallet'),
    path('apply_referral/', views.apply_referral, name='apply_referral'),
    path('download_invoice/<pk>', views.download_invoice, name='download_invoice'),
]


