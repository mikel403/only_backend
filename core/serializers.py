from djoser.serializers import UserSerializer as BaseUserSerializer, UserCreateSerializer as BaseUserCreateSerializer
from rest_framework import serializers

class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        fields = ['id', 'username', 'password',
                  'email', 'first_name', 'last_name']


class UserSerializer(BaseUserSerializer):
    is_physician = serializers.SerializerMethodField()
    class Meta(BaseUserSerializer.Meta):
        fields = ['id', 'username', 'email', 'first_name', 'last_name','is_physician']
        extra_kwargs = {
            'username': {'required': True, 'allow_blank': False},
        }
    def get_is_physician(self, obj):
        # Si tienes OneToOne Physician(user=...)
        return hasattr(obj, "physicist")