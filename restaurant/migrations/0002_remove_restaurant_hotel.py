# Generated by Django 5.1.6 on 2025-03-02 14:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('restaurant', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='restaurant',
            name='hotel',
        ),
    ]
