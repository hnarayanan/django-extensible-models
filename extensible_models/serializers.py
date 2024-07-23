import json
from datetime import date, datetime
from rest_framework import serializers

from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_date, parse_time, parse_datetime
from django.core.serializers.json import DjangoJSONEncoder

from .utils import get_tenant_field, validate_extended_data


class ExtensibleModelSerializerMixin(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        self.tenant = self._get_tenant(kwargs.get("context", {}))
        self.extension_schema = self._get_extension_schema()
        super().__init__(*args, **kwargs)
        self._add_extended_fields()

    def _get_tenant(self, context):
        request = context.get("request")
        tenant_field = get_tenant_field()
        if request and hasattr(request, tenant_field):
            return getattr(request, tenant_field)
        if self.instance:
            return getattr(self.instance, tenant_field)
        return None

    def _get_extension_schema(self):
        if not self.tenant:
            return None
        return self.Meta.model.get_latest_schema(self.tenant)

    def _add_extended_fields(self):
        if not self.extension_schema:
            return
        for field_name, field_schema in self.extension_schema.schema.get(
            "properties", {}
        ).items():
            self.fields[field_name] = self._create_dynamic_field(
                field_name, field_schema
            )

    def _create_dynamic_field(self, field_name, field_schema):
        field_type = field_schema.get("type")
        field_args = {
            "required": field_name in self.extension_schema.schema.get("required", []),
            "allow_null": not field_schema.get("required", False),
            "label": field_schema.get("title", field_name),
            "help_text": field_schema.get("description", ""),
        }

        if field_type == "string":
            if field_schema.get("format") == "date":
                return serializers.DateField(**field_args)
            elif field_schema.get("format") == "time":
                return serializers.TimeField(**field_args)
            elif field_schema.get("format") == "date-time":
                return serializers.DateTimeField(**field_args)
            elif field_schema.get("format") == "email":
                return serializers.EmailField(**field_args)
            elif field_schema.get("format") == "uri":
                return serializers.URLField(**field_args)
            elif "enum" in field_schema:
                return serializers.ChoiceField(
                    choices=[(choice, choice) for choice in field_schema["enum"]],
                    **field_args
                )
            else:
                return serializers.CharField(**field_args)
        elif field_type == "number":
            return serializers.FloatField(**field_args)
        elif field_type == "integer":
            return serializers.IntegerField(**field_args)
        elif field_type == "boolean":
            return serializers.BooleanField(**field_args)
        elif field_type == "array":
            if "items" in field_schema and "enum" in field_schema["items"]:
                return serializers.MultipleChoiceField(
                    choices=[
                        (choice, choice) for choice in field_schema["items"]["enum"]
                    ],
                    **field_args
                )
            return serializers.ListField(**field_args)

        return serializers.JSONField(**field_args)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if hasattr(instance, "extended_data"):
            ret.update(instance.extended_data or {})
        return ret

    def to_internal_value(self, data):
        ret = super().to_internal_value(data)
        if self.extension_schema:
            extended_data = {}
            for field_name, field_schema in self.extension_schema.schema.get('properties', {}).items():
                if field_name in data:
                    value = data[field_name]
                    field_type = field_schema.get('type')
                    try:
                        if field_type == 'string':
                            if field_schema.get('format') == 'date':
                                value = parse_date(value)
                            elif field_schema.get('format') == 'time':
                                value = parse_time(value)
                            elif field_schema.get('format') == 'date-time':
                                value = parse_datetime(value)
                        elif field_type == 'number':
                            value = float(value)
                        elif field_type == 'integer':
                            value = int(value)
                        elif field_type == 'boolean':
                            if isinstance(value, str):
                                value = value.lower() in ('true', '1', 'yes', 'on')
                            else:
                                value = bool(value)
                        elif field_type == 'array':
                            if isinstance(value, str):
                                try:
                                    value = json.loads(value)
                                except json.JSONDecodeError:
                                    # If it's not valid JSON, assume it's a single value
                                    value = [v.strip() for v in value.split(',') if v.strip()]
                            elif not isinstance(value, list):
                                # If it's not a list (could be from multi-select form field), make it a list
                                value = list(value)
                    except (ValueError, json.JSONDecodeError):
                        raise serializers.ValidationError({field_name: f"Invalid value for {field_schema.get('title', field_name)}"})
                    extended_data[field_name] = value
            try:
                validate_extended_data(extended_data, self.extension_schema.schema)
            except ValidationError as e:
                raise serializers.ValidationError({"extended_data": str(e)})
            ret['extended_data'] = extended_data
        return ret

    def create(self, validated_data):
        extended_data = {}
        model_fields = [f.name for f in self.Meta.model._meta.get_fields()]

        for field in list(validated_data.keys()):
            if field not in model_fields:
                extended_data[field] = validated_data.pop(field)

        instance = super().create(validated_data)

        if extended_data:
            instance.extended_data = extended_data
            instance.save()

        return instance

    def update(self, instance, validated_data):
        extended_data = validated_data.pop('extended_data', {})
        instance = super().update(instance, validated_data)

        if extended_data:
            if not isinstance(instance.extended_data, dict):
                instance.extended_data = {}

            # Convert date objects to ISO format strings
            for key, value in extended_data.items():
                if isinstance(value, (date, datetime)):
                    extended_data[key] = value.isoformat()

            instance.extended_data.update(extended_data)

            # Use DjangoJSONEncoder when saving to ensure all types are properly serialized
            instance.extended_data = json.loads(json.dumps(instance.extended_data, cls=DjangoJSONEncoder))

            instance.save()

        return instance


    def validate(self, attrs):
        attrs = super().validate(attrs)
        if self.extension_schema:
            extended_data = attrs.get("extended_data", {})
            try:
                validate_extended_data(extended_data, self.extension_schema.schema)
            except ValidationError as e:
                raise serializers.ValidationError({"extended_data": str(e)})
        return attrs

    def get_fields(self):
        fields = super().get_fields()
        if self.extension_schema:
            for field_name, field_schema in self.extension_schema.schema.get(
                "properties", {}
            ).items():
                fields[field_name] = self._create_dynamic_field(
                    field_name, field_schema
                )
        return fields
