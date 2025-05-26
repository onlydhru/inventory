from datetime import timedelta
from django.utils import timezone
from .models import ProductSupplier, Stock

def notifications(request):
    context = {
        'expiring_products': [],
        'expiring_count': 0,
        'critical_count': 0,
        'low_stock_items': [],
        'low_stock_count': 0,
        'total_notifications': 0
    }

    # Only process notifications for authenticated users
    if request.user.is_authenticated:
        # Expiring products logic (keep your existing code)
        today = timezone.now().date()
        thirty_days_later = today + timedelta(days=30)

        expiring_products = ProductSupplier.objects.filter(
            expiry_date__gte=today,
            expiry_date__lte=thirty_days_later
        ).select_related('product').order_by('expiry_date')[:5]

        for product in expiring_products:
            product.days_remaining = (product.expiry_date - today).days

        # Low stock alerts logic
        low_stock_items = Stock.objects.select_related('product').filter(
            quantity__lt=10
        ).order_by('quantity')[:5]

        # Update context
        context.update({
            'expiring_products': expiring_products,
            'expiring_count': expiring_products.count(),
            'critical_count': sum(1 for p in expiring_products if p.days_remaining <= 7),
            'low_stock_items': low_stock_items,
            'low_stock_count': low_stock_items.count(),
            'total_notifications': expiring_products.count() + low_stock_items.count()
        })

    return context