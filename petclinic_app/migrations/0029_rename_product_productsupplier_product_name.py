# Generated by Django 5.2 on 2025-04-08 14:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('petclinic_app', '0028_alter_productsupplier_supplier'),
    ]

    operations = [
        migrations.RenameField(
            model_name='productsupplier',
            old_name='product',
            new_name='product_name',
        ),
    ]
