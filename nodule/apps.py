from django.apps import AppConfig


class NoduleConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "nodule"

    def ready(self):
        from . import signals  # noqa: F401
