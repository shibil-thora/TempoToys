from django.utils import timezone
from io import BytesIO
import json
from django.shortcuts import render, redirect
from django.http import FileResponse, HttpResponse
from django.views.decorators.cache import never_cache
from admin_panel.models import Brand, CancelReason, Categories, Products, Gender, Wallet
from .models import Cart, Profile, State, Address, Orders, OrderStatus, PaymentModes, OrderItem, Wishlist, referral_code
from admin_panel.models import WalletHistory
from register.models import TempSpace, TempoUser as User
from django.contrib.sessions.models import Session
from django.db.models import Sum
from django.contrib import messages
from django.http import Http404, HttpResponseBadRequest, JsonResponse
import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login
from admin_panel.models import Coupon
from admin_panel.models import ProductOffer, CategoryOffer, UsedCoupon
from django.core.paginator import Paginator
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.units import inch
import random
from django.db.models import Q


#=================================== LANDING PAGE ===================================#
@never_cache
def index(request):
    context = {
        'products': Products.objects.all().order_by('-id').filter(is_listed=True).filter(brand__is_listed=True).filter(category__is_listed=True)
    }
    return render(request, 'index.html', context)


#=================================== FILTER BY GENDER HOME ===================================#
def gender_filter_home(request, q):
    context = {
        'products': Products.objects.all().filter(category__category_name=q).filter(is_listed=True).order_by('-id')
    }
    return render(request, 'index.html', context)
    

#=================================== SHOP VIEW ===================================#
@never_cache
def shop(request):
    if request.user.is_authenticated:
        products = Products.objects.filter(is_listed=True).order_by('-id').filter(brand__is_listed=True).filter(category__is_listed=True)
        paginator = Paginator(products, 3)
        page = request.GET.get('page', 1)

        try:
            venues = paginator.page(page)
        except :
            raise Http404("Page not found")

        context = {
            'products': venues,
            'venues': venues,
            'categories': Categories.objects.all().filter(is_listed=True),
            'brands': Brand.objects.all().filter(is_listed=True),
        }
        return render(request, 'shop.html', context)
    return redirect('r:login')

#=================================== GENDER FILTER SHOP ===================================#
@never_cache
def gender_filter_shop(request, q):
    if request.user.is_authenticated:
        context = {
            'products': Products.objects.all().filter(category__category_name=q).filter(is_listed=True)
        }
        return render(request, 'shop.html', context)
    return redirect('r:login')


#=================================== GENDER FILTER Brand ===================================#
@never_cache
def gender_filter_brand(request, q):
    if request.user.is_authenticated:
        context = {
            'products': Products.objects.all().filter(brand__name=q).filter(is_listed=True)
        }
        return render(request, 'shop.html', context)
    return redirect('r:login')


#=================================== PRIZE RANGE FILTER ===================================#
@never_cache
def prize_filter_shop(request, q):
    if request.user.is_authenticated:
        products = None
        if q == '0-600':
            products = Products.objects.all().filter(price__lte=600).filter(is_listed=True)
        elif q == '600-1200':
            products = Products.objects.all().filter(price__gt=600, price__lte=1200).filter(is_listed=True)
        elif 1 == '1200 above':
            products = Products.objects.all().filter(price__gt=1200).filter(is_listed=True)
        context = {
            'products': products
        }
        return render(request, 'shop.html', context)
    return redirect('r:login')


#=================================== PRODUCT VIEW ===================================#
@never_cache
def product_view(request, pk):
    if request.user.is_authenticated:
        try:
            product = Products.objects.get(id=pk)
            is_carted = request.user.cart.all().filter(product=product)
            is_wished = request.user.wishlist.all().filter(product=product)
            context = {
                'product': product,
                'is_carted': is_carted,
                'is_wished': is_wished
            }
        except:
            return redirect('r:login')
        return render(request, 'view_product.html', context)
    return redirect('r:login')


#=================================== CART VIEW ===================================#
@never_cache
def cart(request):
    if request.user.is_authenticated:
        if Cart.objects.filter(user=request.user):
            sum_w = Cart.objects.filter(user=request.user).aggregate(total = Sum('total_price'))['total'] + 20
        else:
            sum_w = 0
        context = {
            'carts': Cart.objects.filter(user=request.user).order_by('-id'),
            'sum': sum_w,
            'sum_without_shipp': Cart.objects.filter(user=request.user).aggregate(total = Sum('total_price'))['total'],
        }
        return render(request, 'cart.html', context)
    return redirect('r:login')


#=================================== CART VIEW ===================================#
@never_cache
def wishlist(request):
    if request.user.is_authenticated:
        return render(request, 'wishlist.html')
    return redirect('r:login')


#=================================== ADD TO CART ===================================#
@never_cache
def add_to_cart(request, product_id):
    if request.user.is_authenticated:
        if Cart.objects.filter(product__id=product_id, user__id=request.user.id):
            return redirect('h:cart')
        try:
            Wishlist.objects.filter(product_id=product_id).delete()
            product_obj = Products.objects.get(id=product_id)
            price = product_obj.price
            if ProductOffer.objects.filter(product=product_obj):
                price = product_obj.offer.get_offer_price()
            elif CategoryOffer.objects.filter(category=product_obj.category):
                price = product_obj.get_cat_offer_price()

            if product_obj.stock > 0:
                cart_obj = Cart.objects.create(user=request.user, product=product_obj, total_price=price)
                cart_obj.save()
                return redirect('h:cart')
            return redirect('h:cart')
        except:
            return redirect('h:cart')
    return redirect('r:login')


#=================================== ADD TO WISHLIST ===================================#
@never_cache
def add_to_wishlist(request, product_id):
    if request.user.is_authenticated:
        if Wishlist.objects.filter(product__id=product_id, user__id=request.user.id):
            return redirect('h:product_view', pk=product_id)
        try:
            product_obj = Products.objects.get(id=product_id)
            wish_obj = Wishlist.objects.create(user=request.user, product=product_obj)
            wish_obj.save()
            return redirect('h:product_view', pk=product_id)
        except:
            return redirect('h:product_view', pk=product_id)
    return redirect('r:login')



#=================================== ADD CART QUANTITY ===================================#
@never_cache
def add_cart_quantity(request, cart_id):
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(id=cart_id)
            if cart.quantity < cart.product.stock:
                cart.quantity += 1
                cart.total_price += cart.product.price
                cart.save()
                data = {
                    'quantity': cart.quantity,
                    'total_price': cart.total_price,
                    'message': 'quantity added!',
                    'sum': Cart.objects.filter(user=request.user).aggregate(total=Sum('total_price'))['total'] + 20,
                    'sum_without_shipp': Cart.objects.filter(user=request.user).aggregate(total = Sum('total_price'))['total'],
                }
                return JsonResponse(data)
            data = {
                    'quantity': cart.quantity,
                    'total_price': cart.total_price,
                    'message': 'out of stock!',
                    'sum': Cart.objects.filter(user=request.user).aggregate(total=Sum('total_price'))['total'] + 20,
                    'sum_without_shipp': Cart.objects.filter(user=request.user).aggregate(total = Sum('total_price'))['total'],
            
                }
            return JsonResponse(data)
        except:
            return redirect('h:cart')
        
    return redirect('r:login')


#=================================== REMOVE CART QUANTITY ===================================#
@never_cache
def less_cart_quantity(request, cart_id):
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(id=cart_id)
            if cart.quantity > 1:
                cart.quantity -= 1
                cart.total_price -= cart.product.price
            cart.save()
            data = {
                'quantity': cart.quantity,
                'total_price': cart.total_price,
                'message': 'quantity updated',
                'sum': Cart.objects.filter(user=request.user).aggregate(total=Sum('total_price'))['total'] + 20,
                'sum_without_shipp': Cart.objects.filter(user=request.user).aggregate(total = Sum('total_price'))['total'],
            
            }
            return JsonResponse(data)
        except:
            data = {
                'quantity': cart.quantity,
                'total_price': cart.total_price,
                'message': 'out of stock!',
                'sum': Cart.objects.filter(user=request.user).aggregate(total=Sum('total_price'))['total'] + 20,
                'sum_without_shipp': Cart.objects.filter(user=request.user).aggregate(total = Sum('total_price'))['total'],
            
            }
            return JsonResponse(data)
    return redirect('r:login')
    

#=================================== CLEAR CART ===================================#
@never_cache
def clear_cart(request):
    if request.user.is_authenticated:
        try:
            request.user.cart.all().delete()
            return redirect('h:cart')
        except:
            return redirect('h:cart')
    return redirect('r:login')


#=================================== REMOVE FROM CART ===================================#
@never_cache
def remove_from_cart(request, cart_id):
    if request.user.is_authenticated:
        try:
            cart_obj = Cart.objects.get(id=cart_id)
            cart_obj.delete()
            return redirect('h:cart')
        except:
            return redirect('h:cart')
    return redirect('r:login')


#=================================== REMOVE FROM WISH LIST ===================================#
@never_cache
def remove_from_wishlist(request, wish_id):
    if request.user.is_authenticated:
        try:
            wish_obj = Wishlist.objects.get(id=wish_id)
            wish_obj.delete()
            return redirect('h:wishlist')
        except:
            return redirect('h:wishlist')
    return redirect('r:login')



#=================================== CHECKOUT VIEW ===================================#
# address_gb = None
# payment_mode_gb = None
# order_notes_gb = None
# user_id_gb = None
# coupon_gb = None
@never_cache
def checkout(request):
    if request.user.is_authenticated:
        request.session['user_id_gb'] = request.user.id
        if request.method != 'POST':
            TempSpace.objects.filter(user=request.user).delete()
        try: 
            carts = request.user.cart.all()
            shipping_charge = 20
            total_amount = Cart.objects.filter(user=request.user).aggregate(total=Sum('total_price'))['total']
            if request.method != 'POST':
                TempSpace.objects.create(user=request.user, total_amount=total_amount+20)
        except:
            return redirect('r:login')
        try:
            context = {
                    'carts': carts,
                    'shipping_charge': shipping_charge,
                    'cart_sum': total_amount,
                    'sum': total_amount + shipping_charge,
                    'addresses': Address.objects.all().filter(profile=request.user.profile).order_by('-id'),
                    'payment_modes': PaymentModes.objects.all(),
                    'key_id': settings.RAZOR_KEY_ID,
                }
        except:
            return redirect('r:login')
        if request.method == 'POST': 
            carts = request.user.cart.all()
            for cart in carts:
                if cart.quantity > cart.product.stock:
                    messages.success(request, 'sorry! stock is not enough decrease the number!')
                    return redirect('h:cart')
            try:    
                address = request.POST.get('address')
                order_notes = request.POST.get('order_notes')
                payment_mode = request.POST.get('payment_mode')
                payment_mode_obj = PaymentModes.objects.get(mode=payment_mode)
                address_obj = Address.objects.get(id=int(address))
            except:
                messages.success(request, 'please select all fields proprely')
                return redirect('h:checkout')

            request.session['address_gb'] = address_obj.id
            request.session['payment_mode_gb'] = payment_mode_obj.id
            request.session['order_notes_gb'] = order_notes
            try:
                tempspace = request.user.tempspace
                tempspace.address_gb = address_obj.id
                tempspace.payment_mode_gb = payment_mode_obj.id
                tempspace.order_notes_gb = order_notes
                tempspace.save()
            except:
                return redirect('r:login')

            return redirect ('h:payment_window', request.user.id)
        return render(request, 'checkout.html', context)
    return redirect('r:login')


#=================================== APPLY COUPON ===================================#
@never_cache
def apply_coupon(request, code):
    if request.user.is_authenticated:
        try:
            #UsedCoupon.objects.filter(user=request.user, coupon=coupon):
            coupon = Coupon.objects.get(coupon_code=code)
            data = {
                'discount_price': coupon.discount_price
            }
            request.session['coupon_gb'] = code
            tempspace = request.user.tempspace
            tempspace.coupon_gb = coupon.id
            tempspace.save()
            if not coupon.activated:
                coupon = False
                data = {
                    'discount_price': 0
                }
                request.session['coupon_gb'] = None
                tempspace = request.user.tempspace
                tempspace.coupon_gb = None
                tempspace.save()

            if UsedCoupon.objects.filter(user=request.user, coupon=coupon):
                coupon = False
                data = {
                    'discount_price': 0
                }
                request.session['coupon_gb'] = None
                tempspace = request.user.tempspace
                tempspace.coupon_gb = None
                tempspace.save()
        except:
            coupon = False
            data = {
                'discount_price': 0
            }
            request.session['coupon_gb'] = None
            tempspace = request.user.tempspace
            tempspace.coupon_gb = None
            tempspace.save()
        return JsonResponse(data)
    

#=================================== PAYMENT WINDOW ===================================#
response_payment = None
@csrf_exempt
def payment_window(request, pk):

    tempspace = request.user.tempspace
    total_amount = tempspace.total_amount
    try:
        coupon_gb = Coupon.objects.get(id=tempspace.coupon_gb)
    except:
        coupon_gb = None

    address_gb = Address.objects.get(id=request.session.get('address_gb'))
    payment_mode_gb = PaymentModes.objects.get(id=request.session.get('payment_mode_gb'))
    user_id_gb = request.session.get('user_id_gb')
    order_notes_gb = request.session.get('order_notes_gb')
    if coupon_gb is not None:
        total_amount = total_amount - coupon_gb.discount_price
        tempspace.total_amount = total_amount
        tempspace.save()
    
    request.session['total_amount'] = int(total_amount)
    if request.user.is_authenticated:
        client = razorpay.Client(auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))
        payment_dict = {
                'amount': int(total_amount) * 100,
                'currency': 'INR',
            }
        global response_payment
        response_payment = client.order.create(payment_dict)
        if payment_mode_gb == PaymentModes.objects.get(mode='COD'):
            response_payment = False
        elif payment_mode_gb == PaymentModes.objects.get(mode='wallet'):
            response_payment = 'wallet'
        context = {
            'carts': Cart.objects.filter(user=request.user),
            'total': total_amount,
            'payment': response_payment,
            'data_key': settings.RAZOR_KEY_ID,
        }
        return render(request, 'payment_window.html', context)
    return redirect('r:login')


#=================================== PAYMENT STATUS ===================================#
@csrf_exempt
def payment_status(request, pk):
    def get_session_data_by_user_id(user_id):
        try:
            session = Session.objects.filter(expire_date__gt=timezone.now(), session_data__contains=str(user_id)).latest('expire_date')
            session_data_dict = session.get_decoded()

            return session_data_dict
        except Session.DoesNotExist:
            return None
        
    user_obj = User.objects.get(id=pk)
    session = get_session_data_by_user_id(pk)
    total_amount = user_obj.tempspace.total_amount

    response = request.POST
    params_dict = {
        'razorpay_order_id': response['razorpay_order_id'],
        'razorpay_payment_id': response['razorpay_payment_id'],
        'razorpay_signature': response['razorpay_signature'],
    }

    client = razorpay.Client(auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))
    try:
        coupon_gb = Coupon.objects.get(id=user_obj.tempspace.coupon_gb)
    except:
        coupon_gb = None

    address_gb = Address.objects.get(id=int(user_obj.tempspace.address_gb))
    payment_mode_gb = PaymentModes.objects.get(id=user_obj.tempspace.payment_mode_gb)
    user_id_gb = pk
    order_notes_gb = user_obj.tempspace.order_notes_gb
    try:
        order_id = response_payment['id']
        order_status = response_payment['status']
        response_payment['name'] = 'temporary user'
        user_obj = User.objects.get(id=user_id_gb)
        address_str =  f'''
        {address_gb.name} {address_gb.area_desc} 
        {address_gb.city} {address_gb.state} {address_gb.pincode}
        Contact: {address_gb.mobile_number}
        '''

        if order_status == 'created': 
            order = Orders.objects.create(
            address=address_str,
            total_amount=total_amount,
            user=user_obj,
            order_status=OrderStatus.objects.get(status='pending'),
            payment_mode=payment_mode_gb,
            order_notes=order_notes_gb,
            order_id=order_id
            )
            if coupon_gb is not None:
                UsedCoupon.objects.create(coupon=coupon_gb, user=user_obj)
                order.coupon_featured_by = coupon_gb.promoter
                order.coupon_discount = coupon_gb.discount_price
                order.save()
             
        status = client.utility.verify_payment_signature(params_dict)
        order = Orders.objects.get(order_id=response['razorpay_order_id'])
        order.razorpay_payment_id = response['razorpay_payment_id']
        order.paid = True
        order.save()
        TempSpace.objects.filter(user=user_obj).delete()
        for cart in user_obj.cart.all():
                order_item = OrderItem.objects.create(
                    order=order,
                    item=cart.product,
                    quantity=cart.quantity,
                )
                product = cart.product
                product.stock -= cart.quantity
                product.save()
                order_item.price = product.price
                order_item.save()
                Cart.objects.filter(user=user_obj).delete()
        Cart.objects.filter(user=user_obj).delete()
        return render(request, 'order_success.html', {'status': True})
    except:
        order_id = 'NY7T90BHR' + str(random.randint(100000, 199999))
        session = get_session_data_by_user_id(pk)
        order_status = 'created'
        user_obj = User.objects.get(id=user_id_gb)
        address_str =  f'''
        {address_gb.name} {address_gb.area_desc} 
        {address_gb.city} {address_gb.state} {address_gb.pincode}
        Contact: {address_gb.mobile_number}
        '''

        if order_status == 'created': 
            order = Orders.objects.create(
            address=address_str,
            total_amount=total_amount,
            user=user_obj,
            order_status=OrderStatus.objects.get(status='pending'),
            payment_mode=payment_mode_gb,
            order_notes=order_notes_gb,
            order_id=order_id
            )
            order.save()
            if coupon_gb is not None:
                UsedCoupon.objects.create(coupon=coupon_gb, user=user_obj)

        status = client.utility.verify_payment_signature(params_dict)
        order = Orders.objects.get(order_id=order_id)
        order.paid = True
        if coupon_gb is not None: 
            order.coupon_featured_by = coupon_gb.promoter
            order.coupon_discount = coupon_gb.discount_price
        order.save()
        TempSpace.objects.filter(user=user_obj).delete()
        for cart in user_obj.cart.all():
                order_item = OrderItem.objects.create(
                    order=order,
                    item=cart.product,
                    quantity=cart.quantity,
                )
                product = cart.product
                product.stock -= cart.quantity
                product.save()
                order_item.price = product.price
                order_item.save()
                Cart.objects.filter(user=user_obj).delete()
        Cart.objects.filter(user=user_obj).delete()
        return render(request, 'order_success.html', {'status': True})



#=================================== PAYMENT COD ===================================#
def payment_COD(request):
    if request.POST:
        try:
            coupon_gb = Coupon.objects.get(coupon_code=request.session.get('coupon_gb'))
        except:
            coupon_gb = None
        address_gb = Address.objects.get(id=request.session.get('address_gb'))
        payment_mode_gb = PaymentModes.objects.get(id=request.session.get('payment_mode_gb'))
        user_id_gb = request.session.get('user_id_gb')
        order_notes_gb = request.session.get('order_notes_gb')
        user_obj = User.objects.get(id=user_id_gb)
        address_str =  f'''
        {address_gb.name} {address_gb.area_desc} 
        {address_gb.city} {address_gb.state} {address_gb.pincode}
        Contact: {address_gb.mobile_number}
        '''
        total_amount = request.session.get('total_amount')
        order = Orders.objects.create(
        address=address_str,
        total_amount=total_amount,
        user=user_obj,
        order_status=OrderStatus.objects.get(status='pending'),
        payment_mode=payment_mode_gb,
        order_notes=order_notes_gb,
        )
        order.order_id = '270000000' + str(order.id)
        if coupon_gb is not None: 
            order.coupon_featured_by = coupon_gb.promoter
            order.coupon_discount = coupon_gb.discount_price
        order.save()
        if coupon_gb is not None:
                UsedCoupon.objects.create(coupon=coupon_gb, user=user_obj)
        
        order.paid = True
        order.save()
        TempSpace.objects.filter(user=user_obj).delete()
        for cart in user_obj.cart.all():
                order_item = OrderItem.objects.create(
                    order=order,
                    item=cart.product,
                    quantity=cart.quantity,
                )
                product = cart.product
                product.stock -= cart.quantity
                product.save()
                order_item.price = product.price
                order_item.save()
                Cart.objects.filter(user=user_obj).delete()
        Cart.objects.filter(user=user_obj).delete()
        return render(request, 'order_success.html', {'status': True})
    

#=================================== PAYMENT WAllET ===================================#
def payment_wallet(request):
    if request.POST:
        try:
            coupon_gb = Coupon.objects.get(coupon_code=request.session.get('coupon_gb'))
        except:
            coupon_gb = None
        address_gb = Address.objects.get(id=request.session.get('address_gb'))
        payment_mode_gb = PaymentModes.objects.get(id=request.session.get('payment_mode_gb'))
        user_id_gb = request.session.get('user_id_gb')
        order_notes_gb = request.session.get('order_notes_gb')
        user_obj = User.objects.get(id=user_id_gb)
        address_str =  f'''
        {address_gb.name} {address_gb.area_desc} 
        {address_gb.city} {address_gb.state} {address_gb.pincode}
        Contact: {address_gb.mobile_number}
        '''
        wallet = None
        try:
            wallet = user_obj.wallet
        except:
            wallet = Wallet.objects.create(user=user_obj, balance=0)
        
        total_amount = request.session.get('total_amount')
        if wallet.balance < total_amount: 
            messages.success(request, 'wallet has not enough money')
            return redirect('h:checkout')
        
        order = Orders.objects.create(
        address=address_str,
        total_amount=total_amount,
        user=user_obj,
        order_status=OrderStatus.objects.get(status='pending'),
        payment_mode=payment_mode_gb,
        order_notes=order_notes_gb,
        )

        wallet.balance -= order.total_amount
        wallet.save()
        WalletHistory.objects.create(
            wallet=wallet,
            amount= -1 * (order.total_amount),
            payment_mode=order.payment_mode.mode,
        )
        order.order_id = '270000000' + str(order.id)
        order.save()
        TempSpace.objects.filter(user=user_obj).delete()

        if coupon_gb is not None:
                UsedCoupon.objects.create(coupon=coupon_gb, user=user_obj)
        
        order.paid = True
        if coupon_gb is not None: 
            order.coupon_featured_by = coupon_gb.promoter
            order.coupon_discount = coupon_gb.discount_price
        order.save()
        for cart in user_obj.cart.all():
                order_item = OrderItem.objects.create(
                    order=order,
                    item=cart.product,
                    quantity=cart.quantity,
                )
                product = cart.product
                product.stock -= cart.quantity
                product.save()
                order_item.price = product.price
                order_item.save()
                Cart.objects.filter(user=user_obj).delete()
        Cart.objects.filter(user=user_obj).delete()
        return render(request, 'order_success.html', {'status': True})
    
    
#=================================== PLACE ORDER ===================================#
# @csrf_exempt
@never_cache
def place_order(request):
    if request.method == 'POST':
        try:
            coupon_gb = Coupon.objects.get(coupon_code=request.session.get('coupon_gb'))
        except:
            coupon_gb = None
        address_gb = Address.objects.get(id=request.session.get('address_gb'))
        payment_mode_gb = PaymentModes.objects.get(id=request.session.get('payment_mode_gb'))
        user_id_gb = request.session.get('user_id_gb')
        order_notes_gb = request.session.get('order_notes_gb')
        try:
            order = Orders.objects.create(
                address=address_gb,
                total_amount=Cart.objects.filter(user=request.user).aggregate(total=Sum('total_price'))['total'] + 20,
                user=request.user,
                order_status=OrderStatus.objects.get(status='pending'),
                payment_mode=payment_mode_gb,
                order_notes=order_notes_gb,
            )
            order.order_id = '270000000' + str(order.id)
            order.save()
            for cart in request.user.cart.all():
                order_item = OrderItem.objects.create(
                    order=order,
                    item=cart.product,
                    quantity=cart.quantity,
                )
                product = cart.product
                product.stock -= cart.quantity
                product.save()
                order_item.save()
                Cart.objects.filter(user=request.user).delete()
            return redirect('h:payment_window')
        except:
            messages.success(request, 'something went wrong!')
            return redirect('h:home')
    return redirect('h:home')


#=================================== ORDER SUCCESS ===================================#
@never_cache
@csrf_exempt
def success_order(request):
    if request.method == 'POST':
        a = request.POST
        order_id = ""
        for key, val in a.items():
            if key == 'razorpay_order_id':
                order_id = val
                break
        
    return render(request, 'order_success.html')


#=================================== PROFILE VIEW ===================================#
@never_cache
def profile(request):
    if request.user.is_authenticated:
        return render(request, 'profile.html')
    return redirect('r:login')


#=================================== CHANGE PROFILE ===================================#
@never_cache
def change_profile(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            gender = request.POST.get('gender')
            mobile_number = request.POST.get('mobile_number')
            age = request.POST.get('age')

            error_occured = False
            if Profile.objects.exclude(user=request.user).filter(mobile_number=mobile_number):
                error_occured = True
                messages.success(request, 'this mobile number is already attached with another account')
                return render(request, 'profile.html', {'error': 'this mobile number is already attached with another account'})
            
            if not gender:
                error_occured = True
                messages.success(request, 'category required!')
                return render(request, 'profile.html', {'error': 'category required!'})
            

            try:
                int(mobile_number)
            except:
                error_occured = True
                messages.success(request, 'invalid mobile number!')
                return render(request, 'profile.html', {'error': 'invalid mobile number!'})
            

            if not error_occured:
                try:
                    user = request.user
                    user.first_name = first_name
                    user.last_name = last_name
                    user.save()
                except:
                    return redirect('h:profile')
                try:
                    gender_obj = Gender.objects.get(name=gender)
                except:
                    return redirect('h:profile')

                try:
                    profile = Profile.objects.get(user=request.user)
                    profile.mobile_number = mobile_number
                    profile.gender_category = gender_obj
                    profile.age = age
                    profile.save()
                    return redirect('h:profile')
                except:
                    profile = Profile.objects.create(
                        user=request.user,
                        mobile_number=mobile_number,
                        gender_category=gender_obj,
                        age=age
                    )
                    profile.save()
                    return redirect('h:profile')
            
             

        return render(request, 'profile.html')
    return redirect('r:login')


#=================================== USER ORDERS VIEW ===================================#
@never_cache
def my_orders(request):
    if request.user.is_authenticated:
        cancel_status = OrderStatus.objects.get(status='cancelled')
        context = {
            'avoid': True,
            'orders': Orders.objects.filter(user=request.user).order_by('-id')
        }
        return render(request, 'user_order.html', context)
    return redirect('r:login')


#=================================== ORDER DETAILS VIEW ===================================#
@never_cache
def order_details(request, pk):
    if request.user.is_authenticated:
        try:
            order = Orders.objects.get(id=pk)
            context = {
                'avoid': True,
                'items': OrderItem.objects.filter(order=order, is_listed=True),
                'order': order,
            }
            return render(request, 'order_detail_user.html', context )
        except:
            return redirect('h:home')
    return redirect('r:login')


#=================================== ADD ADDRESSES ===================================#
@never_cache
def add_address(request):
    if request.user.is_authenticated:
        if request.method == 'POST': 
            name = request.POST.get('name')
            pincode = request.POST.get('pincode')
            area_desc = request.POST.get('area_desc')
            city = request.POST.get('city')
            state = request.POST.get('state')
            mobile_number = request.POST.get('mobile_number')

            error_occured = False
            
            try:
                int(pincode)
            except:
                error_occured = True
                messages.success(request, 'invalid pincode!')
                return redirect('add_address')
            

            
            if not error_occured:
                try:
                    state_obj = State.objects.get(name=state)
                    address = Address.objects.create(
                        name=name,
                        profile=request.user.profile,
                        area_desc=area_desc,
                        city=city,
                        state=state_obj,
                        mobile_number=mobile_number,
                        pincode=pincode,
                    )
                    Address.objects.update(is_default=False)
                    address.is_default = True
                    address.save()
                    return redirect('h:checkout')

                except:
                    messages.success(request, 'something went wrong')
                    return redirect('h:add_address')
        context = {
            'states': State.objects.all(),
            'profile': False
        }
        return render(request, 'add_address.html', context)
    return redirect('r:login')


#=================================== ADD ADDRESSES FROM PROFILE ===================================#
@never_cache
def add_address_from_profile(request):
    if request.user.is_authenticated:
        if request.method == 'POST': 
            name = request.POST.get('name')
            pincode = request.POST.get('pincode')
            area_desc = request.POST.get('area_desc')
            city = request.POST.get('city')
            state = request.POST.get('state')
            mobile_number = request.POST.get('mobile_number')

            error_occured = False
            
            try:
                int(pincode)
            except:
                error_occured = True
                messages.success(request, 'invalid pincode!')
                return redirect('add_address_from_profile')
            

            
            if not error_occured:
                try:
                    state_obj = State.objects.get(name=state)
                    address = Address.objects.create(
                        name=name,
                        profile=request.user.profile,
                        area_desc=area_desc,
                        city=city,
                        state=state_obj,
                        mobile_number=mobile_number,
                        pincode=pincode,
                    )
                    Address.objects.update(is_default=False)
                    address.is_default = True
                    address.save()
                    return redirect('h:profile')

                except:
                    messages.success(request, 'something went wrong')
                    return redirect('h:add_address_from_profile')
        context = {
            'states': State.objects.all(),
            'profile': True
        }
        return render(request, 'add_address.html', context)
    return redirect('r:login')



#=================================== EDIT ADDRESSES ===================================#
@never_cache
def edit_address(request, pk):
    if request.user.is_authenticated:
        address = Address.objects.get(id=pk)
        if request.method == 'POST': 
            name = request.POST.get('name')
            pincode = request.POST.get('pincode')
            area_desc = request.POST.get('area_desc')
            city = request.POST.get('city')
            state = request.POST.get('state')
            mobile_number = request.POST.get('mobile_number')


            error_occured = False
            if len(area_desc) < 50:
                error_occured = True
                messages.success(request, 'area description should be descriptive!')
                context = {
                    'states': State.objects.all(),
                    'error': 'area description should be descriptive!',
                    'address': address
                }
                return render(request, 'edit_address.html',context)
            
            try:
                int(pincode)
            except:
                error_occured = True
                messages.success(request, 'invalid pincode!')
                context = {
                    'states': State.objects.all(),
                    'error': 'invalid pincode!',
                    'address': address
                }
                return render(request, 'edit_address.html',context)
            

            if not error_occured:
                try:
                    state_obj = State.objects.get(name=state)
                    address.name = name
                    address.pincode = pincode
                    address.area_desc = area_desc
                    address.city = city
                    address.state = state_obj
                    address.mobile_number = mobile_number
                    address.save()
                    
                    return redirect('h:edit_address', pk=pk)
                except:
                    messages.success(request, 'something went wrong!')
                    return redirect('h:edit_address', pk=pk)
            
        context = {
            'states': State.objects.all(),
            'address': address
        }
        return render(request, 'edit_address.html', context)
    return redirect('r:login')


#=================================== EDIT ADDRESSES ===================================#
@never_cache
def delete_address(request, pk):
    if request.user.is_authenticated:
        try:
            address = Address.objects.get(id=pk)
            new_default = Address.objects.all().order_by('id').first()
            new_default.is_default = True
            new_default.save()
            address.delete()
            return redirect('h:profile')
        except:
            return redirect('h:home')
    return redirect('r:login')


#=================================== ORDER SUCCESS ===================================#
@never_cache
@csrf_exempt
def success_order(request):
    return render(request, 'order_success.html')


#=================================== ORDER ITEM CANCELL ===================================#
@never_cache
def cancel_order_item(request, item_id, order_id):
    if request.user.is_authenticated:
        try:
            order = Orders.objects.get(id=order_id)
            temp_order_total_amount = order.total_amount
            item = OrderItem.objects.get(id=item_id)
            item.is_listed = False
            product = item.item
            product.stock += item.quantity
            product.save()
            item.save()
            reason = request.POST.get('reason')
            CancelReason.objects.create(
                product=item.item,
                reason=reason
            )
            temp_order_status = order.order_status.status
            if not order.order_items.filter(is_listed=True):
                order.order_status = OrderStatus.objects.get(status='cancelled')
                order.save()
                if not (order.payment_mode.mode == 'COD' and temp_order_status != 'delivered'):
                    wallet = None
                    try:
                        wallet = request.user.wallet
                    except:
                        wallet = Wallet.objects.create(user=request.user, balance=0)
                    
                    wallet.balance += temp_order_total_amount 
                    wallet.save()
                    WalletHistory.objects.create(
                        wallet=wallet,
                        amount=temp_order_total_amount, 
                        payment_mode=order.payment_mode.mode,
                    )
                order.save()
            return redirect('h:order_details', pk=order_id)
        except:
                return redirect('h:orders')

    return redirect('r:login')
    

#=================================== WALLET ===================================#
def wallet(request):
    if request.user.is_authenticated:
        return render (request, 'wallet.html', {'avoid': True})
    return redirect('r:login')


#=================================== APPLY REFERRAL ===================================#
def apply_referral(request):
    if request.user.is_authenticated:
        if request.method == 'POST': 
            code = request.POST.get('referral_code')
            try:
                user_profile = request.user.profile
            except:
                messages.success(request, 'please creaet a profile!')
                return redirect('h:wallet')
            
            if referral_code.objects.filter(code=code).exclude(user=request.user):
                # wallet of current user
                wallet = None
                try:
                    wallet = request.user.wallet
                except:
                    wallet = Wallet.objects.create(user=request.user, balance=0)
                
                wallet.balance += 100
                wallet.save()
                WalletHistory.objects.create(
                    wallet=wallet,
                    amount=100,
                    payment_mode='referral',
                )
                reffer_obj = referral_code.objects.get(code=code)
                request.user.profile.referred_code = reffer_obj
                request.user.profile.save()

                # wallet other
                wallet = None
                try:
                    wallet = reffer_obj.user.wallet
                except:
                    wallet = Wallet.objects.create(user=reffer_obj.user, balance=0)
                
                wallet.balance += 100
                wallet.save()
                WalletHistory.objects.create(
                    wallet=wallet,
                    amount=100,
                    payment_mode='referral',
                )

                print('comes here')
                return redirect('h:wallet')
            else:
                messages.success(request, 'invalid referral code')
                return redirect('h:wallet')

        return redirect('h:wallet')
    return redirect('r:login')


#=================================== INVOICE DOWNLOAD ===================================#
def download_invoice(request, pk):
    if request.user.is_authenticated:
        try:
            order = Orders.objects.get(id=pk)
        except Orders.DoesNotExist:
            return redirect('r:login')

        total_before_discount = order.total_amount

        order_data = {
            'order_id': order.order_id,
            'customer_name': request.user.username,
            'date': order.date.date(),
            'items': [
                {'product': item.item.product_name, 'quantity': item.quantity, 'price': item.item.price} for
                item in order.order_items.all()
            ],
            'total_before_discount': total_before_discount,
            'address': order.address,
            'payment_method': order.payment_mode,
        }

        buffer = BytesIO()
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="invoice.pdf"'

        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=10, leftMargin=10)
        styles = getSampleStyleSheet()

        heading_style = ParagraphStyle(
            'Heading1',
            parent=styles['Heading1'],
            spaceBefore=12,
            fontSize=20,
            textColor=colors.darkblue,
            alignment=1,
        )
        heading = Paragraph("Invoice", heading_style)

        # Add Payment Method and Address
        payment_address_style = ParagraphStyle(
            'PaymentAddressStyle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.black,
            alignment=1,
            spaceAfter=10,
        )
        payment_address = Paragraph(f"Payment Method: {order_data['payment_method']}<br/>Address: {order_data['address']}",
                                    payment_address_style)

        # Create a paragraph for Order Details
        order_details_paragraph_style = ParagraphStyle(
            'OrderDetailsParagraphStyle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.black,
            alignment=1,
            spaceAfter=10,
        )
        order_details_paragraph = Paragraph(
            f"Order Number: {order_data['order_id']}<br/>Customer Name: {order_data['customer_name']}<br/>Date: {order_data['date']}",
            order_details_paragraph_style
        )

        order_table_details = [
            ["Order Details"],
            [order_details_paragraph],
        ]

        order_table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.darkblue),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.darkblue),
            ('BOX', (0, 0), (-1, -1), 1, colors.darkblue),
        ])
        order_table = Table(order_table_details, style=order_table_style, colWidths=[6 * inch])

        items_data = [
            ["Product", "Quantity", "Price", "Total"],
        ] + [
            [item['product'], f"Qty: {item['quantity']}", f"Price: ${item['price']}",
             f"Total: ${item['quantity'] * item['price']}"]
            for item in order_data['items']
        ]

        items_table_style = TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.darkblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.darkblue),
            ('BOX', (0, 0), (-1, -1), 1, colors.darkblue),
        ])
        items_table = Table(items_data, style=items_table_style, colWidths=[2.5 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch])

        adjusted_total_style = ParagraphStyle(
            'AdjustedTotalStyle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.black,
            alignment=1,
            spaceBefore=10,
        )
        adjusted_total_paragraph = Paragraph(
            f"Total Amount: ${total_before_discount} /-",
            adjusted_total_style)

        doc.build([heading, payment_address, order_table, items_table, adjusted_total_paragraph])

        buffer.seek(0)
        response.write(buffer.read())

        return response
    else:
        return redirect('r:login')

#=================================== PRODUCT SEARCH ===================================#
def search_product(request):
    if request.user.is_authenticated:
        products = Products.objects.filter(is_listed=True).order_by('-id').filter(brand__is_listed=True).filter(category__is_listed=True)
        q = request.GET.get('search_query')
        products = products.filter(product_name__icontains=q)
        print(bool(products))
        if bool(products) == False:
            products = Products.objects.filter(is_listed=True).filter(category__category_name__icontains=q).order_by('-id').filter(brand__is_listed=True).filter(category__is_listed=True)
            print(products)
        paginator = Paginator(products, 3)
        page = request.GET.get('page', 1)

        try:
            venues = paginator.page(page)
        except :
            raise Http404("Page not found")

        context = {
            'products': venues,
            'venues': venues,
            'categories': Categories.objects.all().filter(is_listed=True),
            'brands': Brand.objects.all().filter(is_listed=True),
        }
        return render(request, 'shop.html', context)
    return redirect('r:login')


#=================================== FILTER PARALLEL ===================================#
def filter_parallel(request):
    if request.user.is_authenticated:
        category = request.GET.get('category')
        brand = request.GET.get('brand')
        if bool(brand) == False:
            brand = ''
        if bool(category) == False:
            category = ''

        products = Products.objects.filter(is_listed=True).order_by('-id')
        products = products.filter(Q(category__category_name__icontains=category) & Q(brand__name__icontains=brand) ) 
        paginator = Paginator(products, 3)
        page = request.GET.get('page', 1)

        try:
            venues = paginator.page(page)
        except :
            raise Http404("Page not found")

        context = {
            'products': venues,
            'venues': venues,
            'categories': Categories.objects.all().filter(is_listed=True),
            'brands': Brand.objects.all().filter(is_listed=True),
        }
        return render(request, 'shop.html', context)
    return redirect('r:login')