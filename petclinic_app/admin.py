from django.contrib import admin
from .models import Supplier, Product, Order, OrderItem, Stock, ProductSupplier



admin.site.register(Supplier)
admin.site.register(ProductSupplier)
admin.site.register(Product)
admin.site.register(Stock)
admin.site.register(Order)
admin.site.register(OrderItem)






