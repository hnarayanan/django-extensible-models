from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldError

from .models import ExtensionSchema
from .utils import get_tenant_field


class ExtensibleModelAdminMixin:
    def get_fieldsets(self, request, obj=None):
        print("get_fieldsets called in ExtensibleModelAdminMixin")
        if not hasattr(self, "_cached_fieldsets"):
            original_fieldsets = super().get_fieldsets(request, obj)
            self._cached_fieldsets = self._get_fieldsets_with_extensions(
                request, obj, original_fieldsets
            )
        return self._cached_fieldsets

    def _get_fieldsets_with_extensions(self, request, obj, original_fieldsets):
        fieldsets = list(original_fieldsets)
        extended_fields = self._get_extended_fields(obj)
        if extended_fields:
            existing_fields = set(
                field for fs in fieldsets for field in fs[1]["fields"]
            )
            new_extended_fields = [
                f for f in extended_fields if f not in existing_fields
            ]
            if new_extended_fields:
                fieldsets.append(
                    (
                        "Extended Fields",
                        {"fields": new_extended_fields + ["get_schema_version"]},
                    )
                )
        return fieldsets

    def _get_extended_fields(self, obj):
        if obj:
            extension_schema = self._get_extension_schema(obj)
            if extension_schema:
                return list(extension_schema.schema.get("properties", {}).keys())
        return []

    def get_form(self, request, obj=None, **kwargs):
        print("get_form called in ExtensibleModelAdminMixin")
        extended_fields = self._get_extended_fields(obj)
        fields = kwargs.get("fields")
        if fields:
            kwargs["fields"] = [
                f
                for f in fields
                if f not in extended_fields and f != "get_schema_version"
            ]

        try:
            form = super().get_form(request, obj, **kwargs)
        except FieldError as e:
            error_fields = (
                str(e).split("Unknown field(s) (")[1].split(")")[0].split(", ")
            )
            if "fields" in kwargs:
                kwargs["fields"] = [
                    f
                    for f in kwargs["fields"]
                    if f not in error_fields and f != "get_schema_version"
                ]
            form = super().get_form(request, obj, **kwargs)

        if extended_fields:
            for field in extended_fields:
                if field not in form.base_fields:
                    form.base_fields[field] = self._create_form_field(field, obj)

        return form

    def _create_form_field(self, field_name, obj):
        from django import forms

        extension_schema = self._get_extension_schema(obj)
        field_schema = extension_schema.schema["properties"][field_name]

        if field_schema["type"] == "string":
            return forms.CharField(
                label=field_schema.get("title", field_name),
                help_text=field_schema.get("description", ""),
                required=field_name in extension_schema.schema.get("required", []),
            )
        elif field_schema["type"] == "number":
            return forms.FloatField(
                label=field_schema.get("title", field_name),
                help_text=field_schema.get("description", ""),
                required=field_name in extension_schema.schema.get("required", []),
            )
        elif field_schema["type"] == "boolean":
            return forms.BooleanField(
                label=field_schema.get("title", field_name),
                help_text=field_schema.get("description", ""),
                required=field_name in extension_schema.schema.get("required", []),
            )
        elif field_schema["type"] == "integer":
            return forms.IntegerField(
                label=field_schema.get("title", field_name),
                help_text=field_schema.get("description", ""),
                required=field_name in extension_schema.schema.get("required", []),
            )
        return forms.CharField(label=field_name)

    def _get_extension_schema(self, obj):
        content_type = ContentType.objects.get_for_model(obj.__class__)
        tenant_field = get_tenant_field()
        return (
            ExtensionSchema.objects.filter(
                content_type=content_type, **{tenant_field: getattr(obj, tenant_field)}
            )
            .order_by("-version")
            .first()
        )

    def get_readonly_fields(self, request, obj=None):
        print("get_readonly_fields called in ExtensibleModelAdminMixin")
        readonly_fields = super().get_readonly_fields(request, obj)
        return list(readonly_fields) + ["get_schema_version"]

    def get_schema_version(self, obj):
        extension_schema = self._get_extension_schema(obj)
        return extension_schema.version if extension_schema else "N/A"

    get_schema_version.short_description = "Schema Version"

    def save_model(self, request, obj, form, change):
        for field in self._get_extended_fields(obj):
            if field in form.cleaned_data:
                obj.extended_fields[field] = form.cleaned_data[field]
        super().save_model(request, obj, form, change)


class ExtensionSchemaAdmin(admin.ModelAdmin):
    list_display = ("content_type", get_tenant_field(), "version", "created_at")
    list_filter = ("content_type", get_tenant_field())
    readonly_fields = ("version",)

    def save_model(self, request, obj, form, change):
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


# Register ExtensionSchema admin
admin.site.register(ExtensionSchema, ExtensionSchemaAdmin)
