# Generated by Django 3.1.3 on 2020-12-16 03:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0003_auto_20201215_1719'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='photo',
        ),
        migrations.DeleteModel(
            name='Photo',
        ),
    ]
