# Generated by Django 5.1.6 on 2025-03-16 07:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restaurant', '0009_alter_fooditem_restaurant_alter_order_name_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='location',
            field=models.CharField(default='Address', max_length=255),
        ),
    ]
