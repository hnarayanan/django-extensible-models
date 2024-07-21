from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings


class ExtensibleModelsConfig(AppConfig):
    name = "extensible_models"
    verbose_name = "Extensible Models"

    def ready(self):
        try:
            settings.EXTENSIBLE_MODELS_TENANT_MODEL
        except AttributeError:
            raise ImproperlyConfigured(
                "EXTENSIBLE_MODELS_TENANT_MODEL must be set in settings"
            )
