from djoser.serializers import UserSerializer as BaseUserSerializer, UserCreateSerializer as BaseUserCreateSerializer
from rest_framework import serializers

#Usernames used as keywords in the API urls (e.g. /api/Overall/statistics)
RESERVED_USERNAMES = {"overall"}

class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        fields = ['id', 'username', 'password',
                  'email', 'first_name', 'last_name']
    def validate_username(self, value):
        if value.lower() in RESERVED_USERNAMES:
            raise serializers.ValidationError("This username is reserved, please choose another one")
        return value


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