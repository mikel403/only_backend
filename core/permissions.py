from rest_framework.permissions import BasePermission, SAFE_METHODS
from nodule.models import TestUser


#The test account is shared, so it can browse the app but never save data
def is_test_user(user):
    return user.is_authenticated and (user.username=="TestUser" or TestUser.objects.filter(user=user).exists())


class ReadOnlyForTestUser(BasePermission):
    message = "As a test user you can not save any data"

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or not is_test_user(request.user)
