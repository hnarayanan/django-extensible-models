import jsonschema

from django import forms
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType

from .models import ExtensionSchema
from .utils import get_tenant_field


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
            tenant_field = get_tenant_field()
            return (
                ExtensionSchema.objects.filter(
                    content_type=content_type, **{tenant_field: self.tenant}
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

        # Ensure the form's _meta attribute includes the dynamically added fields
        if hasattr(self, "_meta") and hasattr(self._meta, "fields"):
            if isinstance(self._meta.fields, tuple):
                self._meta.fields = list(self._meta.fields)
            if self._meta.fields is not None:
                for field in self.fields.keys():
                    if field not in self._meta.fields:
                        self._meta.fields.append(field)

    def _create_form_field(self, field_name, field_schema):
        field_type = field_schema.get("type")
        choices = field_schema.get("enum")
        items = field_schema.get("items")

        field_args = {
            "required": field_name in self.extension_schema.schema.get("required", []),
            "label": field_schema.get("title", field_name),
            "help_text": field_schema.get("description", ""),
        }

        if choices:
            field_args["choices"] = [(choice, choice) for choice in choices]
            return forms.ChoiceField(**field_args)
        elif items and items.get("enum"):
            field_args["choices"] = [(item, item) for item in items["enum"]]
            return forms.MultipleChoiceField(**field_args)

        if field_type == "string":
            return forms.CharField(max_length=field_schema.get("maxLength"), **field_args)
        elif field_type == "number":
            return forms.FloatField(min_value=field_schema.get("minimum"), max_value=field_schema.get("maximum"), **field_args)
        elif field_type == "integer":
            return forms.IntegerField(min_value=field_schema.get("minimum"), max_value=field_schema.get("maximum"), **field_args)
        elif field_type == "boolean":
            return forms.BooleanField(**field_args)
        elif field_type == "array":
            return forms.CharField(widget=forms.Textarea, **field_args)
        return None

    def clean(self):
        cleaned_data = super().clean()
        if self.extension_schema:
            extended_fields = {}
            for field_name in self.extension_schema.schema.get("properties", {}):
                if field_name in cleaned_data:
                    extended_fields[field_name] = cleaned_data.pop(field_name)
                elif field_name in self.extension_schema.schema.get("required", []):
                    self.add_error(field_name, f"{field_name} is required.")
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
        if hasattr(self, "cleaned_data") and "extended_fields" in self.cleaned_data:
            instance.extended_data.update(self.cleaned_data["extended_fields"])
        if commit:
            instance.save()
        return instance
