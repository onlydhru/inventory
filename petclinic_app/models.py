from django.db import models
from django.contrib.auth.models import User
import random
import string
from datetime import datetime

CATEGORY_CHOICES = (
    ('Cat Food', 'Cat Food'),
    ('Medicine', 'Medicine'),
    ('Dog Food', 'Dog Food'),
    ('Pet Grooming', 'Pet Grooming'),
)


class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    product_name = models.CharField(max_length=255, unique=True)
    image = models.ImageField(upload_to='product_images/', null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, null=True, blank=True)
    suppliers = models.ManyToManyField("Supplier", blank=True)  # Use string reference
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    movement_threshold = models.IntegerField(default=100)


    def __str__(self):
        return self.product_name

class Stock(models.Model):
    stock_id = models.AutoField(primary_key=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_supplier = models.ForeignKey('ProductSupplier', on_delete=models.CASCADE, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    expiring_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.product_name} - {self.quantity} in stock - Batch {self.product_supplier.batch_number}"


class Supplier(models.Model):
    supplier_id = models.AutoField(primary_key=True)
    supplier_name = models.CharField(max_length=255)
    supplier_location = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    contact_number = models.CharField(max_length=20, blank=True, null=True)  # ✅ New field
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    products = models.ManyToManyField(Product, blank=True)

    def __str__(self):
        return self.supplier_name

class ProductSupplier(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('complete', 'Complete'),
        ('incomplete', 'Incomplete'),
    ]

    id = models.AutoField(primary_key=True)
    supplier = models.ForeignKey('Supplier', on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    quantity_ordered = models.IntegerField()
    quantity_received = models.IntegerField()
    quantity_remaining = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    date_received = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    delivery_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    batch_number = models.CharField(max_length=100, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.batch_number:
            self.batch_number = self.generate_batch_number()  # Generate batch number
        super(ProductSupplier, self).save(*args, **kwargs)  # Call the parent class's save method

    def generate_batch_number(self):
        # Use current time if created_at is None
        timestamp = self.created_at.strftime('%Y%m%d%H%M%S') if self.created_at else datetime.now().strftime('%Y%m%d%H%M%S')
        random_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))  # Random 6-character string
        return f"BN-{timestamp}-{random_string}"  # Example: 'BN-20250409120030-ABC123'

    def __str__(self):
        return f"{self.product.product_name} from {self.supplier.supplier_name}"
    
    

class Order(models.Model):
    order_id = models.AutoField(primary_key=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    order_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.order_id} by {self.created_by.username if self.created_by else 'Unknown'}"

class OrderItem(models.Model):
    id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    order_date = models.DateTimeField(auto_now_add=True,  null=True, blank=True)


    def __str__(self):
        return f"{self.quantity} x {self.product.product_name} in Order {self.order.order_id}"

