from .import views
from django.shortcuts import render, redirect, get_object_or_404, resolve_url
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, ListView, View, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy, reverse
from django.views import generic
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from .models import User, Product, Stock, Supplier, ProductSupplier, OrderItem, Order
from django.utils.decorators import method_decorator
from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView, LoginView
from django.core.paginator import Paginator
from .forms import ProductForm, StockForm, OrderItemForm, UserUpdateForm
from django.contrib.auth import authenticate, login, get_user_model
from django.views.generic.edit import FormView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from .forms import UserRegistrationForm, SupplierForm, ProductSupplierForm
from decimal import Decimal
from django.utils.timezone import now
from django.utils import timezone
from datetime import timedelta, datetime, date
from django.db.models import Sum
from django.db.models.functions import TruncMonth, Now, Cast, TruncDay
from django.db.models import F, ExpressionWrapper, fields, DateField, DurationField
from django.db.models import Q
from django.template.loader import get_template
from xhtml2pdf import pisa
import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import InvalidPage

class IndexView(TemplateView):
    template_name = 'registration/login_form.html' 

class CustomLoginView(LoginView):
    template_name = 'registration/login_form.html'  
    success_url = reverse_lazy('dashboardpage') 

class SignUpView(LoginRequiredMixin, CreateView):
    template_name = 'registration/signup.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, "User created successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        errors = form.errors.as_data()

        if 'username' in errors:
            messages.error(self.request, "Username already exists.")

        if 'email' in errors:
            messages.error(self.request, "Email already exists.")

        # Check for password mismatch, often field named 'password2' or 'password_confirmation'
        if 'password2' in errors or 'password1' in errors:
            messages.error(self.request, "Passwords do not match.")

        if not ('username' in errors or 'email' in errors or 'password2' in errors or 'password1' in errors):
            messages.error(self.request, "Please fix the errors below.")

        self.request.session['form_errors'] = form.errors
        return redirect(self.request.path)

    

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'registration/edit_profile.html'
    success_url = reverse_lazy('edit_profile')

    def get_object(self, queryset=None):
        return self.request.user

class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = 'registration/change_password.html'
    success_url = reverse_lazy('profile_edit')  # Redirect to edit profile after success


class AdminView(LoginRequiredMixin, TemplateView):
    template_name = 'adminbar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        search_query = self.request.GET.get('search', '')
        context['search_query'] = search_query

        if search_query:
            products = Product.objects.filter(
                Q(product_name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(category__icontains=search_query)
            )
            context['results'] = products
        else:
            context['results'] = None

         # Expiring products notifications
        today = timezone.now().date()
        thirty_days_later = today + timedelta(days=30)
        
        expiring_products = ProductSupplier.objects.filter(
            expiry_date__gte=today,
            expiry_date__lte=thirty_days_later
        ).select_related('product').order_by('expiry_date')[:5]
        
        for product in expiring_products:
            product.days_remaining = (product.expiry_date - today).days
        
        context['expiring_products'] = expiring_products
        context['expiring_count'] = expiring_products.count()

        # Low stock alerts
        low_stock_items = Stock.objects.select_related('product').filter(
            quantity__lt=10
        ).order_by('quantity')[:5]
        
        context['low_stock_items'] = low_stock_items
        context['low_stock_count'] = low_stock_items.count()

        # Total notifications count (make sure this is calculated)
        context['total_notifications'] = context['expiring_count'] + context['low_stock_count']
        return context

class DashboardView(LoginRequiredMixin, View):
    def get(self, request):

        
        total_products = Product.objects.count()
        total_sales = OrderItem.objects.aggregate(total=Sum('subtotal'))['total'] or 0
        total_suppliers = Supplier.objects.count()
        total_stock = Stock.objects.aggregate(total_stock=Sum('quantity'))['total_stock'] or 0

        now = timezone.now()

        # Stock percentage change (weekly-based for now)
        start_of_this_week = now - timedelta(days=now.weekday())  # Monday this week
        start_of_last_week = start_of_this_week - timedelta(days=7)
        end_of_last_week = start_of_this_week - timedelta(seconds=1)

        this_week_stock = Stock.objects.filter(updated_at__gte=start_of_this_week).aggregate(total_stock=Sum('quantity'))['total_stock'] or 0
        last_week_stock = Stock.objects.filter(updated_at__range=(start_of_last_week, end_of_last_week)).aggregate(total_stock=Sum('quantity'))['total_stock'] or 0

        if last_week_stock == 0:
            stock_percentage_change = 100 if this_week_stock > 0 else 0
        else:
            stock_percentage_change = ((this_week_stock - last_week_stock) / last_week_stock) * 100

        # Most sold and slow sold items this month
        start_of_month = now.replace(day=1)
        most_sold_month = OrderItem.objects.filter(order_date__gte=start_of_month) \
            .values('product__product_name') \
            .annotate(total_sold=Sum('quantity')) \
            .order_by('-total_sold')[:5]

        slow_sold_month = OrderItem.objects.filter(order_date__gte=start_of_month) \
            .values('product__product_name') \
            .annotate(total_sold=Sum('quantity')) \
            .order_by('total_sold')[:5]
        

            # Get today's date
        today = date.today()

        # Calculate start and end of this week (Monday to Sunday)
        start_of_this_week = today - timedelta(days=today.weekday())  # Monday
        end_of_this_week = start_of_this_week + timedelta(days=6)     # Sunday

        # Calculate start and end of last week
        start_of_last_week = start_of_this_week - timedelta(days=7)
        end_of_last_week = start_of_this_week - timedelta(days=1)

        # Get total sales for this week
        total_sales_this_week = OrderItem.objects.filter(
            order_date__date__range=(start_of_this_week, end_of_this_week)
        ).aggregate(total=Sum('subtotal'))['total'] or 0

        # Get total sales for last week
        total_sales_last_week = OrderItem.objects.filter(
            order_date__date__range=(start_of_last_week, end_of_last_week)
        ).aggregate(total=Sum('subtotal'))['total'] or 0

        # Calculate percentage change
        if total_sales_last_week == 0:
            weekly_sales_percentage_change = 100 if total_sales_this_week > 0 else 0
        else:
            weekly_sales_percentage_change = (
                (total_sales_this_week - total_sales_last_week) / total_sales_last_week
            ) * 100

        # Monthly sales logic
        start_of_this_month = now.replace(day=1)
        start_of_last_month = (start_of_this_month - timedelta(days=1)).replace(day=1)
        end_of_last_month = start_of_this_month - timedelta(seconds=1)

        total_sales_this_month = OrderItem.objects.filter(
            order_date__gte=start_of_this_month
        ).aggregate(total=Sum('subtotal'))['total'] or 0

        total_sales_last_month = OrderItem.objects.filter(
            order_date__range=(start_of_last_month, end_of_last_month)
        ).aggregate(total=Sum('subtotal'))['total'] or 0

        # Fix percentage calculation
        if total_sales_last_month == 0:
            if total_sales_this_month == 0:
                monthly_sales_percentage_change = 0
            else:
                monthly_sales_percentage_change = 100  # From 0 to something = full gain
        else:
            monthly_sales_percentage_change = ((total_sales_this_month - total_sales_last_month) / total_sales_last_month) * 100

                # Yearly Sales
        start_of_this_year = now.replace(month=1, day=1)
        start_of_last_year = (start_of_this_year - timedelta(days=1)).replace(month=1, day=1)
        end_of_last_year = start_of_this_year - timedelta(seconds=1)

        total_sales_this_year = OrderItem.objects.filter(
            order_date__gte=start_of_this_year
        ).aggregate(total=Sum('subtotal'))['total'] or 0

        total_sales_last_year = OrderItem.objects.filter(
            order_date__range=(start_of_last_year, end_of_last_year)
        ).aggregate(total=Sum('subtotal'))['total'] or 0

        if total_sales_last_year == 0:
            if total_sales_this_year == 0:
                yearly_sales_percentage_change = 0
            else:
                yearly_sales_percentage_change = 100
        else:
            yearly_sales_percentage_change = ((total_sales_this_year - total_sales_last_year) / total_sales_last_year) * 100

        # Order count comparison (monthly)
        total_orders_this_month = Order.objects.filter(
            order_date__gte=start_of_this_month
        ).count()

        total_orders_last_month = Order.objects.filter(
            order_date__range=(start_of_last_month, end_of_last_month)
        ).count()

        if total_orders_last_month == 0:
            if total_orders_this_month == 0:
                order_percentage_change = 0
            else:
                order_percentage_change = 100
        else:
            order_percentage_change = (
                (total_orders_this_month - total_orders_last_month) / total_orders_last_month
            ) * 100

        # Expiring products logic
        today = timezone.now().date()
        thirty_days_later = today + timedelta(days=30)
        
        expiring_products = ProductSupplier.objects.filter(
            expiry_date__gte=today,
            expiry_date__lte=thirty_days_later
        ).select_related('product', 'supplier').order_by('expiry_date')[:5]  # Limit to 5 most urgent
        
        # Add days remaining to each product
        for product in expiring_products:
            product.days_remaining = (product.expiry_date - today).days
        
        expiring_count = ProductSupplier.objects.filter(
            expiry_date__gte=today,
            expiry_date__lte=thirty_days_later
        ).count()

        # Low stock alerts calculation (NEW)
        low_stock_threshold = 10
        low_stock_items = Stock.objects.select_related('product')\
        .filter(quantity__lt=low_stock_threshold)\
        .order_by('quantity')[:5]  # Top 5 most critical

        return render(request, 'website/dashboard.html', {
            'total_products': total_products,
            'total_suppliers': total_suppliers,
            'total_stock': total_stock,
            'total_sales': total_sales,
            'stock_percentage_change': round(stock_percentage_change),
            'most_sold_month': most_sold_month,
            'slow_sold_month': slow_sold_month,
            'total_sales_this_month': total_sales_this_month,
            'total_sales_last_month': total_sales_last_month,
            'monthly_sales_percentage_change': round(monthly_sales_percentage_change, 2),
            'total_sales_this_week': total_sales_this_week,
            'total_sales_last_week': total_sales_last_week,
            'weekly_sales_percentage_change': round(weekly_sales_percentage_change, 2),
            'total_sales_this_year': total_sales_this_year,
            'total_sales_last_year': total_sales_last_year,
            'yearly_sales_percentage_change': round(yearly_sales_percentage_change, 2),
            'yearly_sales_percentage_change_abs': round(abs(yearly_sales_percentage_change), 2),
            'total_orders_this_month': total_orders_this_month,
            'total_orders_last_month': total_orders_last_month,
            'order_percentage_change': round(order_percentage_change, 2),
            'expiring_products': expiring_products,
            'expiring_count': expiring_count,
            'low_stock_items': low_stock_items,
            'low_stock_count': Stock.objects.filter(quantity__lt=low_stock_threshold).count(),
            'low_stock_threshold': low_stock_threshold,
        })



class MonthlySalesDataView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        sales_query = OrderItem.objects.all()
        
        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                sales_query = sales_query.filter(
                    order_date__date__gte=start_date,
                    order_date__date__lte=end_date
                )
            except ValueError:
                pass
        
        sales_by_month = (
            sales_query
            .annotate(month=TruncMonth('order_date'))
            .values('month')
            .annotate(total=Sum('subtotal'))
            .order_by('month')
        )
        
        # For single month selection, we'll show daily data
        if start_date_str and end_date_str:
            # Daily breakdown for the selected month
            daily_sales = (
                sales_query
                .annotate(day=TruncDay('order_date'))
                .values('day')
                .annotate(total=Sum('subtotal'))
                .order_by('day')
            )
            
            # Create labels and data for each day in month
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            
            labels = []
            data = []
            current_date = start_date
            
            while current_date <= end_date:
                labels.append(current_date.strftime('%d %b'))
                # Find sales for this day
                day_sale = next(
                    (sale for sale in daily_sales 
                     if sale['day'].date() == current_date.date()),
                    {'total': 0}
                )
                data.append(float(day_sale['total']))
                current_date = current_date + timedelta(days=1)
            
            return JsonResponse({
                'labels': labels,
                'data': data
            })
        
        # Default view (no date filter) - monthly view
        monthly_totals = [0] * 12
        month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        
        for entry in sales_by_month:
            month_index = entry['month'].month - 1
            monthly_totals[month_index] = round(entry['total'], 2)
        
        return JsonResponse({
            'labels': month_labels,
            'data': monthly_totals
        })


class AnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = 'analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get filter parameters from request
        time_range = self.request.GET.get('range', 'month')
        limit = int(self.request.GET.get('limit', 10))
        receipts_range = self.request.GET.get('receipts_range', 'month')
        supplier_id = self.request.GET.get('supplier')
        
        # Set date ranges
        end_date = timezone.now()
        receipts_end_date = timezone.now()  # Define receipts_end_date
        
        if time_range == 'week':
            start_date = end_date - timedelta(days=7)
        elif time_range == 'year':
            start_date = end_date - timedelta(days=365)
        else:  # month
            start_date = end_date - timedelta(days=30)
            
        if receipts_range == 'week':
            receipts_start_date = receipts_end_date - timedelta(days=7)
        elif receipts_range == 'year':
            receipts_start_date = receipts_end_date - timedelta(days=365)
        else:  # month
            receipts_start_date = receipts_end_date - timedelta(days=30)

        # Get top selling products
        top_products_query = OrderItem.objects.filter(
            order_date__range=(start_date, end_date)
        ).values('product__product_id', 'product__product_name').annotate(
            total_quantity=Sum('quantity'),
            total_sales=Sum('subtotal')
        ).order_by('-total_quantity')
        
        top_products = list(top_products_query[:limit])
        
        # Prepare data for chart
        products = [item['product__product_name'] for item in top_products]
        quantities = [item['total_quantity'] for item in top_products]
        sales = [float(item['total_sales']) for item in top_products]
        
        # Get product receipts
        receipts_query = ProductSupplier.objects.filter(
            date_received__range=(receipts_start_date, receipts_end_date)
        )
        
        if supplier_id:
            receipts_query = receipts_query.filter(supplier__supplier_id=supplier_id)
            
        receipts = list(receipts_query.values(
            'product__product_id',
            'product__product_name'
        ).annotate(
            total_received=Sum('quantity_received'),
            total_ordered=Sum('quantity_ordered')
        ).order_by('-total_received')[:10])
        
        # Prepare receipts data
        receipt_products = [item['product__product_name'] for item in receipts]
        received = [item['total_received'] for item in receipts]
        ordered = [item['total_ordered'] for item in receipts]
        
        # Get all suppliers
        suppliers = Supplier.objects.all()
        
        
         # 🔔 Expiring products logic
        today = timezone.now().date()
        thirty_days_later = today + timedelta(days=30)

        expiring_products = ProductSupplier.objects.filter(
            expiry_date__gte=today,
            expiry_date__lte=thirty_days_later
        ).select_related('product', 'supplier').order_by('expiry_date')[:5]

        for product in expiring_products:
            product.days_remaining = (product.expiry_date - today).days

        expiring_count = ProductSupplier.objects.filter(
            expiry_date__gte=today,
            expiry_date__lte=thirty_days_later
        ).count()

        # 📉 Low stock logic
        low_stock_threshold = 20
        low_stock_items = Stock.objects.select_related('product')\
            .filter(quantity__lt=low_stock_threshold)\
            .order_by('quantity')[:5]

        low_stock_count = Stock.objects.filter(quantity__lt=low_stock_threshold).count()

        # Combine all context
        context.update({
            'chart_data': json.dumps({
                'products': products,
                'quantities': quantities,
                'sales': sales,
                'time_range': time_range,
                'limit': limit,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
            }),
            'receipts_chart_data': json.dumps({
                'products': receipt_products,
                'received': received,
                'ordered': ordered,
                'time_range': receipts_range,
                'start_date': receipts_start_date.strftime('%Y-%m-%d'),
                'end_date': receipts_end_date.strftime('%Y-%m-%d')
            }),
            'product_data': zip(products, quantities, sales),
            'product_receipts_data': receipts,
            'suppliers': suppliers,
            'selected_supplier': int(supplier_id) if supplier_id else None,
            'receipts_range': receipts_range,
            # NEW CONTEXT
            'expiring_products': expiring_products,
            'expiring_count': expiring_count,
            'low_stock_items': low_stock_items,
            'low_stock_count': low_stock_count,
            'low_stock_threshold': low_stock_threshold,
        })

        return context

    

class UserListView(LoginRequiredMixin, ListView):
    model = get_user_model()
    template_name = 'user_list.html'
    context_object_name = 'users'
    paginate_by = 5  # Display 5 users per page

    def get_queryset(self):
        queryset = super().get_queryset().filter(is_superuser=False)
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(username__icontains=search_query)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        paginator = context['paginator']
        page_obj = context['page_obj']
        page_number = page_obj.number
        total_pages = paginator.num_pages

        # Generate custom page range with ellipsis logic
        page_range = []

        if total_pages <= 7:
            page_range = list(range(1, total_pages + 1))
        else:
            if page_number <= 4:
                page_range = [1, 2, 3, 4, 5, '...', total_pages]
            elif page_number >= total_pages - 3:
                page_range = [1, '...', total_pages - 4, total_pages - 3, total_pages - 2, total_pages - 1, total_pages]
            else:
                page_range = [1, '...', page_number - 1, page_number, page_number + 1, '...', total_pages]

        context['custom_page_range'] = page_range
        return context

class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'user_update.html'
    fields = ['first_name', 'last_name', 'username', 'email']
    
    def get_object(self):
        user_id = self.kwargs.get('pk')
        return get_object_or_404(User, id=user_id)

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "User updated successfully!")
        return redirect(reverse('user_list'))

    def form_invalid(self, form):
        messages.error(self.request, "There were errors in the form.")
        # Pass the form in context properly
        return self.render_to_response(self.get_context_data(form=form))



class UserDeleteView(LoginRequiredMixin, DeleteView):
    model = User
    success_url = reverse_lazy('user_list')  # redirect to your user list page

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'message': 'User deleted successfully'})
        return super().delete(request, *args, **kwargs)

# Inventory Products 
class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'product_form.html'
    success_url = reverse_lazy('product_list')

    def form_valid(self, form):
        product_name = form.cleaned_data.get('product_name')
        if Product.objects.filter(product_name=product_name).exists():
            messages.error(self.request, "Duplicate product: This product already exists in stock.")
            return self.form_invalid(form)

        product = form.save(commit=False)
        product.created_by = self.request.user
        product.save()
        form.save_m2m()

        messages.success(self.request, "Product added successfully.")
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, "Duplicate product: This product already exists.")
        return self.render_to_response(self.get_context_data(form=form))


class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'product_list.html'
    context_object_name = 'products'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().prefetch_related('suppliers')
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(product_name__icontains=search_query)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paginator = context['paginator']
        page_obj = context['page_obj']
        current_page = page_obj.number
        total_pages = paginator.num_pages

        # Ellipsis logic
        page_range = []
        if total_pages <= 7:
            page_range = range(1, total_pages + 1)
        else:
            if current_page <= 4:
                page_range = [1, 2, 3, 4, 5, '...', total_pages]
            elif current_page >= total_pages - 3:
                page_range = [1, '...', total_pages - 4, total_pages - 3, total_pages - 2, total_pages - 1, total_pages]
            else:
                page_range = [1, '...', current_page - 1, current_page, current_page + 1, '...', total_pages]

        context['custom_page_range'] = page_range
        return context

class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'product_edit_form.html'
    success_url = reverse_lazy('product_list')

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Product updated successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Duplicate product: This product already exists in stock.")
        return self.render_to_response(self.get_context_data(form=form))

class ProductDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        product = get_object_or_404(Product, pk=pk)
        product.delete()
        return JsonResponse({'message': 'Product deleted successfully'})
    

    
class ProductListPDFView(View):
    def get(self, request, *args, **kwargs):
        # Annotate products with total stock
        products = Product.objects.prefetch_related('suppliers').annotate(
            total_stock=Sum('stock__quantity')
        )

        template_path = 'product_list_pdf.html'
        context = {'products': products}
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="product_list.pdf"'
        
        template = get_template(template_path)
        html = template.render(context)

        pisa_status = pisa.CreatePDF(html, dest=response)
        if pisa_status.err:
            return HttpResponse('Error generating PDF', status=500)
        return response


# Stock List

class StockListView(LoginRequiredMixin, ListView):
    model = Stock
    template_name = 'stock_list.html'
    context_object_name = 'stocks'
    paginate_by = 10

    def get_queryset(self):
        queryset = Stock.objects.select_related('product', 'created_by')
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(product__product_name__icontains=search)  # ensure correct field
        return queryset

    def paginate_queryset(self, queryset, page_size):
        """
        Override this to handle invalid pages by redirecting to the last valid page.
        """
        paginator = self.get_paginator(queryset, page_size, allow_empty_first_page=True)
        page = self.request.GET.get('page') or 1
        try:
            page_number = paginator.validate_number(page)
        except InvalidPage:
            page_number = paginator.num_pages  # fallback to last page

        page_obj = paginator.page(page_number)
        return (paginator, page_obj, page_obj.object_list, page_obj.has_other_pages())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paginator = context['paginator']
        page_obj = context['page_obj']
        current_page = page_obj.number
        total_pages = paginator.num_pages

        # Smart pagination logic
        page_range = []
        if total_pages <= 7:
            page_range = range(1, total_pages + 1)
        else:
            if current_page <= 4:
                page_range = [1, 2, 3, 4, 5, '...', total_pages]
            elif current_page >= total_pages - 3:
                page_range = [1, '...', total_pages - 4, total_pages - 3, total_pages - 2, total_pages - 1, total_pages]
            else:
                page_range = [1, '...', current_page - 1, current_page, current_page + 1, '...', total_pages]

        context['custom_page_range'] = page_range
        return context


class StockPDFView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        stocks = Stock.objects.all()

        search_query = request.GET.get('search', '')
        if search_query:
            stocks = stocks.filter(product__product_name__icontains=search_query)

        template_path = 'stock_list_pdf.html'
        context = {'stocks': stocks}
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="stock_list.pdf"'

        template = get_template(template_path)
        html = template.render(context)

        pisa_status = pisa.CreatePDF(html, dest=response)
        if pisa_status.err:
            return HttpResponse('We had some errors <pre>' + html + '</pre>')
        return response

class StockAddItemView(LoginRequiredMixin, View):
    def get(self, request):
        products = Product.objects.all()
        return render(request, 'stock_add_item.html', {'products': products})

    def post(self, request):
        product_id = request.POST.get('product')
        price_str = request.POST.get('price')

        if product_id and price_str:
            product = get_object_or_404(Product, product_id=product_id)

            # Check for duplicate
            if Stock.objects.filter(product=product).exists():
                messages.error(request, "Duplicate item: This product already exists in stock.")
                return redirect('stock_add_item')

            # Create the stock item
            Stock.objects.create(
                product=product,
                price=Decimal(price_str),
                quantity=0,
                created_by=request.user,
            )
            messages.success(request, "Item added to stock successfully.")
            return redirect('stock_list')

        messages.error(request, "Product and price are required.")
        return redirect('stock_add_item')
    


class EditPriceView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        stock_id = request.POST.get('stock_id')
        new_price = request.POST.get('price')

        if not stock_id or not new_price:
            messages.error(request, "Stock ID and price are required.")
            return redirect('stock_list')

        try:
            stock = Stock.objects.get(stock_id=stock_id)
            stock.price = Decimal(new_price)
            stock.save()
            messages.success(request, "Stock price updated successfully!")
        except Stock.DoesNotExist:
            messages.error(request, "Stock not found.")
        except (ValueError, Decimal.InvalidOperation):
            messages.error(request, "Invalid price format.")

        return redirect('stock_list')

class StockDeleteView(LoginRequiredMixin, View):
    def post(self, request, stock_id, *args, **kwargs):
        stock = get_object_or_404(Stock, stock_id=stock_id)
        stock.delete()
        return JsonResponse({'message': 'Stock deleted successfully'})

# Supplier List

class SupplierListView(LoginRequiredMixin, ListView):
    model = Supplier
    template_name = 'supplier_list.html'
    context_object_name = 'suppliers'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['suppliers'] = Supplier.objects.prefetch_related('products')  # Efficient query to load related products
        return context



class SupplierUpdateView(LoginRequiredMixin, UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'supplier_edit_form.html'
    success_url = reverse_lazy('supplier_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        supplier = self.get_object()
        
        # Fetch all products and the products associated with this supplier
        context['products'] = Product.objects.all()  # All products for selection
        context['selected_products'] = supplier.products.all()  # Selected products for this supplier
        
        return context

    def form_valid(self, form):
        supplier = form.save(commit=False)
        supplier.save()


        selected_products = self.request.POST.getlist('products')  # Get selected product ids

        # Clear existing products and add selected ones
        supplier.products.clear()  # Clear old product associations
        for product_id in selected_products:
            try:
                product = Product.objects.get(pk=product_id)
                supplier.products.add(product)  # Add the new products
            except Product.DoesNotExist:
                continue  # Skip if product doesn't exist, though it should

        messages.success(self.request, "Supplier updated successfully!")
        return super().form_valid(form)



class SupplierDeleteView(LoginRequiredMixin, DeleteView):
    model = Supplier
    success_url = reverse_lazy('supplier_list')

    def post(self, request, *args, **kwargs):
        supplier = self.get_object()
        supplier.delete()
        messages.success(request, "Supplier deleted successfully.")
        return redirect(self.success_url)

class SupplierCreateView(LoginRequiredMixin, View):
    def get(self, request):
        form = SupplierForm()
        return render(request, 'supplier_add_form.html', {'form': form})

    def post(self, request):
        form = SupplierForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            if Supplier.objects.filter(email=email).exists():
                messages.error(request, 'A supplier with this email already exists.')
                return redirect('supplier_add')  # redirect to clear message on reload

            supplier = form.save(commit=False)
            supplier.created_by = request.user
            supplier.save()
            form.save_m2m()
            messages.success(request, 'Supplier added successfully!')
            return redirect('supplier_list')

        messages.error(request, 'A supplier with this email already exists.')
        return redirect('supplier_add')


class CreateOrderView(LoginRequiredMixin, View):
    success_url = reverse_lazy('purchase_order_list')

    def get(self, request):
        products = Product.objects.all()
        return render(request, 'order_create_form.html', {
            'products': products,
            'suppliers': None
        })

    def post(self, request):
        product_id = request.POST.get('product')
        product = get_object_or_404(Product, product_id=product_id)
        suppliers = product.suppliers.all()
        products = Product.objects.all()

        if request.POST.get('final_submit'):
            for supplier in suppliers:
                quantity_key = f"quantity_{supplier.supplier_id}"
                quantity_str = request.POST.get(quantity_key)
                if quantity_str:
                    quantity = int(quantity_str)
                    ProductSupplier.objects.create(
                        product=product,
                        supplier=supplier,
                        quantity_ordered=quantity,
                        quantity_received=0,
                        quantity_remaining=quantity,
                        status='pending',
                        created_by=request.user
                    )
            messages.success(request, "Order(s) created successfully!")
            return redirect(self.success_url)  # use the attribute here

        return render(request, 'order_create_form.html', {
            'products': products,
            'suppliers': suppliers,
            'selected_product_id': product_id,
        })


    
class PurchaseOrderListView(LoginRequiredMixin, ListView):
    model = ProductSupplier
    template_name = 'purchase_order_list.html'
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        queryset = ProductSupplier.objects.select_related('product', 'supplier', 'created_by').order_by('-created_at')
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(product__product_name__icontains=search_query) |
                Q(batch_number__icontains=search_query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Include search in context to preserve input in templates
        context['search'] = self.request.GET.get('search', '')

        # Total quantity received
        filtered_queryset = self.get_queryset()
        context['total_quantity_received'] = filtered_queryset.aggregate(
            total=Sum('quantity_received')
        )['total'] or 0

        # Ellipsis pagination logic
        paginator = context['paginator']
        page_obj = context['page_obj']
        current_page = page_obj.number
        total_pages = paginator.num_pages

        if total_pages <= 7:
            page_range = range(1, total_pages + 1)
        else:
            if current_page <= 4:
                page_range = [1, 2, 3, 4, 5, '...', total_pages]
            elif current_page >= total_pages - 3:
                page_range = [1, '...', total_pages - 4, total_pages - 3, total_pages - 2, total_pages - 1, total_pages]
            else:
                page_range = [1, '...', current_page - 1, current_page, current_page + 1, '...', total_pages]

        context['custom_page_range'] = page_range
        return context


class PurchaseOrderUpdateView(LoginRequiredMixin, View):
    template_name = 'purchase_order_update.html'
    success_url = reverse_lazy('purchase_order_list')

    def get(self, request, pk):
        order = get_object_or_404(ProductSupplier, pk=pk)
        return render(request, self.template_name, {'order': order})

    def post(self, request, pk):
        order = get_object_or_404(ProductSupplier, pk=pk)
        quantity_delivered = request.POST.get('quantity_delivered')
        status = request.POST.get('status')

        # ✅ Get new delivery and expiry dates
        delivery_date_str = request.POST.get('delivery_date')
        expiry_date_str = request.POST.get('expiry_date')

        if quantity_delivered is not None:
            quantity_delivered = int(quantity_delivered)

            if quantity_delivered + order.quantity_received > order.quantity_ordered:
                return render(request, self.template_name, {'order': order, 'error': 'Delivered quantity exceeds ordered quantity.'})

            order.quantity_received += quantity_delivered
            order.quantity_remaining = max(0, order.quantity_ordered - order.quantity_received)

            if order.quantity_received >= order.quantity_ordered:
                order.status = 'complete'
            elif order.quantity_received > 0:
                order.status = 'incomplete'
            else:
                order.status = 'pending'

            # ✅ Save delivery/expiry dates if provided
            if delivery_date_str:
                order.delivery_date = datetime.strptime(delivery_date_str, "%Y-%m-%d").date()
            if expiry_date_str:
                order.expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()

            order.save()

            product = order.product
            stock_entries = Stock.objects.filter(product=product)
            if stock_entries.exists():
                stock = stock_entries.first()
                stock.quantity += quantity_delivered

                # ✅ Add expiry and delivery to stock
                stock.delivery_date = order.delivery_date
                stock.expiring_date = order.expiry_date
                stock.save()
            else:
                Stock.objects.create(
                    product=product,
                    quantity=quantity_delivered,
                    delivery_date=order.delivery_date,
                    expiring_date=order.expiry_date,
                    created_by=request.user
                )

            messages.success(request, 'Purchase order updated successfully and stock quantity updated.')
            return redirect(self.success_url)

        return render(request, self.template_name, {'order': order, 'error': 'Please provide valid data.'})

# Order Item Customer 

class OrderItemView(LoginRequiredMixin, View):
    def get(self, request):
        form = OrderItemForm()

        # Pop the messages out of session to show only once
        order_error = request.session.pop('order_error', None)
        order_success = request.session.pop('order_success', None)

        context = {
            'form': form,
            'order_error': order_error,
            'order_success': order_success,
        }
        return render(request, 'order_item_form.html', context)
        
    def post(self, request):
        form = OrderItemForm(request.POST)
        if form.is_valid():
            order_item = form.save(commit=False)

            latest_stock = Stock.objects.filter(product=order_item.product).order_by('-created_at').first()

            if latest_stock:
                if latest_stock.quantity >= order_item.quantity:
                    latest_stock.quantity -= order_item.quantity
                    latest_stock.save()

                    order = Order.objects.create(order_date=timezone.now())
                    order_item.order = order

                    order_item.subtotal = order_item.quantity * (latest_stock.price or 0)
                    order_item.created_by = request.user
                    order_item.save()

                    request.session['order_success'] = "Order placed and stock updated."
                    return redirect('order_item_history')
                else:
                   request.session['order_error'] = "Not enough stock available for this product."
            else:
                request.session['order_error'] = "No stock found for this product."

        # On form errors, just render the form with errors
        order_error = request.session.pop('order_error', None)
        order_success = request.session.pop('order_success', None)

        context = {
            'form': form,
            'order_error': order_error,
            'order_success': order_success,
        }
        return render(request, 'order_item_form.html', context)


class OrderItemHistoryView(LoginRequiredMixin, View):
    def get(self, request):
        order_items_list = OrderItem.objects.select_related('product', 'order', 'created_by').order_by('-order_date')
        paginator = Paginator(order_items_list, 10)

        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        current_page = page_obj.number
        total_pages = paginator.num_pages

        # Ellipsis logic
        if total_pages <= 7:
            page_range = range(1, total_pages + 1)
        else:
            if current_page <= 4:
                page_range = [1, 2, 3, 4, 5, '...', total_pages]
            elif current_page >= total_pages - 3:
                page_range = [1, '...', total_pages - 4, total_pages - 3, total_pages - 2, total_pages - 1, total_pages]
            else:
                page_range = [1, '...', current_page - 1, current_page, current_page + 1, '...', total_pages]

        orders = Order.objects.all().order_by('-order_date')

        return render(request, 'order_item_history.html', {
            'order_items': page_obj.object_list,
            'page_obj': page_obj,
            'paginator': paginator,
            'orders': orders,
            'is_paginated': page_obj.has_other_pages(),
            'custom_page_range': page_range
        })

    
class OrderHistoryPDFView(View):
    def get(self, request, *args, **kwargs):
        order_items = OrderItem.objects.select_related('product', 'created_by').order_by('-order_date')
        
        # Calculate total sales
        total_sales = sum(item.subtotal for item in order_items)
        
        template_path = 'order_history_pdf.html'
        context = {
            'order_items': order_items,
            'total_sales': total_sales
        }

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="order_history.pdf"'
        
        template = get_template(template_path)
        html = template.render(context)

        pisa_status = pisa.CreatePDF(html, dest=response)
        if pisa_status.err:
            return HttpResponse('Error generating PDF')
        return response
    
class OrderSlipView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'order_slip.html'
    context_object_name = 'order'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.get_object()
        order_items = order.orderitem_set.all()

        total_subtotal = sum(item.subtotal for item in order_items)

        context['order_items'] = order_items
        context['total_subtotal'] = total_subtotal
        return context

class OrderSlipPDFView(LoginRequiredMixin, View):
    def get(self, request, pk):
        order = Order.objects.get(pk=pk)
        order_items = order.orderitem_set.all()
        total_subtotal = sum(item.subtotal for item in order_items)

        template = get_template('order_slip_pdf.html')
        context = {
            'order': order,
            'order_items': order_items,
            'total_subtotal': total_subtotal
        }
        html = template.render(context)

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=order_slip_{order.order_id}.pdf'

        # Create PDF with font configuration
        pisa_status = pisa.CreatePDF(
            html,
            dest=response,
            encoding='UTF-8',
            link_callback=self.link_callback
        )
        
        if pisa_status.err:
            return HttpResponse("Error generating PDF", status=500)
        return response

    def link_callback(self, uri, rel):
        # For handling static files if needed
        return uri

# Expiring Products Table

class ExpiringProductsView(LoginRequiredMixin, ListView):
    model = ProductSupplier
    template_name = 'expiring_products.html'
    context_object_name = 'products'
    paginate_by = 10

    def get_queryset(self):
        today = timezone.now().date()
        thirty_days_later = today + timedelta(days=30)
        queryset = ProductSupplier.objects.filter(
            expiry_date__gte=today,
            expiry_date__lte=thirty_days_later
        ).select_related('product', 'supplier').order_by('expiry_date')

        for product in queryset:
            product.days_remaining = (product.expiry_date - today).days
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paginator = context['paginator']
        page_obj = context['page_obj']
        current_page = page_obj.number
        total_pages = paginator.num_pages

        # Ellipsis pagination logic same as ProductListView
        if total_pages <= 7:
            page_range = range(1, total_pages + 1)
        else:
            if current_page <= 4:
                page_range = [1, 2, 3, 4, 5, '...', total_pages]
            elif current_page >= total_pages - 3:
                page_range = [1, '...', total_pages - 4, total_pages - 3, total_pages - 2, total_pages - 1, total_pages]
            else:
                page_range = [1, '...', current_page - 1, current_page, current_page + 1, '...', total_pages]

        context['custom_page_range'] = page_range
        return context

# Low Stock Alert

class LowStockAlertView(LoginRequiredMixin, ListView):
    model = Stock
    template_name = 'low_stock_alerts.html'
    context_object_name = 'low_stock_items'
    paginate_by = 10

    def get_queryset(self):
        return Stock.objects.select_related('product').filter(
            quantity__lt=10  # Threshold for low stock
        ).order_by('quantity')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paginator = context['paginator']
        page_obj = context['page_obj']
        current_page = page_obj.number
        total_pages = paginator.num_pages

        # Ellipsis logic for pagination
        page_range = []
        if total_pages <= 7:
            page_range = range(1, total_pages + 1)
        else:
            if current_page <= 4:
                page_range = [1, 2, 3, 4, 5, '...', total_pages]
            elif current_page >= total_pages - 3:
                page_range = [1, '...', total_pages - 4, total_pages - 3, total_pages - 2, total_pages - 1, total_pages]
            else:
                page_range = [1, '...', current_page - 1, current_page, current_page + 1, '...', total_pages]

        context['custom_page_range'] = page_range
        context['current_page'] = 'Low Stock Alerts'
        return context