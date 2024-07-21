import jsonschema
from rest_framework import serializers

from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.conf import settings

from .models import ExtensionSchema, get_tenant_model


class ExtensibleModelSerializerMixin:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tenant = self.get_tenant()
        self.extension_schema = self._get_extension_schema()
        self._add_extended_fields()

    @classmethod
    def get_tenant_model(cls):
        return get_tenant_model()

    @classmethod
    def get_tenant_field_name(cls):
        return getattr(settings, "EXTENSIBLE_MODELS_TENANT_FIELD", "tenant")

    def get_tenant(self):
        request = self.context.get("request")
        if request and hasattr(request, "tenant"):
            return request.tenant

        if self.instance:
            tenant_field = self.get_tenant_field_name()
            return getattr(self.instance, tenant_field, None)

        return None

    def _get_extension_schema(self):
        if not self.tenant:
            return None

        content_type = ContentType.objects.get_for_model(self.Meta.model)
        return (
            ExtensionSchema.objects.filter(
                content_type=content_type, tenant=self.tenant
            )
            .order_by("-version")
            .first()
        )

    def _add_extended_fields(self):
        if not self.extension_schema:
            return

        for field_name, field_schema in self.extension_schema.schema.get(
            "properties", {}
        ).items():
            self.fields[field_name] = self._create_serializer_field(
                field_name, field_schema
            )

    def _create_serializer_field(self, field_name, field_schema):
        field_type = field_schema.get("type")
        if field_type == "string":
            return serializers.CharField(
                required=field_name in self.extension_schema.schema.get("required", []),
                allow_null=not field_schema.get("required", False),
                max_length=field_schema.get("maxLength"),
            )
        elif field_type == "number":
            return serializers.FloatField(
                required=field_name in self.extension_schema.schema.get("required", []),
                allow_null=not field_schema.get("required", False),
                min_value=field_schema.get("minimum"),
                max_value=field_schema.get("maximum"),
            )
        elif field_type == "integer":
            return serializers.IntegerField(
                required=field_name in self.extension_schema.schema.get("required", []),
                allow_null=not field_schema.get("required", False),
                min_value=field_schema.get("minimum"),
                max_value=field_schema.get("maximum"),
            )
        elif field_type == "boolean":
            return serializers.BooleanField(
                required=field_name in self.extension_schema.schema.get("required", []),
                allow_null=not field_schema.get("required", False),
            )
        elif field_type == "array":
            return serializers.ListField(
                required=field_name in self.extension_schema.schema.get("required", []),
                allow_null=not field_schema.get("required", False),
                child=serializers.JSONField(),
            )
        # TODO: Add more field types
        return serializers.JSONField(
            required=False, allow_null=True
        )  # Default to JSONField for unknown types

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        extended_fields = getattr(instance, "extended_fields", {})
        ret.update(extended_fields)
        return ret

    def to_internal_value(self, data):
        internal_value = super().to_internal_value(data)
        if self.extension_schema:
            extended_fields = {}
            for field_name in self.extension_schema.schema.get("properties", {}):
                if field_name in data:
                    extended_fields[field_name] = data[field_name]

            try:
                jsonschema.validate(
                    instance=extended_fields, schema=self.extension_schema.schema
                )
            except jsonschema.exceptions.ValidationError as e:
                raise serializers.ValidationError(
                    f"Extended fields validation error: {e}"
                )

            internal_value["extended_fields"] = extended_fields
        return internal_value

    def create(self, validated_data):
        extended_fields = validated_data.pop("extended_fields", {})
        instance = super().create(validated_data)
        instance.extended_fields = extended_fields
        instance.save()
        return instance

    def update(self, instance, validated_data):
        extended_fields = validated_data.pop("extended_fields", {})
        instance = super().update(instance, validated_data)
        instance.extended_fields.update(extended_fields)
        instance.save()
        return instance
