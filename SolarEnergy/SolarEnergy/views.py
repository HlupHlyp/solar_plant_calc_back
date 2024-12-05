from django.http import HttpResponse
from django.shortcuts import render
from datetime import date
from SolarEnergy.models import item_model, plant_model, item2plant_model
import psycopg2
from django.db.models import Max

def AddLineChanges(items):
    for item in items:
        item['short_description'] = item['short_description'].replace('!', '\n')
        item['specification'] = item['specification'].replace('!', '\n')
    return items

def GetItem(request, id):
    item = item_model.objects.filter(item_id = id).values()
    return render(request, 'item_page.html', item)

def GetPlantRequest(request, id):
    plant_items = []
    plant = {}
    temp_plant = plant_model.objects.filter(plant_id = id, plant_status = 'draft').values()
    if temp_plant:
        item2plant_list = item2plant_model.objects.filter(plant_id = id).values()
        for item2plant in item2plant_list:
            plant_items.append(item2plant)
        for item in temp_plant:
            plant = item
    data = {'data':{'items': AddLineChanges(item_model.objects.values()), 'plant_req':plant_items, 'plant':plant}}
    return render(request, 'plant_req_page.html', data)

def GetPlantItems(request):
    search_request = request.GET.get('search_request','')
    sorted_list= [] 
    for item in ((item_model.objects.filter(item_name__icontains=search_request) or item_model.objects.filter(long_description__icontains=search_request) 
    or item_model.objects.filter(short_description__icontains=search_request)) and item_model.objects.filter(item_status = 'active')).values():
        sorted_list.append(item)
    data = {'data':{'items':AddLineChanges(sorted_list),'searchText':search_request}}
    return render(request, 'plant_items_page.html', data)

def Add2Plant(request):
    temp_item_id = request.POST['item_id']
    temp_plant_id = request.POST['plant_id']
    records = item2plant_model.objects.filter(item_id = temp_item_id, plant_id = temp_plant_id).values()
    if not records:
        max_id = item2plant_model.objects.aggregate(Max('relate_id'))
        item2plant = item2plant_model(item_id=temp_item_id, plant_id = temp_plant_id, amount = 1, 
        relate_id = max_id['relate_id__max'] + 1)
        item2plant.save()
    else:
        item2plant = item2plant_model.objects.get(item_id = temp_item_id, plant_id = temp_plant_id)
        item2plant.amount = item2plant.amount+1
        item2plant.save()
    return GetPlantItems(request)
    
def DelPlant(request):
    temp_plant_id = request.POST['plant_id']

    print(1)

    conn = psycopg2.connect(dbname="solarenergy", host="127.0.0.1", user="student", password="root", port="5432")

    cursor = conn.cursor()
    cursor.execute(str("UPDATE plants set plant_status = 'deleted' where plant_id = ") + str(temp_plant_id))
    
    conn.commit()   # реальное выполнение команд sql1
    
    cursor.close()
    conn.close()

    return GetPlantItems(request)