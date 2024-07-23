import jsonschema
from datetime import date, time, datetime

from django import forms
from django.apps import apps
from django.conf import settings

from django.core.validators import URLValidator, EmailValidator
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
        validation_schema.pop("required", None)
        for prop in validation_schema.get("properties", {}).values():
            if prop.get("type") == "array":
                prop.pop("minItems", None)

    # Convert datetime.time objects to string before validation
    for field, value in instance.items():
        if isinstance(value, time):
            instance[field] = value.isoformat()
        elif isinstance(value, date):
            instance[field] = value.isoformat()
        elif isinstance(value, datetime):
            instance[field] = value.isoformat()

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
        return forms.ChoiceField(widget=forms.Select(attrs={'class': 'select2'}), **field_args)
    elif field_type == "array" and items and items.get("enum"):
        field_args["choices"] = [(item, item) for item in items["enum"]]
        return forms.MultipleChoiceField(
            widget=forms.CheckboxSelectMultiple(attrs={'class': 'checkbox-inline'}), **field_args
        )

    if field_type == "string":
        if field_schema.get("format") == "date":
            return forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), **field_args)
        elif field_schema.get("format") == "time":
            return forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), **field_args)
        elif field_schema.get("format") == "date-time":
            return forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}), **field_args)
        elif field_schema.get("format") == "email":
            field_args["validators"] = [EmailValidator()]
            return forms.EmailField(widget=forms.EmailInput(attrs={'autocomplete': 'email'}), **field_args)
        elif field_schema.get("format") == "uri":
            field_args["validators"] = [URLValidator()]
            return forms.URLField(widget=forms.URLInput(attrs={'autocomplete': 'url'}), **field_args)
        else:
            return forms.CharField(max_length=field_schema.get("maxLength"),
                                   widget=forms.TextInput(attrs={'class': 'form-control'}), **field_args)
    elif field_type == "number":
        return forms.FloatField(
            min_value=field_schema.get("minimum"),
            max_value=field_schema.get("maximum"),
            widget=forms.NumberInput(attrs={'step': 'any', 'class': 'form-control'}),
            **field_args
        )
    elif field_type == "integer":
        return forms.IntegerField(
            min_value=field_schema.get("minimum"),
            max_value=field_schema.get("maximum"),
            widget=forms.NumberInput(attrs={'class': 'form-control'}),
            **field_args
        )
    elif field_type == "boolean":
        return forms.BooleanField(widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}), **field_args)

    return forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control'}), **field_args)
