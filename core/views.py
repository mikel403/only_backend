from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework.mixins import ListModelMixin, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin
# from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from . import serializers
from django.contrib.auth.password_validation import validate_password

# Create your views here.
# class UserView(CreateModelMixin,RetrieveModelMixin,GenericViewSet):
#     serializer_class=serializers.UserSerializer
#     def retrieve(self,request):

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ResetPassword(request):
    new_password=request.data["new_password"]
    re_new_password=request.data["re_new_password"]
    user=request.user
    if new_password != re_new_password:
        return Response({'error': 'Passwords do not match'}, status=status.HTTP_400_BAD_REQUEST)
    
    validate_password(new_password)
    user.set_password(new_password)
    user.save()
    return Response({'detail': 'The password has been set correctly'}, status=status.HTTP_200_OK)

