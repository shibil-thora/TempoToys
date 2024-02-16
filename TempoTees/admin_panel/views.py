from django.shortcuts import render, redirect
from register.models import TempoUser as User
from .models import Products, Brand, Categories, ProductImages, Variants, Gender
from .models import Coupon, ProductOffer, CategoryOffer
from home.models import Orders, OrderStatus
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.db.models.functions import Upper
from django.db.models import Q, Sum
from home.models import Orders
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from django.utils import timezone
from django.http import FileResponse, HttpResponse
import io
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from xlsxwriter.workbook import Workbook
from datetime import datetime, timedelta
from .forms import CouponForm, ProductOfferForm, CategoryOfferForm
from django.db.models.functions import ExtractDay, ExtractWeek
from home.models import Orders
from home.models import PaymentModes
from .models import Wallet, WalletHistory
from matplotlib.ticker import MaxNLocator

#=================================== DASH BOARD VIEW ===================================#
@never_cache
def admin_dash(request):
    if request.user.is_superuser:
        try:
            # Daily Sales Data
            daily_data = Orders.objects.filter(order_status__status='delivered').values(day=ExtractDay('date')).annotate(total_sale=Sum('total_amount'))
            daily_days = [int(entry['day']) for entry in daily_data]
            daily_sales = [entry['total_sale'] for entry in daily_data]

            fig, ax = plt.subplots(figsize=(10, 6))  # Adjust the figure size as needed
            ax.plot(daily_days, daily_sales, label='Daily Sales', marker='o', color='red', linestyle='-', linewidth=2)
            ax.set_xlabel('Day')
            ax.set_ylabel('Sale Amount')
            ax.set_title('Daily Sales Report')
            ax.legend()
            
            # Set x-axis ticks to display integers without decimals
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))

            # Add grid lines for better readability
            ax.grid(True, linestyle='--', alpha=0.7)

            # Add labels to data points for better clarity
            for i, txt in enumerate(daily_sales):
                ax.annotate(f'{txt:.2f}', (daily_days[i], daily_sales[i]), textcoords="offset points", xytext=(0, 5), ha='center')

            buffer = BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            daily_graph = base64.b64encode(buffer.read()).decode('utf-8')
            plt.clf()

            return render(request, 'admin_panel.html', {'daily_graph': daily_graph, 'orders': Orders.objects.filter(order_status=OrderStatus.objects.get(status='delivered'))})
        except:
            return redirect('r:login')

    return redirect('r:login')
#=================================== PDF RESPONSE ===================================#
@never_cache
def load_file(request):
    if request.user.is_superuser:
        if request.GET.get('file') == 'pdf':
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
            end_date = end_date + timedelta(days=1)

            buf = BytesIO()
            doc = SimpleDocTemplate(buf, pagesize=letter)

            styles = getSampleStyleSheet()
            heading_text = "<b>SALES REPORT</b>"
            heading_style = ParagraphStyle('Heading1', parent=styles['Heading1'], alignment=1)
            heading = Paragraph(heading_text, heading_style)
            

            table_data = [['Order ID', 'Total Amount', 'Date', 'User']]

            qs = Orders.objects.all().filter(order_status=OrderStatus.objects.get(status='delivered')).filter(date__gte=start_date, date__lte=end_date)
            for data in qs:
                o_id = data.order_id
                if data.order_id[0] == 'o':
                    o_id = data.order_id[6:]
                table_data.append([o_id, data.total_amount, data.date.date(), data.user.username])

            total_amount = qs.aggregate(total=Sum('total_amount'))['total']
            table_data.append(['', '', '', ''])
            table_data.append([Paragraph('<b>TOTAL AMOUNT</b>: ', styles['Normal']), str(total_amount)+' INR', '', ''])

            column_widths = [100, 200, 150, 120, 180]

            table = Table(table_data, colWidths=column_widths)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.black),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightcyan),
            ]))

        
            doc.build([heading, table])
            buf.seek(0)

            return FileResponse(buf, as_attachment=True, filename='sales_report.pdf')
        
        elif request.GET['file'] == 'excel':
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
            end_date = end_date + timedelta(days=1)
            buf = BytesIO()
            workbook = Workbook(buf, {'in_memory': True})
            worksheet = workbook.add_worksheet()

            styles = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1})
            normal_style = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1})

            worksheet.merge_range('A1:D1', 'SALES REPORT', styles)

            data = [['Order ID', 'Total Amount', 'Date', 'User']]

            qs = Orders.objects.all().filter(order_status=OrderStatus.objects.get(status='delivered')).filter(date__gte=start_date, date__lte=end_date)
            for order in qs:
                o_id = order.order_id if order.order_id[0] != 'o' else order.order_id[6:]
                data.append([o_id, order.total_amount, str(order.date.date()), order.user.username])

            total_amount = qs.aggregate(total=Sum('total_amount'))['total']
            data.append(['', '', '', ''])
            data.append(['TOTAL AMOUNT: ', total_amount, '', ''])

            for row_num, row_data in enumerate(data):
                for col_num, cell_data in enumerate(row_data):
                    worksheet.write(row_num + 1, col_num, cell_data, styles if row_num == 0 else normal_style)

            workbook.close()
            buf.seek(0)

            response = HttpResponse(buf, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename=sales_report.xlsx'
            return response

    return redirect('r:login')


#=================================== USER TABLE ===================================#
@never_cache
def users(request):
    if request.user.is_superuser:
        context = {
            'users': User.objects.all().exclude(is_superuser=True).order_by('-id')
        }
        return render(request, 'users.html', context)
    return redirect('r:login')


#=================================== COUPON TABLE ===================================#
@never_cache
def coupons(request):
    if request.user.is_superuser:
        context = {
            'coupons': Coupon.objects.all().order_by('-id')
        }
        return render(request, 'coupons.html', context)
    return redirect('r:login')



#=================================== BLOCK USER ===================================#
@never_cache
def block(request, pk):
    if request.user.is_superuser:
        try:
            user = User.objects.get(id=pk)
            user.is_active = False
            user.save()
            return redirect('a:users')
        except:
            return redirect('a:users')
    return redirect('r:login')


#=================================== ACTIVATE USER ===================================#
@never_cache
def activate(request, pk):
    if request.user.is_superuser:
        try:
            user = User.objects.get(id=pk)
            user.is_active = True
            user.save()
            return redirect('a:users')
        except:
            return redirect('a:users')
    return redirect('r:login')


#=================================== PRODUCTS TABLE ===================================#
@never_cache
def products(request):
    if request.user.is_superuser:
        context = {
            'products': Products.objects.all().order_by('-id')
        }
        return render(request, 'products.html', context)
    return redirect('r:login')


#=================================== CATEGORIES TABLE ===================================#
@never_cache
def categories(request):
    if request.user.is_superuser:
        context = {
            'categories': Categories.objects.filter(is_listed=True).order_by('-id')
        }
        return render(request, 'categories.html', context)
    return redirect('r:login')


#=================================== ADD CATEGORY ===================================#
@never_cache
def add_category(request):
    if request.user.is_superuser:
        if request.method == 'POST':
            try:
                category_name = request.POST.get('category_name')
                Categories.objects.create(category_name=category_name)
                return redirect('a:categories')
            except:
                return redirect('a:categories')
        return render(request, 'add_category.html')
    return redirect('r:login')


#=================================== Edit CATEGORY ===================================#
@never_cache
def edit_category(request, pk):
    if request.user.is_superuser:
        category = Categories.objects.get(id=pk)
        if request.method == 'POST':
            try:
                category_name = request.POST.get('category_name')
                category = Categories.objects.get(id=pk)
                category.category_name = category_name
                category.save()
                return redirect('a:categories')
            except:
                return redirect('a:categories')
        context = {
            'category': category
        }
        return render(request, 'edit_category.html', context)
    return redirect('r:login')


#=================================== DELETE CATEGORY ===================================#
@never_cache
def delete_category(request, pk):
    if request.user.is_superuser:
        try:
            category = Categories.objects.get(id=pk)
            category.is_listed = False
            category.save()
            return redirect('a:categories')

        except:
            messages.success(request, 'category is assosiated with products cannot delete')
            return redirect('a:categories')
    return redirect('r:login')


#=================================== ADD PRODUCTS ===================================#
@never_cache
def add_product(request):
    if request.user.is_superuser:
        if request.method == 'POST':
            try:
                product_name = request.POST.get('product_name')
                product_name = product_name.strip()
                brand = request.POST.get('brand')
                category = request.POST.get('category')
                stock = request.POST.get('stock')
                description = request.POST.get('description')
                description_detailed = request.POST.get('description_detailed')
                price = request.POST.get('price')
                image_set = request.FILES.getlist('image_set')
                brand_obj = Brand.objects.get(name=brand)
                category_obj = Categories.objects.get(category_name=category)
                error_occured = False
                if len(product_name) < 3:
                    error_occured = True
                    context = {
                    'brands': Brand.objects.all().filter(is_listed=True),
                    'categories': Categories.objects.all().filter(is_listed=True),
                    'genders': Gender.objects.all(),
                    'error': 'product name should be atleast 3 charactors!',
                    }
                    return render(request, 'add_product.html', context)

                if not error_occured:
                    product = Products.objects.create(product_name=product_name, product_desc=description, brand=brand_obj, stock=stock, category=category_obj, price=price, product_desc_detailed=description_detailed)
                    product.save()


                for img in image_set:
                    new_img = ProductImages(image=img, product=product)
                    new_img.save()
                return redirect('a:products')
            except:
                messages.success(request, 'something went wrong! you may not have entered all data')
                return redirect('a:products')
        
        context = {
            'brands': Brand.objects.all().filter(is_listed=True),
            'categories': Categories.objects.all().filter(is_listed=True),
            'genders': Gender.objects.all(),
        }

        return render(request, 'add_product.html', context)
    return redirect('r:login')


#=================================== UNLIST PRODUCT ===================================#
@never_cache
def unlist(request, pk):
    if request.user.is_superuser:
        try:
            product = Products.objects.get(id=pk)
            product.is_listed = False
            product.save()
            return redirect('a:products')
        except:
            return redirect('a:products')
    return redirect('r:login')


#=================================== LIST PRODUCT ===================================#
@never_cache
def list(request, pk):
    if request.user.is_superuser:
        try:
            product = Products.objects.get(id=pk)
            product.is_listed = True
            product.save()
            return redirect('a:products')
        except:
            return redirect('a:products')
    return redirect('r:login')


#=================================== EDIT PRODUCT ===================================#
@never_cache
def edit_product(request, pk):
    if request.user.is_superuser:
        product = Products.objects.get(id=pk)

        
        if request.method == 'POST':
            try:
                product_name = request.POST.get('product_name')
                product_name = product_name.strip()
                brand = request.POST.get('brand')
                category = request.POST.get('category')
                stock = request.POST.get('stock')
                description = request.POST.get('description')
                description_detailed = request.POST.get('description_detailed')
                price = request.POST.get('price')

                brand_obj = Brand.objects.get(name=brand)
                category_obj = Categories.objects.get(category_name=category)
                 

                product.product_name = product_name
                product.brand = brand_obj
                product.category = category_obj
                product.stock = stock
                product.product_desc = description
                product.product_desc_detailed = description_detailed
                product.price = price
                

                if len(product_name) < 3:
                    context = {
                    'brands': Brand.objects.all().filter(is_listed=True),
                    'categories': Categories.objects.all().filter(is_listed=True),
                    'genders': Gender.objects.all(),
                    'error': 'invalid entry!',
                    }
                    messages.success(request, 'something went wrong! you may not have entered all data')
                    return render(request, 'add_product.html', context)
                
                product.save()
             
                image_set = request.FILES.getlist('image_set')
                for img in image_set:
                    new_img = ProductImages(image=img, product=product)
                    new_img.save()
                return redirect('a:products')
            except:
                return redirect('a:products')
                
        
        context = {
            'product': product,
            'id': pk,
            'brands': Brand.objects.all().filter(is_listed=True),
            'categories': Categories.objects.all().filter(is_listed=True),
            'genders': Gender.objects.all(),
        }
        return render(request, 'edit_product.html', context)
    

    return redirect('r:login')


#=================================== DELETE ALL IMAGES ===================================#
@never_cache
def delete_images(request, pk, p_id):
    if request.user.is_superuser:
        try:
            image = ProductImages.objects.get(id=pk)
            image.delete()
            return redirect('a:edit_product', pk=p_id)
        except:
            return redirect('a:edit_product', pk=p_id)
    
    return redirect('r:login')


#=================================== BRANDS TABLE ===================================#
@never_cache
def brands(request):
    if request.user.is_superuser:
        context = {
            'brands': Brand.objects.filter(is_listed=True).order_by('-id')
        }
        return render(request, 'brands.html', context)
    return redirect('r:login')


#=================================== ADD BRAND ===================================#
@never_cache
def add_brand(request):
    if request.user.is_superuser:
        if request.method == 'POST':
            try:
                brand_name = request.POST.get('brand_name')
                brand_name = brand_name.strip()
                
                if len(brand_name) < 2:
                    return render(request, 'add_brand.html', {'error': 'invalid entry!'})

                Brand.objects.create(name=brand_name)
                return redirect('a:brands')
            except:
                return redirect('a:brands')
        return render(request, 'add_brand.html')
    return redirect('r:login')


#=================================== Edit BRAND ===================================#
@never_cache
def edit_brand(request, pk):
    if request.user.is_superuser:
        brand = Brand.objects.get(id=pk)
        if request.method == 'POST':
            try:
                brand_name = request.POST.get('brand_name')
                brand_name = brand_name.strip()

                if len(brand_name) < 2:
                    return render(request, 'edit_brand.html', {'error': 'invalid entry!', 'brand': brand})
                
                brand = Brand.objects.get(id=pk)
                brand.name = brand_name
                brand.save()
                return redirect('a:brands')
            except:
                return redirect('a:brands')
        context = {
            'brand': brand
        }
        return render(request, 'edit_brand.html', context)
    return redirect('r:login')


#=================================== DELETE BRAND ===================================#
@never_cache
def delete_brand(request, pk):
    if request.user.is_superuser:
        try:
            brand = Brand.objects.get(id=pk)
            brand.is_listed = False
            brand.save()
            return redirect('a:brands')

        except:
            messages.success(request, 'brand is assosiated with products cannot delete')
            return redirect('a:brands')
    return redirect('r:login')


#=================================== ADMIN ORDERS ===================================#
@never_cache
def admin_orders(request):
    if request.user.is_superuser:
        context = {
            'orders': Orders.objects.all().order_by('-id')
        }
        return render(request, 'admin_orders.html', context)
    return redirect('r:login')


#=================================== ADMIN ORDERS DEAILED ===================================#
@never_cache
def admin_order_details(request, pk):
    if request.user.is_superuser:
        order = Orders.objects.get(id=pk)
        context = {
            'order': order,
            'address': order.address,
        }
        return render(request, 'admin_order_details.html', context)
    return redirect('r:login')


#=================================== CHANGE TO  DELIVERED ===================================#
@never_cache
def change_to_delivered(request, pk):
    if request.user.is_superuser:
        try:
            order = Orders.objects.get(id=pk)
            if order.order_status == OrderStatus.objects.get(status='pending') or order.order_status == OrderStatus.objects.get(status='out for delivery') or order.order_status == OrderStatus.objects.get(status='dispatched') :
                order.order_status = OrderStatus.objects.get(status='delivered')
                order.save()
            return redirect('a:admin_orders')
        except:
            return redirect('a:admin_orders')
    return redirect('r:login')


#=================================== CHANGE TO  DISPATCHED ===================================#
@never_cache
def change_to_dispatched(request, pk):
    if request.user.is_superuser:
        try:
            order = Orders.objects.get(id=pk)
            if order.order_status == OrderStatus.objects.get(status='pending') or order.order_status == OrderStatus.objects.get(status='out for delivery') or order.order_status == OrderStatus.objects.get(status='dispatched') :
                order.order_status = OrderStatus.objects.get(status='dispatched')
                order.save()
            return redirect('a:admin_orders')
        except:
            return redirect('a:admin_orders')
    return redirect('r:login')


#=================================== CHANGE TO  OUT fOR DELIVERY ===================================#
@never_cache
def change_to_out(request, pk):
    if request.user.is_superuser:
        try:
            order = Orders.objects.get(id=pk)
            if order.order_status == OrderStatus.objects.get(status='pending') or order.order_status == OrderStatus.objects.get(status='out for delivery') or order.order_status == OrderStatus.objects.get(status='dispatched') :
                order.order_status = OrderStatus.objects.get(status='out for delivery')
                order.save()
            return redirect('a:admin_orders')
        except:
            return redirect('a:admin_orders')
    return redirect('r:login')


#=================================== CANCEL ORDER  ===================================#
@never_cache
def cancel_order(request, pk):
    if request.user.is_superuser:
        try:
            order = Orders.objects.get(id=pk)
            temp_order_status = order.order_status.status
            if not (order.payment_mode.mode == 'COD' and temp_order_status != 'delivered'):
                wallet = None
                try:
                    wallet = order.user.wallet
                except:
                    wallet = Wallet.objects.create(user=order.user, balance=0)
                
                wallet.balance += order.total_amount
                wallet.save()
                WalletHistory.objects.create(
                    wallet=wallet,
                    amount=order.total_amount,
                    payment_mode=order.payment_mode.mode,
                )
                order.save()

            order.order_status = OrderStatus.objects.get(status='cancelled')
            order.save()
            for item in order.order_items.all():
                product = item.item
                product.stock += item.quantity
                product.save()
            return redirect('a:admin_orders')
        except:
            return redirect('a:admin_orders')
    return redirect('r:login')


#=================================== ADD COUPON  ===================================#
@never_cache
def add_coupon(request):
    if request.user.is_superuser:
        if request.method == 'POST':
            coupon_code = request.POST.get('coupon_code')
            discount_price = request.POST.get('discount_price')
            days_valid = request.POST.get('days_valid')
            promoter = request.POST.get('promoter')

            if len(coupon_code) < 4: 
                messages.success(request, 'coupon code should be 4 charecters')
                return redirect('a:add_coupon')
            
            if len(promoter.strip()) < 3: 
                messages.success(request, 'promoter name should be 3 charecters')
                return redirect('a:add_coupon')
            
            if int(discount_price) < 0: 
                messages.success(request, 'discount price should be a positive number')
                return redirect('a:add_coupon')
            
            
            if int(days_valid) < 0: 
                messages.success(request, 'days should be a positive number')
                return redirect('a:add_coupon')
            
            Coupon.objects.create(
                coupon_code=coupon_code,
                discount_price=discount_price,
                days_valid=days_valid,
                promoter=promoter
            )
            return redirect('a:coupons')
        context = {
            'form': CouponForm(),
        }
        return render(request, 'add_coupon.html', context)
    return redirect('r:login')


#=================================== EDIT COUPON  ===================================#
@never_cache
def edit_coupon(request, pk):
    if request.user.is_superuser:
        coupon = Coupon.objects.get(id=pk)
        if request.method == 'POST':
            form = CouponForm(request.POST, instance=coupon)
            if form.is_valid():
                form.save()
                return redirect('a:coupons')
        context = {
            'form': CouponForm(instance=coupon),
            'id': pk,
        }
        return render(request, 'edit_coupon.html', context)
    return redirect('r:login')


#=================================== DELETE COUPON  ===================================#
@never_cache
def delete_coupon(request, pk):
    if request.user.is_superuser:
        try:
            coupon = Coupon.objects.get(id=pk)
            coupon.activated = False
            coupon.save()
            return redirect('a:coupons')
        except:
            return redirect('a:coupons')
    return redirect('r:login')


#=================================== ACTIVATE COUPON  ===================================#
@never_cache
def activate_coupon(request, pk):
    if request.user.is_superuser:
        try:
            coupon = Coupon.objects.get(id=pk)
            coupon.activated = True
            coupon.save()
            return redirect('a:coupons')
        except:
            return redirect('a:coupons')
    return redirect('r:login')


#=================================== OFFERS ===================================#
@never_cache
def offers(request):
    if request.user.is_superuser:
        context = {
            'product_offers': ProductOffer.objects.all().order_by('-id'),
            'category_offers': CategoryOffer.objects.all().order_by('-id'),
        }
        return render (request, 'offers.html', context)
    return redirect('r:login')


#=================================== ADD PRODUCT OFFERS ===================================#
@never_cache
def add_product_offer(request):
    if request.user.is_superuser:
        form = ProductOfferForm(request.POST)
        if request.method == 'POST': 
            product = request.POST.get('product')
            offer_percent = request.POST.get('offer_percent')

            if ProductOffer.objects.filter(product=Products.objects.get(id=product)):
                messages.error(request, f'{Products.objects.get(id=product).product_name} already has an offer!')
                return redirect('a:add_product_offer')
            
            if int(offer_percent) < 0 or int(offer_percent) > 100:
                messages.error(request, 'percent value should be in between 0 and 100')
                return redirect('a:add_product_offer')

            ProductOffer.objects.create(
                product=Products.objects.get(id=product),
                offer_percent=offer_percent
            )
            return redirect('a:offers')
        context = {
            'form': ProductOfferForm()
        }
        return render(request, 'add_offer_product.html', context)
    return redirect('r:login')


#=================================== ADD CATEGORY OFFERS ===================================#
@never_cache
def add_category_offer(request):
    if request.user.is_superuser:
        form = CategoryOfferForm(request.POST)
        if request.method == 'POST': 
            category = request.POST.get('category')
            offer_percent = request.POST.get('offer_percent')

            if CategoryOffer.objects.filter(category=Categories.objects.get(id=category)):
                messages.error(request, f'{Categories.objects.get(id=category).category_name} already has an offer!')
                return redirect('a:add_category_offer')
            
            if int(offer_percent) < 0 or int(offer_percent) > 100:
                messages.error(request, 'percent value should be in between 0 and 100')
                return redirect('a:add_category_offer')

            CategoryOffer.objects.create(
                category=Categories.objects.get(id=category),
                offer_percent=offer_percent
            )
            return redirect('a:offers')
        context = {
            'form': CategoryOfferForm()
        }
        return render(request, 'add_offer_category.html', context)
    return redirect('r:login')


#=================================== DELETE OFFERS PRODUCT ===================================#
def delete_product_offer(request, pk):
    if request.user.is_superuser:
        try:
            offer = ProductOffer.objects.get(id=pk)
            offer.delete()
            return redirect('a:offers')
        except:
            return redirect('a:offers')
    return redirect('r:login')


#=================================== DELETE OFFERS CATEGORY ===================================#
def delete_category_offer(request, pk):
    if request.user.is_superuser:
        try:
            category = CategoryOffer.objects.get(id=pk)
            category.delete()
            return redirect('a:offers')
        except:
            return redirect('a:offers')
    return redirect('r:login')


#=================================== EDIT OFFERS PRODUCT ===================================#
def edit_product_offer(request, pk):
    if request.user.is_superuser:
        offer = ProductOffer.objects.get(id=pk)
        if request.method == 'POST': 
            discount_rate = request.POST.get('offer_percent')
            if int(discount_rate) < 0 or int(discount_rate) > 100:
                messages.error(request, 'percent value should be in between 0 and 100')
                return redirect('a:edit_product_offer', pk=offer.id)
            offer.offer_percent = int(discount_rate)
            offer.save()
            return redirect('a:offers')
        context = {
            'form': ProductOfferForm(instance=offer),
            'offer': offer
        }
        return render(request, 'edit_product_offer.html', context)
    return redirect('r:login')


#=================================== EDIT OFFERS CATEGORY ===================================#
def edit_category_offer(request, pk):
    if request.user.is_superuser:
        offer = CategoryOffer.objects.get(id=pk)
        if request.method == 'POST': 
            discount_rate = request.POST.get('offer_percent')
            if int(discount_rate) < 0 or int(discount_rate) > 100:
                messages.error(request, 'percent value should be in between 0 and 100')
                return redirect('a:edit_category_offer', pk=offer.id)
            offer.offer_percent = int(discount_rate)
            offer.save()
            return redirect('a:offers')
        context = {
            'form': CategoryOfferForm(instance=offer),
            'offer': offer
        }
        return render(request, 'edit_category_offer.html', context)
    return redirect('r:login')







 