# Generated by Django 5.1.7 on 2025-03-30 07:29

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('petclinic_app', '0004_alter_product_category'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('user_id', models.AutoField(primary_key=True, serialize=False)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='order',
            name='customer',
        ),
        migrations.RemoveField(
            model_name='notification',
            name='product',
        ),
        migrations.RemoveField(
            model_name='report',
            name='order',
        ),
        migrations.RemoveField(
            model_name='report',
            name='product',
        ),
        migrations.RemoveField(
            model_name='product',
            name='product_description',
        ),
        migrations.RemoveField(
            model_name='product',
            name='product_price',
        ),
        migrations.RemoveField(
            model_name='product',
            name='quantity',
        ),
        migrations.RemoveField(
            model_name='product',
            name='supplier',
        ),
        migrations.RemoveField(
            model_name='supplier',
            name='supplier_address',
        ),
        migrations.RemoveField(
            model_name='supplier',
            name='supplier_contact',
        ),
        migrations.AddField(
            model_name='product',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='supplier',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='supplier',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='supplier',
            name='supplier_location',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='supplier',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='quantity',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.CharField(choices=[('Cat Food', 'Cat Food'), ('Medicine', 'Medicine'), ('Dog Food', 'Dog Food')], max_length=50),
        ),
        migrations.CreateModel(
            name='Stock',
            fields=[
                ('stock_id', models.AutoField(primary_key=True, serialize=False)),
                ('quantity', models.IntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='petclinic_app.product')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='petclinic_app.user')),
            ],
        ),
        migrations.CreateModel(
            name='ProductSupplier',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('quantity_ordered', models.IntegerField()),
                ('quantity_received', models.IntegerField()),
                ('quantity_remaining', models.IntegerField()),
                ('status', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='petclinic_app.product')),
                ('supplier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='petclinic_app.supplier')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='petclinic_app.user')),
            ],
        ),
        migrations.AddField(
            model_name='order',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='petclinic_app.user'),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='petclinic_app.user'),
        ),
        migrations.AddField(
            model_name='product',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='petclinic_app.user'),
        ),
        migrations.AddField(
            model_name='supplier',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='petclinic_app.user'),
        ),
        migrations.DeleteModel(
            name='Customer',
        ),
        migrations.DeleteModel(
            name='Notification',
        ),
        migrations.DeleteModel(
            name='Report',
        ),
    ]
