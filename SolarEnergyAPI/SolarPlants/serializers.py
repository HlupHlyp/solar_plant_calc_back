from SolarPlants.models import item_model,plant_model,item2plant_model, CustomUser
#from SolarPlants.models import AuthUser
from rest_framework import serializers
from collections import OrderedDict

class ItemPartialSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(required = True)
    short_description = serializers.CharField(required = False)
    long_description = serializers.CharField(required = False)
    specification = serializers.CharField(required = False)
    item_cost = serializers.IntegerField(required = True)
    item_type = serializers.CharField(required = True)
    item_voltage = serializers.DecimalField(decimal_places=2, max_digits=10,required = True)
    item_capacity = serializers.DecimalField(decimal_places=2, max_digits=10,required = True)
    item_power = serializers.DecimalField(decimal_places=2, max_digits=10,required = True)
    class Meta:
        # Модель, которую мы сериализуем
        model = item_model
        # Поля, которые мы сериализуем
        fields = ["item_name","short_description", "long_description", "specification", "item_cost", 
        "item_type", "item_voltage", "item_capacity", "item_power"]
        def get_fields(self):
            new_fields = OrderedDict()
            for name, field in super().get_fields().items():
                field.required = True
                new_fields[name] = field
            return new_fields 
        
class FreeItemPartialSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(required = False)
    short_description = serializers.CharField(required = False)
    long_description = serializers.CharField(required = False)
    specification = serializers.CharField(required = False)
    item_cost = serializers.IntegerField(required = False)
    item_type = serializers.CharField(required = False)
    item_voltage = serializers.DecimalField(decimal_places=2, max_digits=10,required = False)
    item_capacity = serializers.DecimalField(decimal_places=2, max_digits=10,required = False)
    item_power = serializers.DecimalField(decimal_places=2, max_digits=10,required = False)
    class Meta:
        # Модель, которую мы сериализуем
        model = item_model
        # Поля, которые мы сериализуем
        fields = ["item_name","short_description", "long_description", "specification", "item_cost", 
        "item_type", "item_voltage", "item_capacity", "item_power"]
        def get_fields(self):
            new_fields = OrderedDict()
            for name, field in super().get_fields().items():
                print('!')
                field.required = True
                new_fields[name] = field
            return new_fields         

class ItemSerializer(serializers.ModelSerializer):

    class Meta:
        # Модель, которую мы сериализуем
        model = item_model
        # Поля, которые мы сериализуем
        fields = ["item_id", "item_name", "img_link", "short_description", "long_description", "specification", "item_cost", 
        "item_type", "item_voltage", "item_capacity", "item_power"] 

class PlantSerializer(serializers.ModelSerializer):
    class Meta:
        # Модель, которую мы сериализуем
        model = plant_model
        # Поля, которые мы сериализуем  
        fields = ["plant_id", "plant_status", "creation_date", "forming_date", "finishing_date", "generation", "saving", "latitude", "creator", "moderator"]        

class PlantPartialSerializer(serializers.ModelSerializer):
    latitude = serializers.DecimalField(decimal_places=5, max_digits=8, required=True)
    class Meta:
        # Модель, которую мы сериализуем
        model = plant_model
        # Поля, которые мы сериализуем
        fields = ["latitude"] 

class PlantStatusSerializer(serializers.ModelSerializer):
    class Meta:
        # Модель, которую мы сериализуем
        model = plant_model
        # Поля, которые мы сериализуем
        fields = ["plant_status"] 

class PlantFinishSerializer(serializers.ModelSerializer):
    class Meta:
        # Модель, которую мы сериализуем
        model = plant_model
        # Поля, которые мы сериализуем
        fields = ["plant_status", "generation", "saving"] 

class Item2PlantSerializer(serializers.ModelSerializer):
    item_id = serializers.IntegerField(required = True)
    plant_id = serializers.IntegerField(required = True)
    amount = serializers.IntegerField(required = True)
    class Meta:
        # Модель, которую мы сериализуем
        model = item2plant_model
        # Поля, которые мы сериализуем
        fields = ["item_id", "plant_id", "amount"]

class UserSerializer(serializers.ModelSerializer):
    is_staff = serializers.BooleanField(default=False, required=False)
    is_superuser = serializers.BooleanField(default=False, required=False)
    fio = serializers.CharField(required = True)
    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'is_staff', 'is_superuser', 'fio']