from django.conf import settings
from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from . import models


    
class PhysicistSerializer(serializers.ModelSerializer):
    
    class Meta:
        model=models.Physicist
        fields=["user_id","experience","profession"] 

    
    def create(self,validated_data):
        user_id=self.context["user_id"]
        return models.Physicist.objects.create(user_id=user_id, **validated_data)

class NodulePhysicistSerializer(serializers.ModelSerializer):
    new=serializers.StringRelatedField(read_only=True)
    full_image=serializers.ImageField(read_only=True)
    numDescriptions=serializers.IntegerField(read_only=True)
    numNodules=serializers.IntegerField(read_only=True)
    numNodules2Times=serializers.IntegerField(read_only=True)
    numNodulesDescribed=serializers.IntegerField(read_only=True)
    private_image_url = serializers.SerializerMethodField()
    private_full_image_url = serializers.SerializerMethodField()
    public_image_url = serializers.SerializerMethodField()
    public_full_image_url = serializers.SerializerMethodField()
    class Meta:
         model=models.Nodule
         fields=["id","name", "image","full_image","new","numDescriptions","numNodules","numNodules2Times","numNodulesDescribed","public_image_url","public_full_image_url","private_image_url","private_full_image_url"]
    def create(self,validated_data):
        new=self.context["new"]
        return models.Nodule.objects.create(new=new, **validated_data)
    def _abs(self, request, url: str) -> str:
        return request.build_absolute_uri(url) if request else url
    def get_public_image_url(self, obj):
        # Solo dataset público
        if obj.new is not None or not obj.image:
            return None
        base = settings.PUBLIC_MEDIA_BASE_URL.rstrip("/")
        return f"{base}{settings.PUBLIC_MEDIA_URL}{obj.image.name}"

    def get_public_full_image_url(self, obj):
        if obj.new is not None or not obj.full_image:
            return None
        base = settings.PUBLIC_MEDIA_BASE_URL.rstrip("/")
        return f"{base}{settings.PUBLIC_MEDIA_URL}{obj.full_image}"

    def get_private_image_url(self, obj):
        request = self.context.get("request")
        return self._abs(request, f"/api/nodules/{obj.pk}/image/")

    def get_private_full_image_url(self, obj):
        request = self.context.get("request")
        return self._abs(request, f"/api/nodules/{obj.pk}/full-image/")

class DescriptionSerializer(serializers.ModelSerializer):
    # physicist=PhysicistSerializer(read_only=True)
    nodule_id=serializers.IntegerField(read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    
    # physicist_id=serializers.IntegerField(read_only=True)
    class Meta:
        model=models.Description
        fields=["id","shape","margin","orientation","echogenicity","posterior","calcification","suggestivity","birads","nodule_id", "user_id"]        

    def create(self,validated_data):
        nodule_id =self.context["nodule_id"]
        user = self.context["request"].user
        
        
        return models.Description.objects.create(nodule_id=nodule_id,user=user, **validated_data)
    
# class DescriptionForNoduleSerializer(serializers.ModelSerializer):
#     class Meta:
#         model=models.Description
#         fields=["birads"]
class NoduleDescriptionsSerializer(serializers.ModelSerializer):
    # descriptions=DescriptionSerializer(many=True,read_only=True)
    # descriptions__birads=serializers.StringRelatedField(read_only=True)
    # descriptions__physicist_id=serializers.StringRelatedField(read_only=True)
    descriptions = serializers.SerializerMethodField()
    numDescriptions=serializers.IntegerField(read_only=True)
    numNodules2Times=serializers.IntegerField(read_only=True)
    numNodulesDescribed=serializers.IntegerField(read_only=True)
    
    private_image_url = serializers.SerializerMethodField()
    private_full_image_url = serializers.SerializerMethodField()
    public_image_url = serializers.SerializerMethodField()
    public_full_image_url = serializers.SerializerMethodField()
    class Meta:
        model=models.Nodule
        fields=["id","name", "image","new","descriptions","numDescriptions","numNodules2Times","numNodulesDescribed","public_image_url","public_full_image_url","private_image_url","private_full_image_url"]
    def _abs(self, request, url: str) -> str:
        return request.build_absolute_uri(url) if request else url
    def get_descriptions(self, instance: models.Nodule):
        request = self.context["request"]
        user = request.user
        # Filter the descriptions based on physicist ID (assuming 'physicist_id' is a field in Description model)
        descriptions = instance.descriptions.select_related("user").filter(user=user)
        
        # Serialize the filtered descriptions
        serializer = DescriptionSerializer(descriptions, many=True)
        return serializer.data
    def get_public_image_url(self, obj):
        # Solo dataset público
        if obj.new is not None or not obj.image:
            return None
        base = settings.PUBLIC_MEDIA_BASE_URL.rstrip("/")
        return f"{base}{settings.PUBLIC_MEDIA_URL}{obj.image}"

    def get_public_full_image_url(self, obj):
        if obj.new is not None or not obj.full_image:
            return None
        base = settings.PUBLIC_MEDIA_BASE_URL.rstrip("/")
        return f"{base}{settings.PUBLIC_MEDIA_URL}{obj.full_image}"

    def get_private_image_url(self, obj):
        request = self.context.get("request")
        return self._abs(request, f"/api/nodules/{obj.pk}/image/")

    def get_private_full_image_url(self, obj):
        request = self.context.get("request")
        return self._abs(request, f"/api/nodules/{obj.pk}/full-image/")