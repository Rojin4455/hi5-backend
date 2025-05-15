from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import viewsets
from .models import Notification
from .serializers import NotificationSerializer
from rest_framework.views import APIView
from rest_framework import status

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer


class NotificatioStatus(APIView):
    def patch(self, request, id):

        status = request.data.get('is_read')
        try:
            notification = Notification.objects.get(id=id)
            notification.save()
        except Notification.DoesNotExist:
            return Response({"message":"notification is not found"}, status=status.HTTP_404_NOT_FOUND)
            
        print(status, id)
        return Response()

