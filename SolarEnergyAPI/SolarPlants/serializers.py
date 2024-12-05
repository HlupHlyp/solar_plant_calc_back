from SolarPlants.models import item_model,plant_model,item2plant_model
#from SolarPlants.models import AuthUser
from rest_framework import serializers
from django.contrib.auth.models import User


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        # Модель, которую мы сериализуем
        model = item_model
        # Поля, которые мы сериализуем
        fields = ["item_id", "item_status", "item_name", "img_link", "short_description", "long_description", "specification", "item_cost", 
        "item_type", "item_voltage", "item_capacity", "item_power"]

class FullItemSerializer(serializers.ModelSerializer):

    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        # Модель, которую мы сериализуем
        model = item_model
        # Поля, которые мы сериализуем
        fields = ["item_id", "item_status", "item_name", "img_link", "short_description", "long_description", "specification", "item_cost", 
        "item_type", "item_voltage", "item_capacity", "item_power", "user_id"] 

class PlantListSerializer(serializers.ModelSerializer):
    class Meta:
        # Модель, которую мы сериализуем
        model = plant_model
        # Поля, которые мы сериализуем  
        fields = ["plant_id", "plant_status", "creation_date", "forming_date", "finishing_date", "creator_login", "moderator_login", 
        "generation", "saving", "latitude", "fio"]   

class PlantSerializer(serializers.ModelSerializer):
    class Meta:
        # Модель, которую мы сериализуем
        model = plant_model
        # Поля, которые мы сериализуем  
        fields = ["plant_id", "plant_status", "creation_date", "forming_date", "finishing_date", "creator_login", "moderator_login", 
        "generation", "saving", "latitude", "fio", "user"]    

class PlantChangeSerializer(serializers.ModelSerializer):
    class Meta:
        # Модель, которую мы сериализуем
        model = plant_model
        # Поля, которые мы сериализуем
        fields = ["generation", "saving", "latitude", "fio"] 

class PlantStatusSerializer(serializers.ModelSerializer):
    class Meta:
        # Модель, которую мы сериализуем
        model = plant_model
        # Поля, которые мы сериализуем
        fields = ["plant_status"] 

class Item2PlantSerializer(serializers.ModelSerializer):
    item_id = serializers.IntegerField(required = True)
    plant_id = serializers.IntegerField(required = True)
    amount = serializers.IntegerField(required = True)
    class Meta:
        # Модель, которую мы сериализуем
        model = item2plant_model
        # Поля, которые мы сериализуем
        fields = ["relate_id", "item_id", "plant_id", "amount"]

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["id","password", "last_login", "is_superuser", "username", "last_name", "email", 
        "is_staff", "is_active", "date_joined", "first_name"]