# Generated by Django 5.1.7 on 2025-03-30 07:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('petclinic_app', '0005_user_remove_order_customer_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.CharField(blank=True, choices=[('Cat Food', 'Cat Food'), ('Medicine', 'Medicine'), ('Dog Food', 'Dog Food')], max_length=50, null=True),
        ),
    ]
