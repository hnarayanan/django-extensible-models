import jsonschema

from django import forms
from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError


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


def validate_extended_data(instance, schema, is_creation=False):
    validation_schema = schema.copy()
    if is_creation:
        # When objects are first created (outside the context of
        # tenant-specific forms), they don't know (yet) what their
        # extension schema is (if any). So we don't check for required
        # fields or minimum number of items on multi-select fields
        # just yet.
        validation_schema.pop("required", None)
        for prop in validation_schema.get("properties", {}).values():
            if prop.get("type") == "array":
                prop.pop("minItems", None)

    try:
        jsonschema.validate(instance=instance, schema=validation_schema)
    except jsonschema.exceptions.ValidationError as e:
        raise ValidationError(f"Extended data validation error: {e}")


def create_form_field(field_name, field_schema):
    field_type = field_schema.get("type")
    choices = field_schema.get("enum")
    items = field_schema.get("items")
    field_args = {
        "required": field_name in field_schema.get("required", []),
        "label": field_schema.get("title", field_name),
        "help_text": field_schema.get("description", ""),
    }

    if choices:
        field_args["choices"] = [(choice, choice) for choice in choices]
        return forms.ChoiceField(**field_args)
    elif field_type == "array" and items and items.get("enum"):
        field_args["choices"] = [(item, item) for item in items["enum"]]
        return forms.MultipleChoiceField(
            widget=forms.CheckboxSelectMultiple, **field_args
        )

    if field_type == "string":
        return forms.CharField(max_length=field_schema.get("maxLength"), **field_args)
    elif field_type == "number":
        return forms.FloatField(
            min_value=field_schema.get("minimum"),
            max_value=field_schema.get("maximum"),
            **field_args,
        )
    elif field_type == "integer":
        return forms.IntegerField(
            min_value=field_schema.get("minimum"),
            max_value=field_schema.get("maximum"),
            **field_args,
        )
    elif field_type == "boolean":
        return forms.BooleanField(**field_args)

    return forms.CharField(**field_args)
