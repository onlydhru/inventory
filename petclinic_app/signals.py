import random
import string
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import ProductSupplier
from datetime import datetime
import random
import string
from django.utils import timezone

def set_batch_number(sender, instance, **kwargs):
    if not instance.batch_number:
        instance.batch_number = generate_batch_number()

def generate_batch_number():
    # Generate a unique batch number (same as in the previous example)
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
    random_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"BN-{timestamp}-{random_string}"