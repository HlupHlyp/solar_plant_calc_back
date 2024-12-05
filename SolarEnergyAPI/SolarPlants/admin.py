from django.contrib import admin

# Register your models here.
from SolarPlants.models import item_model, plant_model, item2plant_model

admin.site.register(item_model)
admin.site.register(plant_model)
admin.site.register(item2plant_model)
