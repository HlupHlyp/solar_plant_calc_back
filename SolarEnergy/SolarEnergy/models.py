from django.db import models
import uuid
from datetime import datetime
class item_model(models.Model):
    item_statuses = {
        'active': 'active',
        'deleted': 'deleted',
    }
    item_types = {
        'solar_panel': 'solar_panel',
        'battery': 'battery',
    }
    item_id = models.AutoField(primary_key=True)
    item_status = models.CharField(max_length=20, choices=item_statuses, default = 'active')
    item_name = models.CharField(max_length=200)
    img_link = models.CharField(max_length=200)
    short_description = models.CharField(max_length=255)
    long_description = models.CharField(max_length=1000)
    specification = models.CharField(max_length=400)
    item_cost = models.IntegerField()
    item_type = models.CharField(max_length=20, choices=item_types)
    item_voltage = models.DecimalField(decimal_places=2, max_digits=10, default=None, blank=True, null=True)
    item_capacity = models.DecimalField(decimal_places=2, max_digits=10, default=None, blank=True, null=True)
    item_power = models.DecimalField(decimal_places=2, max_digits=10, default=None, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'items'
class plant_model(models.Model):
    plant_statuses = {
        'draft': 'draft',
        'deleted': 'deleted',
        'completed': 'completed',
        'formed': 'formed',
        'rejected': 'rejected',
    }
    plant_id = models.AutoField(primary_key=True)
    plant_status = models.CharField(max_length=20, choices=plant_statuses, default = 'draft')
    creation_date = models.DateTimeField(default = datetime.now)
    forming_date = models.DateTimeField(default=None, blank=True, null=True)
    finishing_date = models.DateTimeField(default=None, blank=True, null=True)
    creator_login = models.CharField(max_length=50)
    moderator_login = models.CharField(max_length=50, default=None, blank=True, null=True)
    generation = models.DecimalField(decimal_places=2, max_digits=10, default=None, blank=True, null=True)
    saving = models.DecimalField(decimal_places=2, max_digits=10, default=None, blank=True, null=True)
    latitude = models.DecimalField(decimal_places=5, max_digits=8, default=None, blank=True, null=True)
    fio = models.CharField(max_length=255, default=None, blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'plants'

class item2plant_model(models.Model):
    relate_id = models.AutoField(primary_key=True)
    item_id = models.IntegerField()
    plant_id = models.IntegerField()
    amount = models.IntegerField()
    class Meta:
        managed = False
        db_table = 'item2plant'
        constraints = [
            models.UniqueConstraint(fields=['item_id', 'plant_id'], name='unique item in plant')
        ]
