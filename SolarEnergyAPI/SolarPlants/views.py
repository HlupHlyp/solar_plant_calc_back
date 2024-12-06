from django.shortcuts import render
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status
from SolarPlants.serializers import ItemSerializer, ItemPartialSerializer, PlantSerializer, PlantPartialSerializer, Item2PlantSerializer, PlantStatusSerializer, UserSerializer, FreeItemPartialSerializer, PlantFinishSerializer
from SolarPlants.models import item_model, plant_model, item2plant_model, CustomUser
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import api_view, authentication_classes, permission_classes, action
from SolarPlants.minio import add_pic, del_pic
import datetime
from django.contrib.auth.models import User
from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from SolarPlants.permissions import IsManager, IsAuthorised
from django.conf import settings
import redis, uuid
from drf_yasg import openapi
from rest_framework.decorators import parser_classes
from rest_framework.parsers import MultiPartParser, FormParser

# Connect to our Redis instance
session_storage = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

def get_user(request):
    if not request.COOKIES.get('session_id'):
        return False
    session_id = request.COOKIES['session_id']
    if session_storage.get(session_id) is not None:
        email = session_storage.get(session_id).decode('utf-8')
        return CustomUser.objects.filter(email=email).first()
    return False

class UserViewSet(ModelViewSet):
    """Класс, описывающий методы работы с пользователями
    Осуществляет связь с таблицей пользователей в базе данных
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    model_class = CustomUser

    def create(self, request):
        """
        Функция регистрации новых пользователей
        Если пользователя c указанным в request email ещё нет, в БД будет добавлен новый пользователь.
        """
        if self.model_class.objects.filter(email=request.data['email']).exists():
            return Response({'status': 'Exist'}, status=400)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            print(serializer.data)
            self.model_class.objects.create_user(email=serializer.data['email'],
                                     password=serializer.data['password'],
                                     is_superuser=serializer.data['is_superuser'],
                                     is_staff=serializer.data['is_staff'])
            return Response({'status': 'Success'}, status=200)
        return Response({'status': 'Error', 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
def method_permission_classes(classes):
    def decorator(func):
        def decorated_func(self, *args, **kwargs):
            self.permission_classes = classes        
            self.check_permissions(self.request)
            return func(self, *args, **kwargs)
        return decorated_func
    return decorator

class ItemList(APIView):
    model_class = item_model
    serializer_class = ItemSerializer
    partial_serializer_class = ItemPartialSerializer
    parser_classes=[MultiPartParser]
    

    @swagger_auto_schema(method='get', responses = {status.HTTP_200_OK:serializer_class}, 
                         manual_parameters=[openapi.Parameter(name="search_request", in_=openapi.IN_QUERY, type=openapi.TYPE_STRING,required=True)], 
                         operation_description="Item list information")
    @action(detail=False, methods=['GET'])
    def get(self, request, format=None):
        plants = None
        plant_id = 0
        amount = 0
        search_request = request.GET.get('search_request','')
        items = (item_model.objects.filter(item_name__icontains=search_request, item_status = 'active') 
        or item_model.objects.filter(long_description__icontains=search_request, item_status = 'active') 
        or item_model.objects.filter(short_description__icontains=search_request, item_status = 'active'))
        serializer = self.serializer_class(items, many=True)
        if get_user(request) is not None:
            plants = plant_model.objects.filter(creator = get_user(request), plant_status = "draft").values()
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
    

    @swagger_auto_schema(request_body=partial_serializer_class, responses = {status.HTTP_201_CREATED:serializer_class, status.HTTP_400_BAD_REQUEST:"wrong params"},
                         operation_description="Uploading new item")
    @method_permission_classes((IsManager,))
    def post(self, request, format=None):
        serializer = self.partial_serializer_class(data=request.data)
        if serializer.is_valid():
            data = serializer.data
            data["item_status"] = 'active'
            end_serializer = self.serializer_class(data=data)
            if end_serializer.is_valid():
                item = end_serializer.save()
                item.save()
                return Response(end_serializer.data, status=status.HTTP_201_CREATED)
            return Response(end_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Добавляет новую акцию

class ItemDetail(APIView):
    model_class = item_model
    serializer_class = ItemSerializer
    partial_serializer_class = ItemPartialSerializer
    free_partial_serializer_class = FreeItemPartialSerializer
    parser_classes=[MultiPartParser]


    @swagger_auto_schema(method='get', responses = {status.HTTP_404_NOT_FOUND: "item isn't found", status.HTTP_200_OK:serializer_class}, 
                         operation_description="Item detail information")
    @action(detail=True, methods=['GET'])
    def get(self, request, item_id, format=None):
        item = get_object_or_404(self.model_class, item_id=item_id)
        serializer = self.serializer_class(item)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

    @swagger_auto_schema(request_body=free_partial_serializer_class, responses = {status.HTTP_404_NOT_FOUND: "item isn't found", status.HTTP_200_OK:serializer_class,
                            status.HTTP_400_BAD_REQUEST: "wrong params"}, 
                            operation_description="Changing of item") 
    @method_permission_classes((IsManager,))
    def put(self, request, item_id, format=None):
        item = get_object_or_404(self.model_class, item_id=item_id)
        serializer = self.serializer_class(item, data=request.data, partial=True)
        if serializer.is_valid():
            item = serializer.save()
            item.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

    @swagger_auto_schema(responses = {status.HTTP_404_NOT_FOUND: "item isn't found", status.HTTP_204_NO_CONTENT:"success"},
                         operation_description="Deletion of item") 
    @method_permission_classes((IsManager,))
    def delete(self, request, item_id, format=None):
        item = get_object_or_404(self.model_class, item_id=item_id)
        del_pic(item_id)
        item.item_status = "deleted"
        item.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

    @swagger_auto_schema(responses = {status.HTTP_404_NOT_FOUND: "item is not found", status.HTTP_200_OK:serializer_class, 
                                                                  status.HTTP_400_BAD_REQUEST:"wrong params"}, 
                        manual_parameters=[openapi.Parameter(name="pic", in_=openapi.IN_FORM, type=openapi.TYPE_FILE,required=True)],
                        operation_description="Uploading of item img") 
    @method_permission_classes((IsManager,))
    def post(self, request, item_id, format=None):
        item = get_object_or_404(self.model_class, item_id=item_id)
        serializer = self.serializer_class(item, data=request.data, partial=True)
        if serializer.is_valid():
            pic = request.FILES.get("pic")
            pic_result = add_pic(item, pic)
            if 'error' in pic_result.data:    
                return pic_result
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class item2plant(APIView):
    model_class = item2plant_model
    serializer_class = Item2PlantSerializer
    parser_classes=[MultiPartParser]


    @swagger_auto_schema(responses = {status.HTTP_400_BAD_REQUEST: "wrong params", status.HTTP_404_NOT_FOUND: "no such plant", 
                                                                        status.HTTP_403_FORBIDDEN:"you aren't creator", status.HTTP_204_NO_CONTENT:"success", 
                                                                        status.HTTP_406_NOT_ACCEPTABLE:"plant isn't draft", status.HTTP_400_BAD_REQUEST: "no relation"}, 
                            manual_parameters=[openapi.Parameter(name="plant_id", in_=openapi.IN_FORM, type=openapi.TYPE_INTEGER,required=True), 
                                               openapi.Parameter(name="item_id", in_=openapi.IN_FORM, type=openapi.TYPE_INTEGER,required=True)],
                            operation_description="Deletion item from plant", )   
    @method_permission_classes((IsAuthorised,)) #✔
    def delete(self, request, format=None):
        item_id = request.POST['item_id']
        plant_id = request.POST['plant_id']
        plant = get_object_or_404(plant_model,plant_id=plant_id)
        if plant.creator != get_user(request):
            return Response("This plant doesn't belong to you", status=status.HTTP_403_FORBIDDEN)
        if plant.plant_status != 'draft':
            return Response("Status of this plant isn't draft", status=status.HTTP_406_NOT_ACCEPTABLE)
        if self.model_class.objects.filter(item_id = item_id, plant_id = plant_id):
            self.model_class.objects.filter(item_id = item_id, plant_id = plant_id).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


    @swagger_auto_schema(responses = {status.HTTP_400_BAD_REQUEST: "wrong params", status.HTTP_404_NOT_FOUND: "no such plant", 
                                                                        status.HTTP_403_FORBIDDEN:"you aren't creator", status.HTTP_206_PARTIAL_CONTENT:serializer_class, 
                                                                        status.HTTP_406_NOT_ACCEPTABLE:"this plant isn't draft"}, 
                            operation_description="Changing item amount in plant", manual_parameters=[openapi.Parameter(name="plant_id", in_=openapi.IN_QUERY, type=openapi.TYPE_INTEGER,required=True), 
                                               openapi.Parameter(name="item_id", in_=openapi.IN_QUERY, type=openapi.TYPE_INTEGER,required=True),
                                               openapi.Parameter(name="amount", in_=openapi.IN_FORM, type=openapi.TYPE_INTEGER,required=True)])   
    @method_permission_classes((IsAuthorised,)) #✔
    def put(self, request, format=None):
        item_id = request.query_params.get('item_id')
        plant_id = request.query_params.get('plant_id')
        amount = request.POST['amount']
        plant = get_object_or_404(plant_model, plant_id=plant_id)
        if plant.creator != get_user(request):
            return Response("This plant doesn't belong to you", status=status.HTTP_403_FORBIDDEN)
        if plant.plant_status != 'draft':
            return Response("Status of this plant isn't draft", status=status.HTTP_406_NOT_ACCEPTABLE)
        item2plant = get_object_or_404(self.model_class, item_id=item_id, plant_id=plant_id)
        item2plant.amount = amount
        serializer = self.serializer_class(item2plant, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_206_PARTIAL_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PlantList(APIView):
    model_class = plant_model
    serializer_class = PlantSerializer


    @swagger_auto_schema(method = 'get', responses = {status.HTTP_400_BAD_REQUEST: "wrong params", status.HTTP_200_OK:serializer_class}, 
                         manual_parameters=[openapi.Parameter(name="plant_status", in_=openapi.IN_QUERY, type=openapi.TYPE_STRING,required=False), 
                                            openapi.Parameter(name="bottom_date", in_=openapi.IN_QUERY, type=openapi.TYPE_STRING, required=False),
                                            openapi.Parameter(name="top_date", in_=openapi.IN_QUERY, type=openapi.TYPE_STRING, required=False)], 
                         operation_description="Plant list information")   
    @action(detail=False, methods=['GET'])
    @method_permission_classes((IsAuthorised,)) #✔
    def get(self, request, format=None):
        plants = []
        req_plant_status = request.query_params.get("plant_status")
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
            & plant_model.objects.filter(forming_date__range=[bottom_date, top_date]) & plant_model.objects.filter(creator=get_user(request)))
        else:
            plants = ((plant_model.objects.filter(plant_status = "completed") | plant_model.objects.filter(plant_status = "formed") 
            | plant_model.objects.filter(plant_status = "rejected")) & plant_model.objects.filter(forming_date__range=[bottom_date, top_date]) 
            & plant_model.objects.filter(creator=get_user(request)))
            plants = plant_model.objects.filter(forming_date__range=[bottom_date, top_date])
        if not plants:
            return Response("No suitable ones" ,status.HTTP_200_OK)
        else:
            serializer = self.serializer_class(plants, many=True)
            return Response(serializer.data, status.HTTP_200_OK)


class PlantDetail(APIView):
    model_class = plant_model
    serializer_class = PlantSerializer
    partial_serializer_class = PlantPartialSerializer
    parser_classes=[MultiPartParser]


    @swagger_auto_schema(method = 'get', responses = {status.HTTP_404_NOT_FOUND: "no such plant", status.HTTP_403_FORBIDDEN:"it's not your plant", 
                                                      status.HTTP_200_OK:serializer_class}, 
                         operation_description="Plant detail information")   
    @action(detail=True, methods=['GET'])
    @method_permission_classes((IsAuthorised,)) #✔
    def get(self, request, plant_id, format=None):
        plant = get_object_or_404(plant_model, plant_id=plant_id)
        if plant.creator != get_user(request) and not get_user(request).is_staff: 
            return Response("This plant doesn't available for you", status=status.HTTP_403_FORBIDDEN)
        items = []
        items2plant = item2plant_model.objects.filter(plant_id = plant_id).values()
        for item2plant in items2plant:
            item = item_model.objects.get(item_id = int(item2plant['item_id']))
            items.append({'item_name':item.item_name, 'img_link':item.img_link, 'amount':item2plant["amount"], 
                          'item_cost':item.item_cost,'sum_cost':item.item_cost*item2plant["amount"]})
        data = {"plant":self.serializer_class(plant).data, "items":items}
        return Response(data, status = status.HTTP_200_OK)


    @swagger_auto_schema(request_body = partial_serializer_class, responses = {status.HTTP_404_NOT_FOUND: "no such plant", status.HTTP_403_FORBIDDEN:"it's not your plant", 
                                                      status.HTTP_206_PARTIAL_CONTENT:serializer_class, status.HTTP_400_BAD_REQUEST:"wrong params"}, 
                         operation_description="Changing of plant information")   
    @method_permission_classes((IsAuthorised,)) #✔
    def put(self, request, plant_id, format=None):
        plant = get_object_or_404(self.model_class, plant_id=plant_id)
        if plant.creator != get_user(request) or not get_user(request).is_staff: 
            return Response("This plant doesn't available for you", status=status.HTTP_403_FORBIDDEN)
        serializer = self.partial_serializer_class(plant, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status = status.HTTP_206_PARTIAL_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    @swagger_auto_schema(responses = {status.HTTP_404_NOT_FOUND: "no such plant", status.HTTP_204_NO_CONTENT:"success", 
                                      status.HTTP_400_BAD_REQUEST:"wrong params"}, 
                         operation_description="Deletion of plant")   
    @method_permission_classes((IsAuthorised,)) #✔
    def delete(self, request, plant_id, format=None):
        plant = get_object_or_404(plant_model, plant_id = plant_id)
        if plant.creator != get_user(request): 
            return Response("This plant doesn't available for you", status=status.HTTP_400_BAD_REQUEST)
        plant.plant_status = "deleted"
        plant.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


@swagger_auto_schema(method='put', responses = {status.HTTP_404_NOT_FOUND: "no such plant", status.HTTP_206_PARTIAL_CONTENT:"success", 
                                    status.HTTP_403_FORBIDDEN:"it's not your plant", status.HTTP_400_BAD_REQUEST:"plsnt is already formed"}, 
                         operation_description="Plant forming")   
@api_view(['Put'])
@permission_classes([IsAuthorised]) #✔
def plant_forming(request, plant_id, format=None):
    plant = get_object_or_404(plant_model, plant_id = plant_id)
    if plant.creator != get_user(request): 
        return Response("This plant doesn't available for you", status=status.HTTP_403_FORBIDDEN)
    if plant.plant_status == 'draft':
        plant.plant_status = "formed"
        plant.forming_date = datetime.datetime.now()
        plant.save()
        return Response(status=status.HTTP_206_PARTIAL_CONTENT)
    return Response(status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='put', responses = {status.HTTP_404_NOT_FOUND: "no such plant", status.HTTP_206_PARTIAL_CONTENT:"success", 
                                    status.HTTP_403_FORBIDDEN:"it's not your plant", status.HTTP_400_BAD_REQUEST:"wrong params"}, 
                         operation_description="Plant finishing", 
                         manual_parameters=[openapi.Parameter(name="plant_status", in_=openapi.IN_FORM, type=openapi.TYPE_STRING,required=True)] )  
@api_view(['Put'])
@permission_classes([IsManager]) #✔
@parser_classes([MultiPartParser])
def plant_finishing(request, plant_id, format=None):
    plant_status = request.POST.get("plant_status")
    plant = get_object_or_404(plant_model, plant_id = plant_id)
    if plant_status in ["rejected", "completed"] and plant.plant_status == 'formed':
        data = calculating(plant_id)
        plant.plant_status = plant_status
        if plant_status == "completed":
            plant.saving = data["saving"]
            plant.generation = data["generation"]
            plant.finishing_date = datetime.datetime.now()
            plant.moderator = get_user(request)
        plant.save()
        return Response(status=status.HTTP_206_PARTIAL_CONTENT)
    return Response(status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='post', responses = {status.HTTP_201_CREATED:"plant_id", status.HTTP_404_NOT_FOUND: "no such item"}, 
                     operation_description="Adding to plant")
@permission_classes([IsAuthorised])
@api_view(['Post'])
def add2plant(request, item_id, format=None):
    plant_id = None
    plant = None
    f = False
    if not plant_model.objects.filter(creator = get_user(request), plant_status = 'draft').values(): f = True  
    if f:
        if not plant_model.objects.filter(creator = get_user(request), plant_status = 'draft').values():
            plant = plant_model.objects.create(creator = get_user(request))
            plant.save()
        else:
            plant = plant_model.objects.get(creator = get_user(request), plant_status = 'draft')
        plant_id = plant.plant_id
    else:
        plant_id = plant_model.objects.get(creator = get_user(request), plant_status = 'draft').plant_id

    get_object_or_404(item_model, item_id=item_id)

    if not item2plant_model.objects.filter(item_id = item_id, plant_id = plant_id):
        item2plant = item2plant_model(item_id = item_id, plant_id = plant_id, amount = 1)
        item2plant.save()
    else:
        item2plant = item2plant_model.objects.get(item_id = item_id, plant_id = plant_id)
        item2plant.amount = item2plant.amount+1
        item2plant.save()
    return Response(status=status.HTTP_201_CREATED, data = {'plant_id':plant_id})


@swagger_auto_schema(method='post', manual_parameters=[openapi.Parameter(name="email", in_=openapi.IN_FORM, type=openapi.TYPE_STRING,required=True), 
                                            openapi.Parameter(name="password", in_=openapi.IN_FORM, type=openapi.TYPE_STRING, required=True)])
@permission_classes([AllowAny])
@api_view(['Post'])    
@csrf_exempt
@parser_classes([MultiPartParser])
def login_user(request):
    if not get_user(request):
        username = request.POST.get("email")
        password = request.POST.get("password")
        print(username, password)
        user = authenticate(request, email=username, password=password)
        print(user)
        if user is not None:
            random_key = str(uuid.uuid4())
            session_storage.set(random_key, username)

            response = HttpResponse("{'status': 'ok'}")
            user = CustomUser.objects.filter(email = username).first()
            user.last_login = datetime.datetime.now()
            user.save()
            response.set_cookie("session_id", random_key)

            return response
        else:
            return HttpResponse("{'status': 'error', 'error': 'login failed'}")
    return HttpResponse("{'status': 'error', 'error': 'You have already authorized'}")

@swagger_auto_schema(method='post', request_body=UserSerializer, responses = {status.HTTP_404_NOT_FOUND: "no such plant", status.HTTP_200_OK:"success", 
                                    status.HTTP_400_BAD_REQUEST:"exists or wrong params"}, 
                         operation_description="User creation", )  
@permission_classes([AllowAny])
@api_view(['Post'])
@csrf_exempt
@parser_classes([MultiPartParser])
def create_user(request):
        if CustomUser.objects.filter(email=request.data['email']).exists():
            return Response({'status': 'Exist'}, status=400)
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            CustomUser.objects.create_user(email=serializer.data['email'],
                                     password=serializer.data['password'],
                                     is_superuser=serializer.data['is_superuser'],
                                     is_staff=serializer.data['is_staff'])
            return Response({'status': 'Success'}, status=200)
        return Response({'status': 'Error', 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@permission_classes([IsAuthorised])
@api_view(['Put'])
def change_user(request):
    if not request.session_id:
        return Response({'status': 'Error', 'error': "no login"}, status=status.HTTP_403_FORBIDDEN)
    user = get_user(request)
    serializer = UserSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save
        return Response({'status': 'Success'}, status=206)
    return Response({'status': 'Error', 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='post', responses = {status.HTTP_204_NO_CONTENT: "success", 
                                    status.HTTP_403_FORBIDDEN:"you aren't authorised"})
@permission_classes([IsAuthorised])
@api_view(['Post'])
def logout_user(request):
    session_id = request.COOKIES.get("session_id")
    if not session_id:
        return Response(status=status.HTTP_403_FORBIDDEN)
    if session_storage.exists(session_id):
        session_storage.delete(session_id)
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie("session_id")
        return response
    return Response(status=status.HTTP_403_FORBIDDEN)

def calculating(plant_id):
    ratio = 5 + 7*0.7
    saving = 0
    generation = 0
    sets = item2plant_model.objects.filter(plant_id = plant_id).values()
    for set in sets:
        item_id = set["item_id"]
        item = item_model.objects.get(item_id = item_id)
        if item.item_type == 'battery':
            saving += float(item.item_capacity) * float(item.item_voltage) * set["amount"]
        else:
            generation += float(item.item_power) * ratio
    return {"generation":generation, "saving":saving}

        
