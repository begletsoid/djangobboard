# Generated by Django 3.1.4 on 2021-06-08 10:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0012_bb_phone_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='bb',
            name='likes_count',
            field=models.BigIntegerField(default='0'),
        ),
    ]
