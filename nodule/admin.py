import csv

from django.contrib import admin
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from rangefilter.filters import DateRangeFilterBuilder

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


#Descriptor fields in the order they are shown and exported
DESCRIPTOR_FIELDS = ["shape", "margin", "orientation", "echogenicity", "posterior", "calcification", "suggestivity", "birads"]


class AuthorTypeFilter(admin.SimpleListFilter):
    title = "author type"
    parameter_name = "author_type"

    def lookups(self, request, model_admin):
        return [("radiologist", "Radiologist"), ("user", "Registered user"), ("test", "Test user"), ("ai", "AI")]

    def queryset(self, request, queryset):
        value = self.value()
        if value == "radiologist":
            return queryset.filter(user__physicist__isnull=False)
        if value == "user":
            return queryset.filter(user__isnull=False, user__physicist__isnull=True, user__testuser__isnull=True)
        if value == "test":
            return queryset.filter(user__testuser__isnull=False)
        if value == "ai":
            return queryset.filter(ai__isnull=False)
        return queryset


#Descriptions are scientific data: the admin can browse, filter and export them, but never add, edit or delete them
@admin.register(models.Description)
class DescriptionAdmin(admin.ModelAdmin):
    list_display = ["time", "author", "nodule_link", *DESCRIPTOR_FIELDS]
    #No date_hierarchy: it needs the MySQL time zone tables, while the range filter compares UTC values directly
    list_filter = [
        ("time", DateRangeFilterBuilder(title="date")),
        AuthorTypeFilter,
        ("user", admin.RelatedOnlyFieldListFilter),
        ("ai", admin.RelatedOnlyFieldListFilter),
        "birads",
    ]
    search_fields = ["user__username", "ai__name", "nodule__name"]
    list_select_related = ["user", "ai", "nodule"]
    ordering = ["-time"]
    list_per_page = 50
    actions = ["export_csv"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="author", ordering="user__username")
    def author(self, obj):
        return obj.user.username if obj.user else f"AI: {obj.ai.name}"

    @admin.display(description="nodule", ordering="nodule__name")
    def nodule_link(self, obj):
        url = reverse("admin:nodule_nodule_change", args=[obj.nodule_id])
        return format_html('<a href="{}">{}</a>', url, obj.nodule.name)

    @admin.action(description="Export selected descriptions to CSV")
    def export_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="descriptions.csv"'
        #The BOM lets Excel open the accents correctly
        response.write("﻿")
        writer = csv.writer(response)
        writer.writerow(["description_id", "time", "author", "author_type", "nodule_id", "nodule_name", "uploaded_by", *DESCRIPTOR_FIELDS])
        rows = queryset.select_related("user__physicist", "user__testuser", "ai", "nodule").order_by("time")
        for d in rows:
            if d.ai:
                author, author_type = d.ai.name, "ai"
            elif hasattr(d.user, "physicist"):
                author, author_type = d.user.username, "radiologist"
            elif hasattr(d.user, "testuser"):
                author, author_type = d.user.username, "test"
            else:
                author, author_type = d.user.username, "user"
            writer.writerow([
                d.id, timezone.localtime(d.time).strftime("%Y-%m-%d %H:%M:%S"), author, author_type,
                d.nodule_id, d.nodule.name, d.nodule.new or "",
                *[getattr(d, field) or "" for field in DESCRIPTOR_FIELDS],
            ])
        return response
