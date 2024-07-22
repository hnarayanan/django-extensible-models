import json
import jsonschema

from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType

from .models import ExtensionSchema
from .utils import get_tenant_field


class ExtensibleModelAdminMixin:

    def get_form(self, request, obj=None, **kwargs):
        original_kwargs = kwargs.copy()
        if "fields" in original_kwargs:
            original_fields = [
                f
                for f in original_kwargs["fields"]
                if f in [field.name for field in self.model._meta.get_fields()]
            ]
            original_kwargs["fields"] = original_fields

        FormClass = super().get_form(request, obj, **original_kwargs)

        extension_schema = self._get_extension_schema(obj)

        class ExtendedForm(FormClass):
            extended_data_json = forms.CharField(
                widget=forms.Textarea(attrs={"readonly": "readonly"}),
                required=False,
                help_text="JSON representation of extended data.",
            )

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.extension_schema = extension_schema
                for field_name in original_fields:
                    if field_name not in self.fields:
                        self.fields[field_name] = self.base_fields[field_name]
                if self.extension_schema:
                    for field_name, field_schema in self.extension_schema.schema.get(
                        "properties", {}
                    ).items():
                        self.fields[field_name] = (
                            ExtensibleModelAdminMixin._create_form_field(
                                field_name, field_schema
                            )
                        )
                        if (
                            obj
                            and obj.extended_data
                            and field_name in obj.extended_data
                        ):
                            self.initial[field_name] = obj.extended_data[field_name]
                for field_name in self.base_fields:
                    if field_name not in self.fields:
                        self.fields[field_name] = self.base_fields[field_name]

                if obj and obj.extended_data:
                    self.initial["extended_data_json"] = json.dumps(
                        obj.extended_data, indent=2
                    )

            def clean(self):
                cleaned_data = super().clean()
                if self.extension_schema:
                    extended_data = {}
                    for field_name, field_schema in self.extension_schema.schema.get('properties', {}).items():
                        if field_name in cleaned_data:
                            extended_data[field_name] = cleaned_data.pop(field_name)

                    try:
                        jsonschema.validate(instance=extended_data, schema=self.extension_schema.schema)
                    except jsonschema.exceptions.ValidationError as e:
                        raise ValidationError(f"Extended data validation error: {e}")

                    cleaned_data['extended_data'] = extended_data
                return cleaned_data

        return ExtendedForm

    @staticmethod
    def _create_form_field(field_name, field_schema):
        field_type = field_schema.get("type")
        field_args = {
            "required": field_name in field_schema.get("required", []),
            "label": field_schema.get("title", field_name),
            "help_text": field_schema.get("description", ""),
        }

        if field_type == "string":
            return forms.CharField(**field_args)
        elif field_type == "number":
            return forms.FloatField(**field_args)
        elif field_type == "integer":
            return forms.IntegerField(**field_args)
        elif field_type == "boolean":
            return forms.BooleanField(**field_args)
        return forms.CharField(**field_args)

    def get_fieldsets(self, request, obj=None):
        fieldsets = list(super().get_fieldsets(request, obj))

        extension_schema = self._get_extension_schema(obj)
        if extension_schema:
            extended_fields = list(extension_schema.schema.get("properties", {}).keys())
            fieldsets.append(("Extended Fields", {"fields": extended_fields}))

        fieldsets.append(("Meta", {"fields": ["extended_data_json"]}))

        return fieldsets

    def _get_extension_schema(self, obj):
        if obj and hasattr(obj, get_tenant_field()):
            content_type = ContentType.objects.get_for_model(obj.__class__)
            return (
                ExtensionSchema.objects.filter(
                    content_type=content_type,
                    **{get_tenant_field(): getattr(obj, get_tenant_field())}
                )
                .order_by("-version")
                .first()
            )
        return None

    def save_model(self, request, obj, form, change):
        if 'extended_data' in form.cleaned_data:
            obj.extended_data = form.cleaned_data['extended_data']
        super().save_model(request, obj, form, change)

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if obj:
            extension_schema = self._get_extension_schema(obj)
            if extension_schema:
                extended_fields = list(
                    extension_schema.schema.get("properties", {}).keys()
                )
                fields = [
                    f for f in fields if f not in extended_fields
                ] + extended_fields
        return fields

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        return list(readonly_fields) + ["extended_data_json"] if obj and obj.extended_data else readonly_fields


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


admin.site.register(ExtensionSchema, ExtensionSchemaAdmin)
