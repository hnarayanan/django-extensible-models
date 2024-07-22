from django.contrib import admin
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldError


from .models import ExtensionSchema
from .utils import get_tenant_field


class ExtensibleModelAdminMixin:

    def get_form(self, request, obj=None, **kwargs):
        print(f"get_form called with obj: {obj}")  # Debug print

        if obj:
            extension_schema = self._get_extension_schema(obj)
            if extension_schema:
                # Remove extended fields from kwargs to prevent FieldError
                extended_fields = list(
                    extension_schema.schema.get("properties", {}).keys()
                )
                fields = kwargs.get("fields")
                if fields:
                    kwargs["fields"] = [f for f in fields if f not in extended_fields]

        try:
            FormClass = super().get_form(request, obj, **kwargs)
        except FieldError:
            # If FieldError is raised, try again with no fields specified
            kwargs.pop("fields", None)
            FormClass = super().get_form(request, obj, **kwargs)

        if obj and extension_schema:

            class ExtendedForm(FormClass):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    for field_name, field_schema in extension_schema.schema.get(
                        "properties", {}
                    ).items():
                        if field_name not in self.fields:
                            self.fields[field_name] = self._create_form_field(
                                field_name, field_schema
                            )
                        # Initialize the field with existing data
                        if obj.extended_data and field_name in obj.extended_data:
                            self.initial[field_name] = obj.extended_data[field_name]

                @staticmethod
                def _create_form_field(field_name, field_schema):
                    # Move the _create_form_field method here
                    return self._create_form_field(field_name, field_schema)

            print(
                f"Form created with fields: {list(ExtendedForm().fields.keys())}"
            )  # Debug print
            return ExtendedForm

        print(
            f"Form created with fields: {list(FormClass().fields.keys())}"
        )  # Debug print
        return FormClass

    def _create_form_field(self, field_name, field_schema):
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
        fieldsets = super().get_fieldsets(request, obj)
        if obj:
            extension_schema = self._get_extension_schema(obj)
            if extension_schema:
                extended_fields = list(
                    extension_schema.schema.get("properties", {}).keys()
                )
                # Remove extended fields from the default fieldset
                default_fields = [
                    f for f in fieldsets[0][1]["fields"] if f not in extended_fields
                ]
                fieldsets[0][1]["fields"] = default_fields
                # Add extended fields as a separate fieldset
                fieldsets.append(("Extended Fields", {"fields": extended_fields}))
        return fieldsets

    def _get_extension_schema(self, obj):
        content_type = ContentType.objects.get_for_model(obj.__class__)
        from extensible_models.models import ExtensionSchema

        return (
            ExtensionSchema.objects.filter(content_type=content_type, portal=obj.portal)
            .order_by("-version")
            .first()
        )

    def save_model(self, request, obj, form, change):
        print(f"save_model called for obj: {obj}")  # Debug print
        extension_schema = self._get_extension_schema(obj)
        if extension_schema:
            extended_data = {}
            for field_name in extension_schema.schema.get("properties", {}).keys():
                if field_name in form.cleaned_data:
                    extended_data[field_name] = form.cleaned_data[field_name]
            obj.extended_data = extended_data
            print(f"Extended data being saved: {extended_data}")  # Debug print
        super().save_model(request, obj, form, change)
        print(f"Object saved. Extended data: {obj.extended_data}")  # Debug print

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
