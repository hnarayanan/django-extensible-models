from django import forms
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from .models import ExtensionSchema, get_tenant_model
import jsonschema


class ExtensibleModelFormMixin:
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop("tenant", None)
        super().__init__(*args, **kwargs)
        self.extension_schema = self._get_extension_schema()
        self._add_extended_fields()

    def _get_extension_schema(self):
        if hasattr(self, "instance") and self.instance.pk:
            return self.instance.get_extension_schema()
        elif self.tenant:
            content_type = ContentType.objects.get_for_model(self._meta.model)
            return (
                ExtensionSchema.objects.filter(
                    content_type=content_type, tenant=self.tenant
                )
                .order_by("-version")
                .first()
            )
        return None

    def _add_extended_fields(self):
        if not self.extension_schema:
            return

        for field_name, field_schema in self.extension_schema.schema.get(
            "properties", {}
        ).items():
            field = self._create_form_field(field_name, field_schema)
            if field:
                self.fields[field_name] = field

    def _create_form_field(self, field_name, field_schema):
        field_type = field_schema.get("type")
        if field_type == "string":
            return forms.CharField(
                required=field_name in self.extension_schema.schema.get("required", []),
                label=field_schema.get("title", field_name),
                help_text=field_schema.get("description", ""),
                max_length=field_schema.get("maxLength"),
            )
        elif field_type == "number":
            return forms.FloatField(
                required=field_name in self.extension_schema.schema.get("required", []),
                label=field_schema.get("title", field_name),
                help_text=field_schema.get("description", ""),
                min_value=field_schema.get("minimum"),
                max_value=field_schema.get("maximum"),
            )
        elif field_type == "integer":
            return forms.IntegerField(
                required=field_name in self.extension_schema.schema.get("required", []),
                label=field_schema.get("title", field_name),
                help_text=field_schema.get("description", ""),
                min_value=field_schema.get("minimum"),
                max_value=field_schema.get("maximum"),
            )
        elif field_type == "boolean":
            return forms.BooleanField(
                required=field_name in self.extension_schema.schema.get("required", []),
                label=field_schema.get("title", field_name),
                help_text=field_schema.get("description", ""),
            )
        elif field_type == "array":
            return forms.CharField(
                required=field_name in self.extension_schema.schema.get("required", []),
                label=field_schema.get("title", field_name),
                help_text=f"{field_schema.get('description', '')} (Enter items separated by commas)",
                widget=forms.Textarea,
            )
        # Add more field types as needed
        return None

    def clean(self):
        cleaned_data = super().clean()
        if self.extension_schema:
            extended_fields = {
                field_name: cleaned_data.get(field_name)
                for field_name in self.extension_schema.schema.get("properties", {})
            }
            try:
                jsonschema.validate(
                    instance=extended_fields, schema=self.extension_schema.schema
                )
            except jsonschema.exceptions.ValidationError as e:
                raise ValidationError(f"Extended fields validation error: {e}")
            cleaned_data["extended_fields"] = extended_fields
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.extension_schema:
            instance.extended_fields = self.cleaned_data["extended_fields"]
        if commit:
            instance.save()
        return instance
