# Generated by Django 3.1.3 on 2020-12-01 12:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0002_auto_20201118_1813'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='products',
            field=models.ManyToManyField(related_name='my_orders', to='order.OrderItem'),
        ),
    ]
