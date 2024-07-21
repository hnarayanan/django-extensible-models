from django.contrib import admin
from django.contrib.contenttypes.models import ContentType

from .models import ExtensionSchema
from .utils import get_tenant_field
from .forms import ExtensibleModelFormMixin


class ExtensibleModelAdminMixin:
    """
    Mixin to extend admin functionalities for models using the ExtensionSchema.
    """

    def get_form(self, request, obj=None, **kwargs):
        """
        Overrides get_form to include ExtensibleModelFormMixin dynamically.
        """
        form = super().get_form(request, obj, **kwargs)
        # Ensure the dynamically generated form class name is unique
        form_class_name = f"ExtensibleModelAdminForm_{self.model.__name__}"
        return type(form_class_name, (ExtensibleModelFormMixin, form), {})

    def get_fieldsets(self, request, obj=None):
        """
        Overrides get_fieldsets to include extended fields from the extension schema.
        """
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
        """
        Overrides get_readonly_fields to include schema_version if an object is provided.
        """
        readonly_fields = super().get_readonly_fields(request, obj)
        if obj:
            extension_schema = self._get_extension_schema(obj)
            if extension_schema:
                readonly_fields = list(readonly_fields) + ["schema_version"]
        return readonly_fields

    def _get_extension_schema(self, obj):
        """
        Retrieves the latest extension schema for the given object.
        """
        tenant = self._get_tenant(obj)
        if not tenant:
            return None

        content_type = ContentType.objects.get_for_model(obj.__class__)
        return (
            ExtensionSchema.objects.filter(
                content_type=content_type, **{get_tenant_field(): tenant}
            )
            .order_by("-version")
            .first()
        )

    def _get_tenant(self, obj):
        """
        Retrieves the tenant for the given object using the configured tenant field.
        """
        tenant_field = get_tenant_field()
        return getattr(obj, tenant_field, None)

    def save_model(self, request, obj, form, change):
        """
        Overrides save_model to set the schema version for new objects.
        """
        if not change:  # New object
            tenant = self._get_tenant(obj)
            if tenant:
                extension_schema = self._get_extension_schema(obj)
                if extension_schema:
                    obj.schema_version = extension_schema.version
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        """
        Overrides save_related to save extended fields.
        """
        super().save_related(request, form, formsets, change)
        if hasattr(form, "cleaned_data") and "extended_fields" in form.cleaned_data:
            form.instance.extended_fields = form.cleaned_data["extended_fields"]
            form.instance.save()


class ExtensionSchemaAdmin(admin.ModelAdmin):
    """
    Admin class for ExtensionSchema model.
    """

    list_display = ("content_type", get_tenant_field(), "version", "created_at")
    list_filter = ("content_type", get_tenant_field())
    readonly_fields = ("version",)

    def save_model(self, request, obj, form, change):
        """
        Overrides save_model to automatically set the version number for new schemas.
        """
        tenant_field = get_tenant_field()
        if not change:  # New schema
            obj.version = (
                ExtensionSchema.objects.filter(
                    content_type=obj.content_type,
                    **{tenant_field: getattr(obj, tenant_field)},
                ).count()
                + 1
            )
        super().save_model(request, obj, form, change)


# Register the model with the admin site
admin.site.register(ExtensionSchema, ExtensionSchemaAdmin)
