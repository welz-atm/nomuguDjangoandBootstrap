# Generated by Django 3.0.4 on 2020-10-08 16:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0002_auto_20201008_1722'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.CharField(blank=True, choices=[('beauty', 'Beauty'), ('computer/laptops', 'Computer/Laptops'), ('electronics', 'Electronics'), ('fashion', 'Fashion'), ('flight', 'Flight'), ('food', 'Food'), ('home appliances', 'Home Appliances'), ('hotels', 'Hotel'), ('Kitchen appliances', 'Kitchen Appliances'), ('phones/tablets', 'Phones/Tablets')], max_length=25, null=True),
        ),
    ]