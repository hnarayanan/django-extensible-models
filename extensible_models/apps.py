from django.apps import AppConfig
from django.db import models
from django.db.models import UniqueConstraint
from django.utils.module_loading import import_string

from .utils import get_tenant_field, get_tenant_model


def setup_extension_schema():
    tenant_field_name = get_tenant_field()
    tenant_model = get_tenant_model()
    ExtensionSchema = import_string("extensible_models.models.ExtensionSchema")

    ExtensionSchema.add_to_class(
        tenant_field_name, models.ForeignKey(tenant_model, on_delete=models.CASCADE)
    )

    # Add unique constraints
    ExtensionSchema._meta.constraints.append(
        UniqueConstraint(
            fields=["content_type", "version", tenant_field_name],
            name=f"unique_content_type_{tenant_field_name}_version",
        )
    )


class ExtensibleModelsConfig(AppConfig):

    name = "extensible_models"
    verbose_name = "Extensible Models"

    def ready(self):
        setup_extension_schema()
