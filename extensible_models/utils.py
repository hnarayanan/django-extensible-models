from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def get_tenant_model():
    try:
        return apps.get_model(settings.EXTENSIBLE_MODELS_TENANT_MODEL)
    except AttributeError:
        raise ImproperlyConfigured(
            "EXTENSIBLE_MODELS_TENANT_MODEL must be set in settings"
        )


def get_tenant_field():
    try:
        return settings.EXTENSIBLE_MODELS_TENANT_FIELD
    except AttributeError:
        raise ImproperlyConfigured(
            "EXTENSIBLE_MODELS_TENANT_FIELD must be set in settings"
        )
