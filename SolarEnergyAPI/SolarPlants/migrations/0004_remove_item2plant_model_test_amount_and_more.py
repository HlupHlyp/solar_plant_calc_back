# Generated by Django 5.1.2 on 2024-11-03 15:55

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('SolarPlants', '0003_alter_plant_model_creation_date'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='item2plant_model',
            name='test_amount',
        ),
        migrations.AlterField(
            model_name='plant_model',
            name='creation_date',
            field=models.DateTimeField(default=datetime.datetime(2024, 11, 3, 15, 55, 9, 538356)),
        ),
    ]