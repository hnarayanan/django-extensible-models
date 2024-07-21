from django.apps import AppConfig


class ExtensibleModelsConfig(AppConfig):

    name = "extensible_models"
    verbose_name = "Extensible Models"

    def ready(self):
        from .models import setup_extension_schema
        setup_extension_schema()
