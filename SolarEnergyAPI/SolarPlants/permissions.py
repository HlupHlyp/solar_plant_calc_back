from rest_framework import permissions
from SolarPlants.models import CustomUser
from django.conf import settings
import redis

session_storage = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        try:
            session_id = request.COOKIES['session_id']
            if session_id is None:
                return False
            email = session_storage.get(session_id).decode('utf-8')
        except:
            return False
        user = CustomUser.objects.filter(email=email).first()
        return user.is_staff

class IsAuthorised(permissions.BasePermission):
    def has_permission(self, request, view):
        try:
            session_id = request.COOKIES['session_id']
            if session_id is None:
                return False
            email = session_storage.get(session_id).decode('utf-8')
        except:
            return False
        user = CustomUser.objects.filter(email=email).first()
        return True