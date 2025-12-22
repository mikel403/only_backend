from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from . import models



    
    
class PhysicistSerializer(serializers.ModelSerializer):
    
    class Meta:
        model=models.Physicist
        fields=["user_id","username","experience","first_name","last_name","email"] 

    
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
    class Meta:
         model=models.Nodule
         fields=["id","name", "image","full_image","new","numDescriptions","numNodules","numNodules2Times","numNodulesDescribed"]
    def create(self,validated_data):
        new=self.context["new"]
        return models.Nodule.objects.create(new=new, **validated_data)


class DescriptionSerializer(serializers.ModelSerializer):
    # physicist=PhysicistSerializer(read_only=True)
    nodule_id=serializers.IntegerField(read_only=True)
    object_id=serializers.IntegerField(read_only=True)
    content_type_id=serializers.IntegerField(read_only=True)
    # physicist_id=serializers.IntegerField(read_only=True)
    class Meta:
        model=models.Description
        fields=["id","shape","margin","orientation","echogenicity","posterior","calcification","suggestivity","birads","content_type_id","object_id","nodule_id"]        

    def create(self,validated_data):
        nodule_id =self.context["nodule_id"]
        user_id=self.context["user_id"]
        # content_type_id=ContentType.objects.get_for_model(models.Physicist).id
        content_type_id = self.context.get("content_type_id")  # Por defecto, Physicist
        
        return models.Description.objects.create(nodule_id=nodule_id,content_type_id=content_type_id,object_id=user_id, **validated_data)
    
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
    class Meta:
        model=models.Nodule
        fields=["id","name", "image","new","descriptions","numDescriptions","numNodules2Times","numNodulesDescribed"]

    def get_descriptions(self, instance: models.Nodule):
        # Filter the descriptions based on physicist ID (assuming 'physicist_id' is a field in Description model)
        descriptions = instance.descriptions.filter(physicist__user_id=self.context["request"].user.id)
        
        # Serialize the filtered descriptions
        serializer = DescriptionSerializer(descriptions, many=True)
        return serializer.data