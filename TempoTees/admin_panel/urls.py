from django.urls import path
from . import views


app_name = 'admin_app'
urlpatterns = [
    path('', views.admin_dash, name='admin'),   
    path('users/', views.users, name='users'),
    path('block/<pk>', views.block, name='block'),
    path('activate/<pk>', views.activate, name='activate'),
    path('products/', views.products, name='products'),
    path('add_product/', views.add_product, name='add_product'),
    path('unlist/<pk>', views.unlist, name='unlist'),
    path('list/<pk>', views.list, name='list'),
    path('edit_product/<pk>', views.edit_product, name='edit_product'),
    path('delete_images/<pk>/<p_id>', views.delete_images, name='delete_images'),
    path('categories/', views.categories, name='categories'),
    path('add_category/', views.add_category, name='add_category'),
    path('edit_category/<pk>', views.edit_category, name='edit_category'),
    path('delete_category/<pk>', views.delete_category, name='delete_category'),
    path('brands/', views.brands, name='brands'),
    path('add_brand/', views.add_brand, name='add_brand'),
    path('edit_brand/<pk>', views.edit_brand, name='edit_brand'),
    path('delete_brand/<pk>', views.delete_brand, name='delete_brand'),
    path('admin_orders/', views.admin_orders, name='admin_orders'),
    path('admin_order_details/<pk>', views.admin_order_details, name='admin_order_details'),
    path('change_to_delivered/<pk>', views.change_to_delivered, name='change_to_delivered'),
    path('change_to_dispatched/<pk>', views.change_to_dispatched, name='change_to_dispatched'),
    path('change_to_out/<pk>', views.change_to_out, name='change_to_out'),
    path('cancel_order/<pk>', views.cancel_order, name='cancel_order'),
    path('load_file/', views.load_file, name='load_file'),
    path('coupons/', views.coupons, name='coupons'),
    path('offers/', views.offers, name='offers'),
    path('add_product_offer/', views.add_product_offer, name='add_product_offer'),
    path('delete_product_offer/<pk>', views.delete_product_offer, name='delete_product_offer'),
    path('delete_category_offer/<pk>', views.delete_category_offer, name='delete_category_offer'),
    path('edit_product_offer/<pk>', views.edit_product_offer, name='edit_product_offer'),
    path('edit_category_offer/<pk>', views.edit_category_offer, name='edit_category_offer'),
    path('add_category_offer/', views.add_category_offer, name='add_category_offer'),
    path('add_coupon/', views.add_coupon, name='add_coupon'),
    path('edit_coupon/<pk>', views.edit_coupon, name='edit_coupon'),
    path('delete_coupon/<pk>', views.delete_coupon, name='delete_coupon'),
    path('activate_coupon/<pk>', views.activate_coupon, name='activate_coupon'),
]
