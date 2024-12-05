"""
URL configuration for lab project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from SolarEnergy import views
from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.GetPlantItems),
    path('plant_req/<int:id>', views.GetPlantRequest, name='plant_req_url'),
    path('item/<str:id>/', views.GetItem, name='item_url'),
    path('add2plant', views.Add2Plant),
    path('plant_req/del_plant', views.DelPlant),
]
