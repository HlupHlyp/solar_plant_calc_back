from django.shortcuts import render
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status
from SolarPlants.serializers import ItemSerializer, PlantSerializer, PlantListSerializer, PlantChangeSerializer, Item2PlantSerializer, PlantStatusSerializer, UserSerializer
from SolarPlants.models import item_model, plant_model, item2plant_model
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from SolarPlants.minio import add_pic, del_pic
import datetime
from django.contrib.auth.models import User

def user():
    try:
        user1 = User.objects.get(id=1)
    except:
        user1 = User(id=1, first_name="Иван", last_name="Иванов", password=1234, username="user1")
        user1.save()
    return user1

class ItemList(APIView):
    model_class = item_model
    serializer_class = ItemSerializer

    # Возвращает список акций
    def get(self, request, format=None, creator_login = "andrew"):
        plant_id = 0
        amount = 0
        search_request = request.GET.get('search_request','')
        items = (item_model.objects.filter(item_name__icontains=search_request, item_status = 'active') 
        or item_model.objects.filter(long_description__icontains=search_request, item_status = 'active') 
        or item_model.objects.filter(short_description__icontains=search_request, item_status = 'active'))
        serializer = self.serializer_class(items, many=True)
        plants = plant_model.objects.filter(creator_login = creator_login, plant_status = "draft").values()
        if not plants:
            data = {'items':serializer.data, 'plant_id':None, 'amount':None}
        else:
            for plant in plants:
                plant_id = plant['plant_id']
            items2plant = item2plant_model.objects.filter(plant_id = plant_id).values()
            for item2plant in items2plant:
                amount+=item2plant['amount']
            data = {'items':serializer.data, 'plant_id':plant_id, 'amount':amount} 
        return Response(data)

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            item = serializer.save()
            user1 = user()
            item.user = user1
            item.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Добавляет новую акцию

class ItemDetail(APIView):
    model_class = item_model
    serializer_class = ItemSerializer

    # Возвращает информацию об акции
    def get(self, request, item_id, format=None):
        item = get_object_or_404(self.model_class, item_id=item_id)
        serializer = self.serializer_class(item)
        return Response(serializer.data)

    def put(self, request, item_id, format=None):
        item = get_object_or_404(self.model_class, item_id=item_id)
        serializer = self.serializer_class(item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, item_id, format=None):
        item = get_object_or_404(self.model_class, item_id=item_id)
        del_pic(item_id)
        item.item_status = "deleted"
        item.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def post(self, request, item_id, format=None):
        item = get_object_or_404(self.model_class, item_id=item_id)
        serializer = self.serializer_class(item, data=request.data, partial=True)
        if serializer.is_valid():
            pic = request.FILES.get("pic")
            pic_result = add_pic(item, pic)
            if 'error' in pic_result.data:    
                return pic_result
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UsersList(APIView):
    model_class = User
    serializer_class = UserSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, user_id):
        user = get_object_or_404(self.model_class, id = user_id)
        serializer = self.serializer_class(user,data = request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response('Incorrect data', status=status.HTTP_400_BAD_REQUEST)

class item2plant(APIView):
    model_class = item2plant_model
    serializer_class = Item2PlantSerializer

    def delete(self, request, format=None):
        item_id = request.POST['item_id']
        plant_id = request.POST['plant_id']
        if self.model_class.objects.filter(item_id = item_id, plant_id = plant_id):
            self.model_class.objects.filter(item_id = item_id, plant_id = plant_id).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, format=None):
        item_id = request.POST['item_id']
        plant_id = request.POST['plant_id']
        amount = request.POST['amount']
        item2plant = get_object_or_404(self.model_class, item_id=item_id, plant_id=plant_id)
        item2plant.amount = amount
        serializer = self.serializer_class(item2plant, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PlantList(APIView):
    model_class = plant_model
    serializer_class = PlantListSerializer

    def get(self, request, format=None):
        plants = []
        req_plant_status = request.POST.get("plant_status")
        status_f = False
        bottom_date = request.POST.get("bottom_date")
        bottom_f = False
        top_date = request.POST.get("top_date")
        top_f = False
        if req_plant_status:
            status_f = True
            if not req_plant_status in ['rejected', 'completed', 'formed']:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        if top_date:
            top_f = True
        else: 
            top_date = datetime.datetime.now()
        if bottom_date:
            top_f = True
        else:
            bottom_date = "2000-01-01"
        if status_f:
            plants = (plant_model.objects.filter(plant_status = req_plant_status) 
            & plant_model.objects.filter(forming_date__range=[bottom_date, top_date]))
            print(req_plant_status)
            print(plants)
        else:
            plants = ((plant_model.objects.filter(plant_status = "completed") | plant_model.objects.filter(plant_status = "formed") 
            | plant_model.objects.filter(plant_status = "rejected")) & plant_model.objects.filter(forming_date__range=[bottom_date, top_date]))
            print(plants.values())
            print(bottom_date)
            print(top_date)
            plants =  plant_model.objects.filter(forming_date__range=[bottom_date, top_date])
            print(plants.values())
        if not plants:
            return Response(None)
        else:
            serializer = self.serializer_class(plants, many=True)
            return Response(serializer.data)

class PlantDetail(APIView):
    model_class = plant_model
    serializer_class = PlantSerializer
    partial_serializer_class = PlantChangeSerializer

    def get(self, request, plant_id, format=None):
        plant = plant_model.objects.get(plant_id = plant_id)
        if not plant:
            return Response(status=status.HTTP_400_BAD_REQUEST)  
        items = []
        items2plant = item2plant_model.objects.filter(plant_id = plant_id).values()
        for item2plant in items2plant:
            item = item_model.objects.get(item_id = int(item2plant['item_id']))
            items.append({'item_name':item.item_name, 'img_link':item.img_link, 'amount':item2plant["amount"], 
                          'item_cost':item.item_cost,'sum_cost':item.item_cost*item2plant["amount"]})
        data = {"plant":self.serializer_class(plant).data, "items":items}
        return Response(data)

    def put(self, request, plant_id, format=None):
        plant = get_object_or_404(self.model_class, plant_id=plant_id)
        serializer = self.partial_serializer_class(plant, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, plant_id, format=None):
        plant = get_object_or_404(plant_model, plant_id = plant_id)
        plant.plant_status = "deleted"
        plant.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['Put'])
def plant_forming(request, plant_id, format=None):
    plant = get_object_or_404(plant_model, plant_id = plant_id)
    plant.plant_status = "formed"
    plant.forming_date = datetime.datetime.now()
    plant.save()
    return Response(status=status.HTTP_206_PARTIAL_CONTENT)

@api_view(['Put'])
def plant_finishing(request, plant_id, format=None):
    plant_status = request.POST.get("plant_status")
    plant = get_object_or_404(plant_model, plant_id = plant_id)
    if plant_status in ["rejected", "completed"] and plant.plant_status == 'formed':
        serializer = PlantStatusSerializer(plant, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(finishing_date = datetime.datetime.now())
            return Response(status=status.HTTP_206_PARTIAL_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)
    return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['Post'])
def add2plant(request, item_id, plant_id, format=None, user_id = 6):
    plant = None
    f = False
    if not plant_model.objects.filter(plant_id = plant_id, plant_status = 'draft').values(): f = True  
    if f:
        if not plant_model.objects.filter(user_id = user_id, plant_status = 'draft').values():
            plant = plant_model.objects.create(user = User.objects.get(id = user_id))
            plant.save()
        else:
            plant = plant_model.objects.get(user_id = user_id, plant_status = 'draft')
        plant_id = plant.plant_id

    get_object_or_404(item_model, item_id=item_id)

    if not item2plant_model.objects.filter(item_id = item_id, plant_id = plant_id):
        item2plant = item2plant_model(item_id = item_id, plant_id = plant_id, amount = 1)
        item2plant.save()
    else:
        item2plant = item2plant_model.objects.get(item_id = item_id, plant_id = plant_id)
        item2plant.amount = item2plant.amount+1
        item2plant.save()
    if plant_id != request.POST.get('plant_id'):
        return Response(status=status.HTTP_201_CREATED, data = {'plant_id':plant_id})

@api_view(['Post'])
def user_login(request):
    return Response('login',status=status.HTTP_200_OK)

@api_view(['Post'])
def user_logout(request):
    return Response('logout',status=status.HTTP_200_OK)

@api_view(['Post'])
def user_create(request):
    return Response('user_created',status=status.HTTP_200_OK)




   