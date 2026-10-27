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
from django.core.exceptions import ValidationError
from nodule.models import TestUser

# Create your views here.
# class UserView(CreateModelMixin,RetrieveModelMixin,GenericViewSet):
#     serializer_class=serializers.UserSerializer
#     def retrieve(self,request):

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ResetPassword(request):
    current_password=request.data.get("current_password")
    new_password=request.data.get("new_password")
    re_new_password=request.data.get("re_new_password")
    user=request.user
    #The test user is shared, so its password can not be changed
    if user.username=="TestUser" or TestUser.objects.filter(user=user).exists():
        return Response({'error': 'As a test user you can not change the password', 'codes': ['test_user']}, status=status.HTTP_403_FORBIDDEN)
    if not current_password or not new_password or not re_new_password:
        return Response({'error': 'All fields are required', 'codes': ['required']}, status=status.HTTP_400_BAD_REQUEST)
    if not user.check_password(current_password):
        return Response({'error': 'The current password is not correct', 'codes': ['wrong_password']}, status=status.HTTP_400_BAD_REQUEST)
    if new_password != re_new_password:
        return Response({'error': 'Passwords do not match', 'codes': ['password_mismatch']}, status=status.HTTP_400_BAD_REQUEST)
    if new_password == current_password:
        return Response({'error': 'The new password must be different from the current one', 'codes': ['same_password']}, status=status.HTTP_400_BAD_REQUEST)
    #Passing the user enables the similarity validator; codes let the frontend translate the messages
    try:
        validate_password(new_password, user)
    except ValidationError as e:
        return Response({'error': ' '.join(e.messages), 'codes': [error.code for error in e.error_list]}, status=status.HTTP_400_BAD_REQUEST)
    user.set_password(new_password)
    user.save()
    return Response({'detail': 'The password has been set correctly'}, status=status.HTTP_200_OK)
