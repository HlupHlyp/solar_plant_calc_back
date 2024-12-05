from django.db import models
import uuid
import datetime
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import BaseUserManager, PermissionsMixin

class NewUserManager(BaseUserManager):
    def create_user(self,email,password=None, **extra_fields):
        if not email:
            raise ValueError('User must have an email address')
        
        email = self.normalize_email(email) 
        user = self.model(email=email, **extra_fields) 
        user.set_password(password)
        user.save(using=self._db)
        return user
    def create_superuser(self,email,password=None, **extra_fields):
        user = self.create_user(email, password=password, **extra_fields)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(("email адрес"), unique=True)
    password = models.CharField(max_length=128, verbose_name="Пароль")    
    is_staff = models.BooleanField(default=False, verbose_name="Является ли пользователь менеджером?")
    is_superuser = models.BooleanField(default=False, verbose_name="Является ли пользователь админом?")
    fio = models.CharField(max_length=128)    

    USERNAME_FIELD = 'email'

    objects =  NewUserManager()

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
    img_link = models.CharField(max_length=200, default=None, blank=True, null=True)
    short_description = models.CharField(max_length=255)
    long_description = models.CharField(max_length=1000)
    specification = models.CharField(max_length=400)
    item_cost = models.IntegerField()
    item_type = models.CharField(max_length=20, choices=item_types)
    item_voltage = models.DecimalField(decimal_places=2, max_digits=10, default=None, blank=True, null=True)
    item_capacity = models.DecimalField(decimal_places=2, max_digits=10, default=None, blank=True, null=True)
    item_power = models.DecimalField(decimal_places=2, max_digits=10, default=None, blank=True, null=True)

    class Meta:
        managed = True
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
    creation_date = models.DateTimeField(default = datetime.datetime.now())
    forming_date = models.DateTimeField(default=None, blank=True, null=True)
    finishing_date = models.DateTimeField(default=None, blank=True, null=True)
    generation = models.DecimalField(decimal_places=2, max_digits=10, default=None, blank=True, null=True)
    saving = models.DecimalField(decimal_places=2, max_digits=10, default=None, blank=True, null=True)
    latitude = models.DecimalField(decimal_places=5, max_digits=8, default=None, blank=True, null=True)
    creator = models.ForeignKey(CustomUser, db_column='creator', default = '1', on_delete = models.CASCADE)
    moderator = models.ForeignKey(CustomUser, models.DO_NOTHING, db_column='moderator', related_name='plant_moderator', blank=True, null=True)
    class Meta:
        managed = True
        db_table = 'plants'

class item2plant_model(models.Model):
    relate_id = models.AutoField(primary_key=True)
    item = models.ForeignKey('item_model', on_delete = models.CASCADE)
    plant = models.ForeignKey('plant_model', on_delete = models.CASCADE)
    amount = models.IntegerField(default = 1)
    class Meta:
        managed = True
        db_table = 'item2plant'
        constraints = [
            models.UniqueConstraint(fields=['item_id', 'plant_id'], name='unique item in plant')
        ]

