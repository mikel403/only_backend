from email.headerregistry import ContentTypeHeader
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation


# Create your models here.
# class UserManager(models.Manager):
#     def get_queryset(self):
#         return super(UserManager, self).get_queryset().select_related()


    # class Meta:
    #     ordering= ["user__first name", "user__last name"]


class Nodule(models.Model):
    name=models.CharField(max_length=255,default="nodulo prueba")
    image=models.ImageField(
        upload_to="nodule/images",
        null=True)
    full_image=models.ImageField(
        upload_to="full_nodule/images",
        null=True)
    new=models.CharField(max_length=255,null=True)


class Description(models.Model):

    content_type=models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id=models.PositiveIntegerField()
    content_object=GenericForeignKey("content_type","object_id")
    # physicist=models.ForeignKey(Physicist,on_delete=models.CASCADE, related_name="descriptions")

    nodule=models.ForeignKey(Nodule,on_delete=models.CASCADE, related_name="descriptions")
    SHAPE_CHOICES=[
        ("oval", "oval"),
        ("round","round"),
        # ("lobulated","lobulated"),
        ("irregular","irregular"),
    ]
    MARGIN_CHOICES=[
        ("circumscribed", "circumscribed"),
        ("microlobulated", "microlobulated"),
        ("indistinct","indistinct"),
        ("angulated","angulated"),
        ("spiculated","spiculated"),
    ]
    ORIENTATION_CHOICES=[
        ("parallel", "parallel"),
        ("no orientation","no orientation"),
        ("not parallel","not parallel"),
    ]
    ECHOGENICITY_CHOICES=[
        ("anechoic", "anechoic"),
        ("isoechoic", "isoechoic"),
        ("hyperechoic", "hyperechoic"),
        ("hypoechoic","hypoechoic"),
        ("heterogeneous", "heterogeneous"),
        ("complex cystic and solid", "complex cystic and solid"),
    ]
    POSTERIOR_CHOICES=[
        ("enhancement", "enhancement"),
        ("no features","no features"),
        ("shadowing","shadowing"),
        ("combined pattern","combined pattern"),
    ]

    # HALO_CHOICES=[
    #     ("no halo", "no halo"),
    #     ("halo","halo"),
    # ]

    CALCIFICATION_CHOICES=[
        ("no calcifications","no calcifications"),
        ("calcifications", "calcifications"),

    ]

    SUGGESTIVITY_CHOICES=[
        ("simple cyst","simple cyst"),
        ("clustered microcysts", "clustered microcysts"),
        ("complicated cyst","complicated cyst"),
        ("mass in skin", "mass in skin"),
        ("mass on skin", "mass on skin"),
        ("lymph node","lymph node"),
        ("postsurgical fluid collection","postsurgical fluid collection"),
        ("fat necrosis","fat necrosis"),

    ]

    BIRADS_CHOICES=[
        ("2", "2"),
        ("3","3"),
        ("4A", "4A"),
        ("4B", "4B"),
        ("4C", "4C"),
        ("5","5")
    ]

    shape=models.CharField(max_length=20,choices=SHAPE_CHOICES,null=True)
    margin=models.CharField(max_length=20,choices=MARGIN_CHOICES,null=True)
    orientation=models.CharField(max_length=20,choices=ORIENTATION_CHOICES,null=True)
    echogenicity=models.CharField(max_length=30,choices=ECHOGENICITY_CHOICES,null=True)
    posterior=models.CharField(max_length=20,choices=POSTERIOR_CHOICES,null=True)
    # halo=models.CharField(max_length=20,choices=HALO_CHOICES,null=True)
    calcification=models.CharField(max_length=20,choices=CALCIFICATION_CHOICES,null=True)
    suggestivity=models.CharField(max_length=50,choices=SUGGESTIVITY_CHOICES,null=True)
    birads=models.CharField(max_length=20,choices=BIRADS_CHOICES,null=True)

    
    # physicist=models.CharField(max_length=255,default="doctor prueba")
    # descriptors=models.ManyToManyField(Descriptors)
    time=models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]
    
class Physicist(models.Model):
    user=models.OneToOneField(settings.AUTH_USER_MODEL,primary_key=True,on_delete=models.CASCADE)
    experience=models.PositiveIntegerField()
    def __str__(self) -> str:
        return f'{self.user.first_name} {self.user.last_name}'
    def email(self) -> str:
        return self.user.email
    def first_name(self) -> str:
        return self.user.first_name
    def username(self) -> str:
        return self.user.username
    def last_name(self) -> str:
        return self.user.last_name
    
    descriptions = GenericRelation(Description,related_query_name="physicist")

class AI(models.Model):
    name=models.CharField(max_length=255)
    descriptions = GenericRelation(Description,related_query_name="AI")

class TestUser(models.Model):
    user=models.OneToOneField(settings.AUTH_USER_MODEL,primary_key=True,on_delete=models.CASCADE)
    descriptions = GenericRelation(Description,related_query_name="TestUser")
    def username(self) -> str:
        return self.user.username
    