# Generated by Django 3.1.3 on 2020-12-01 13:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0003_auto_20201201_1356'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='products',
            field=models.ManyToManyField(to='order.OrderItem'),
        ),
    ]
