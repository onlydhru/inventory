# Generated by Django 5.2 on 2025-04-17 16:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('petclinic_app', '0035_alter_orderitem_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.CharField(blank=True, choices=[('Cat Food', 'Cat Food'), ('Medicine', 'Medicine'), ('Dog Food', 'Dog Food'), ('Pet Grooming', 'Pet Grooming')], max_length=20, null=True),
        ),
    ]
