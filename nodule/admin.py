import csv

from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Count, IntegerField, Max, Min, OuterRef, Subquery, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from rangefilter.filters import DateRangeFilterBuilder

from . import models

# Register your models here.

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


#Activity of a user: their descriptions and the nodules they uploaded (Nodule.new stores the username)
def annotate_activity(queryset, user_path=""):
    uploaded = (
        models.Nodule.objects.filter(new=OuterRef(f"{user_path}username"))
        .values("new").annotate(total=Count("id")).values("total")
    )
    return queryset.annotate(
        num_descriptions=Count(f"{user_path}descriptions", distinct=True),
        num_nodules_described=Count(f"{user_path}descriptions__nodule", distinct=True),
        first_description=Min(f"{user_path}descriptions__time"),
        last_description=Max(f"{user_path}descriptions__time"),
        num_uploaded=Coalesce(Subquery(uploaded, output_field=IntegerField()), Value(0)),
    )


class ActivityColumns:
    """Columns shared by the user and radiologist lists; user_of(obj) returns the auth user"""

    def user_of(self, obj):
        return obj

    @admin.display(description="descriptions", ordering="num_descriptions")
    def descriptions_link(self, obj):
        url = reverse("admin:nodule_description_changelist") + f"?user__id__exact={self.user_of(obj).id}"
        return format_html('<a href="{}">{}</a>', url, obj.num_descriptions)

    @admin.display(description="nodules described", ordering="num_nodules_described")
    def nodules_described(self, obj):
        return obj.num_nodules_described

    @admin.display(description="first description", ordering="first_description")
    def first_description_time(self, obj):
        return obj.first_description

    @admin.display(description="last description", ordering="last_description")
    def last_description_time(self, obj):
        return obj.last_description

    @admin.display(description="uploaded nodules", ordering="num_uploaded")
    def uploaded_link(self, obj):
        url = reverse("admin:nodule_nodule_changelist") + f"?new__exact={self.user_of(obj).username}"
        return format_html('<a href="{}">{}</a>', url, obj.num_uploaded)


ACTIVITY_COLUMNS = ["descriptions_link", "nodules_described", "first_description_time", "last_description_time", "uploaded_link"]


class RoleFilter(admin.SimpleListFilter):
    title = "role"
    parameter_name = "role"

    def lookups(self, request, model_admin):
        return [("radiologist", "Radiologist"), ("user", "Registered user"), ("test", "Test user")]

    def queryset(self, request, queryset):
        value = self.value()
        if value == "radiologist":
            return queryset.filter(physicist__isnull=False)
        if value == "user":
            return queryset.filter(physicist__isnull=True, testuser__isnull=True)
        if value == "test":
            return queryset.filter(testuser__isnull=False)
        return queryset


User = get_user_model()
admin.site.unregister(User)


#Django's user admin (passwords, permissions...) plus the activity of each user in the platform
@admin.register(User)
class UserAdmin(ActivityColumns, BaseUserAdmin):
    list_display = ["username", "first_name", "last_name", "role", *ACTIVITY_COLUMNS, "is_staff"]
    list_filter = [RoleFilter, *BaseUserAdmin.list_filter]
    actions = ["make_radiologist"]

    def get_queryset(self, request):
        return annotate_activity(super().get_queryset(request)).select_related("physicist", "testuser")

    @admin.display(description="role")
    def role(self, obj):
        if hasattr(obj, "physicist"):
            return "Radiologist"
        if hasattr(obj, "testuser"):
            return "Test user"
        return "User"

    #Radiologists count in the expert panel; the shared test user can never be one
    @admin.action(description="Make the selected users radiologists")
    def make_radiologist(self, request, queryset):
        created = skipped = 0
        for user in queryset.select_related("physicist", "testuser"):
            if hasattr(user, "testuser") or user.username == "TestUser":
                skipped += 1
                continue
            _, is_new = models.Physicist.objects.get_or_create(user=user)
            created += is_new
        self.message_user(request, f"{created} user(s) are now radiologists.", messages.SUCCESS)
        if skipped:
            self.message_user(request, f"{skipped} test user(s) skipped.", messages.WARNING)


@admin.register(models.Physicist)
class PhysicistAdmin(ActivityColumns, admin.ModelAdmin):
    list_display = ["username", "first_name", "last_name", "experience", "profession", *ACTIVITY_COLUMNS]
    search_fields = ["user__username", "user__first_name", "user__last_name", "profession"]
    list_select_related = ["user"]
    #The user can not be changed once the radiologist exists
    readonly_fields = ["user"]

    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields if obj else []

    def get_queryset(self, request):
        return annotate_activity(super().get_queryset(request), user_path="user__")

    def user_of(self, obj):
        return obj.user
