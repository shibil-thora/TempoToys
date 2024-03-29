from django.urls import path
from . import views



app_name = 'register_app'
urlpatterns = [
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('signup/', views.signup_user, name='signup'),
    path('otp/', views.otp, name='otp'),
]
