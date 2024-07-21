import jsonschema

from django.contrib import admin
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.forms import modelform_factory
from django.conf import settings

from .models import ExtensionSchema, get_tenant_model
from .forms import ExtensibleModelFormMixin


class ExtensibleModelAdminMixin:

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        return type("ExtensibleModelAdminForm", (ExtensibleModelFormMixin, form), {})

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if obj:
            extension_schema = self._get_extension_schema(obj)
            if extension_schema:
                extended_fields = list(
                    extension_schema.schema.get("properties", {}).keys()
                )
                fieldsets = list(fieldsets) + [
                    ("Extended Fields", {"fields": extended_fields})
                ]
        return fieldsets

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        if obj:
            extension_schema = self._get_extension_schema(obj)
            if extension_schema:
                readonly_fields = list(readonly_fields) + ["schema_version"]
        return readonly_fields

    def _get_extension_schema(self, obj):
        tenant = self._get_tenant(obj)
        if not tenant:
            return None

        content_type = ContentType.objects.get_for_model(obj.__class__)
        return (
            ExtensionSchema.objects.filter(content_type=content_type, tenant=tenant)
            .order_by("-version")
            .first()
        )

    def _get_tenant(self, obj):
        tenant_field = getattr(settings, "EXTENSIBLE_MODELS_TENANT_FIELD", "tenant")
        return getattr(obj, tenant_field, None)

    def save_model(self, request, obj, form, change):
        if not change:  # New object
            tenant = self._get_tenant(obj)
            if tenant:
                extension_schema = self._get_extension_schema(obj)
                if extension_schema:
                    obj.schema_version = extension_schema.version
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        if hasattr(form, "cleaned_data") and "extended_fields" in form.cleaned_data:
            form.instance.extended_fields = form.cleaned_data["extended_fields"]
            form.instance.save()


class ExtensionSchemaAdmin(admin.ModelAdmin):

    list_display = ("content_type", "tenant", "version", "created_at")
    list_filter = ("content_type", "tenant")
    readonly_fields = ("version",)

    def save_model(self, request, obj, form, change):
        if not change:  # New schema
            obj.version = (
                ExtensionSchema.objects.filter(
                    content_type=obj.content_type, tenant=obj.tenant
                ).count()
                + 1
            )
        super().save_model(request, obj, form, change)


