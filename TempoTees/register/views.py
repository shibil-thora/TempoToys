from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
import random
from datetime import timedelta, timezone, datetime
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.cache import never_cache
import pyotp
from .models import TempoUser as User
from django.core.validators import EmailValidator
from home.models import referral_code


#============== this is global template for user details =====================#
interval = 85  #seconds
otp_obj = pyotp.TOTP('base32secret3232', interval=interval)
temp_username = None
temp_password = None
temp_email = None
temp_first_name = None
temp_last_name = None


#=================================== LOGIN ===================================#
@never_cache
def login_user(request):
    if not request.user.is_authenticated:
        if request.method == 'POST':
            username = request.POST['username']
            password = request.POST.get('password')
            if '@' and '.' in username:
                try:
                    username = User.objects.get(email=username).username
                except:
                    user = None

            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'you have been logged in succesfully!')
                if user.is_superuser:
                    return redirect('a:admin')
                return redirect('h:home')
            
            else:
                messages.error(request, 'Login failed! Ensure your username, email, and password are correct')
                return redirect('r:login')
            
        return render(request, 'login.html')
    return redirect('h:home')


#=================================== send_mail_to_user ===================================#
def send_mail_to_user(email, otp):
    try:
        subject = 'TempoTees Verification'
        message = f'Your OTP is: {otp}'
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [email]
        send_mail(subject=subject, message=message, from_email=from_email, recipient_list=recipient_list)
    except:
        return redirect('r:signup')



#=================================== SIGNUP ===================================#
def signup_user(request):
    if not request.user.is_authenticated:
        if request.method == 'POST': 

            username = request.POST.get('username')
            username = username.strip()
            email = request.POST.get('email')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            password_1 = request.POST.get('password1')
            password_2 = request.POST.get('password2')

            password_1 = password_1.strip()
            password_2 = password_2.strip()
            
            if len(username) < 5:
                return render(request, 'signup.html', {'error': 'username must be atleast 5 charecters'})
            
            if User.objects.filter(username=username):
                return render(request, 'signup.html', {'error': 'username already exists'})
            
            
            if User.objects.filter(email=email):
                return render(request, 'signup.html', {'error': 'email already exists'})
            
            if '@' not in email or '.' not in email :
                return render(request, 'signup.html', {'error': 'invalid email format!'})
            
            if len(password_1) < 8:
                return render(request, 'signup.html', {'error': 'passwords must be atleast 8 characters'})
            
            try:
                int(password_1)
                return render(request, 'signup.html', {'error': 'passwords must contain letters and numbers'})
            except:
                pass
            
            if not password_1 == password_2:
                return render(request, 'signup.html', {'error': 'passwords do not match'})
            
            global temp_username
            global temp_password 
            global temp_email 
            global temp_first_name 
            global temp_last_name

            otp = otp_obj.now()
            send_mail_to_user(email=email, otp=otp)
            

            temp_username = username
            temp_password = password_1
            temp_email = email
            temp_first_name = first_name
            temp_last_name = last_name

            return redirect('r:otp')
        return render(request, 'signup.html')
    return redirect('h:home')


#=================================== OTP VIEW ===================================#
def otp(request):
    if request.method == 'POST':
        otp = request.POST.get('otp')
        if not otp == otp_obj.now():
            messages.success(request, 'invalid otp! sign in again')
            return redirect('r:signup')

        new_user = User.objects.create_user(username=temp_username, email=temp_email, password=temp_password)
        new_user.first_name = temp_first_name
        new_user.last_name = temp_last_name
        code = 'Ab' + str(random.randint(0,1000)) + 'Tb'
        referral_code.objects.create(user=new_user, code=code)
        new_user.save()
        
        return redirect('r:login')
    return render(request, 'otp.html')


#=================================== LOGOUT ===================================#
def logout_user(request):
    logout(request)
    return redirect('r:login')



