# Generated by Django 5.0 on 2023-12-10 07:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('LittleLemon', '0003_rename_first_name_booking_name_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='comment',
            field=models.CharField(default='', max_length=1000),
        ),
    ]