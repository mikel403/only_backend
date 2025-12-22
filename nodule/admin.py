from django.contrib import admin
from . import models

# Register your models here.
@admin.register(models.Physicist)
class PhysicistAdmin(admin.ModelAdmin):
    list_display=["username","experience"]

@admin.register(models.TestUser)
class TestUserAdmin(admin.ModelAdmin):
    list_display=["username"]

@admin.register(models.AI)
class AIAdmin(admin.ModelAdmin):
    list_display=["name"]



admin.site.register(models.Nodule)
# admin.site.register(models.Physicist)