from rest_framework import serializers
from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_date, parse_time, parse_datetime

from .utils import get_tenant_field, validate_extended_data


class ExtensibleModelSerializerMixin(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tenant = self._get_tenant()
        self.extension_schema = self._get_extension_schema()
        self._add_extended_fields()

    def _get_tenant(self):
        request = self.context.get('request')
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
        for field_name, field_schema in self.extension_schema.schema.get('properties', {}).items():
            self.fields[field_name] = self._create_dynamic_field(field_name, field_schema)

    def _create_dynamic_field(self, field_name, field_schema):
        field_type = field_schema.get('type')
        field_args = {
            'required': field_name in self.extension_schema.schema.get('required', []),
            'allow_null': not field_schema.get('required', False),
            'label': field_schema.get('title', field_name),
            'help_text': field_schema.get('description', ''),
        }

        if field_type == 'string':
            if field_schema.get('format') == 'date':
                return serializers.DateField(**field_args)
            elif field_schema.get('format') == 'time':
                return serializers.TimeField(**field_args)
            elif field_schema.get('format') == 'date-time':
                return serializers.DateTimeField(**field_args)
            elif field_schema.get('format') == 'email':
                return serializers.EmailField(**field_args)
            elif field_schema.get('format') == 'uri':
                return serializers.URLField(**field_args)
            else:
                return serializers.CharField(**field_args)
        elif field_type == 'number':
            return serializers.FloatField(**field_args)
        elif field_type == 'integer':
            return serializers.IntegerField(**field_args)
        elif field_type == 'boolean':
            return serializers.BooleanField(**field_args)
        elif field_type == 'array':
            return serializers.ListField(**field_args)

        return serializers.JSONField(**field_args)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if hasattr(instance, 'extended_data'):
            ret.update(instance.extended_data)
        return ret

    def to_internal_value(self, data):
        ret = super().to_internal_value(data)
        if self.extension_schema:
            extended_data = {}
            for field_name, field_schema in self.extension_schema.schema.get('properties', {}).items():
                if field_name in data:
                    value = data[field_name]
                    if field_schema.get('type') == 'string':
                        if field_schema.get('format') == 'date':
                            value = parse_date(value)
                        elif field_schema.get('format') == 'time':
                            value = parse_time(value)
                        elif field_schema.get('format') == 'date-time':
                            value = parse_datetime(value)
                    extended_data[field_name] = value
            try:
                validate_extended_data(extended_data, self.extension_schema.schema)
            except ValidationError as e:
                raise serializers.ValidationError({"extended_data": str(e)})

            ret['extended_data'] = extended_data
        return ret

    def create(self, validated_data):
        extended_data = validated_data.pop('extended_data', {})
        instance = super().create(validated_data)
        if extended_data:
            instance.extended_data = extended_data
            instance.save()
        return instance

    def update(self, instance, validated_data):
        extended_data = validated_data.pop('extended_data', {})
        instance = super().update(instance, validated_data)
        if extended_data:
            instance.extended_data.update(extended_data)
            instance.save()
        return instance

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if self.extension_schema:
            extended_data = attrs.get('extended_data', {})
            try:
                validate_extended_data(extended_data, self.extension_schema.schema)
            except ValidationError as e:
                raise serializers.ValidationError({"extended_data": str(e)})
        return attrs
