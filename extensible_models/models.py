import jsonschema

from django.db import models
from django.db.models import F, Q, UniqueConstraint
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from .utils import get_tenant_model, get_tenant_field


class ExtensionSchema(models.Model):
    schema = models.JSONField()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['content_type', 'version'],
                condition=Q(**{get_tenant_field(): F(get_tenant_field())}),
                name='unique_content_type_tenant_version'
            )
        ]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        tenant_field_name = get_tenant_field()
        tenant_model = get_tenant_model()
        cls.add_to_class(
            tenant_field_name, models.ForeignKey(tenant_model, on_delete=models.CASCADE)
        )

    def clean(self):
        super().clean()
        try:
            jsonschema.Draft7Validator.check_schema(self.schema)
        except jsonschema.exceptions.SchemaError as e:
            raise ValidationError(f"Invalid JSON Schema: {e}")

    def save(self, *args, **kwargs):
        if not self.pk:  # New schema
            tenant_field_name = get_tenant_field()
            max_version = (
                ExtensionSchema.objects.filter(
                    content_type=self.content_type,
                    **{tenant_field_name: getattr(self, tenant_field_name)},
                ).aggregate(models.Max("version"))["version__max"]
                or 0
            )
            self.version = max_version + 1
        super().save(*args, **kwargs)

    def __str__(self):
        tenant_field_name = get_tenant_field()
        tenant_value = getattr(self, tenant_field_name)
        return (
            f"Schema v{self.version} for {self.content_type} (Tenant: {tenant_value})"
        )


class ExtensibleModelMixin(models.Model):
    extended_data = models.JSONField(default=dict, blank=True)

    class Meta:
        abstract = True

    def get_tenant(self):
        tenant_model = get_tenant_model()
        for field in self._meta.fields:
            if (
                isinstance(field, models.ForeignKey)
                and field.related_model == tenant_model
            ):
                return getattr(self, field.name)
        raise AttributeError(
            f"No tenant field found for model {self.__class__.__name__}"
        )

    def get_extension_schema(self):
        tenant = self.get_tenant()
        content_type = ContentType.objects.get_for_model(self.__class__)
        return (
            ExtensionSchema.objects.filter(
                content_type=content_type, **{get_tenant_field(): tenant}
            )
            .order_by("-version")
            .first()
        )

    def clean(self):
        super().clean()
        self.validate_extended_data()

    def validate_extended_data(self):
        schema = self.get_extension_schema()
        if schema:
            try:
                jsonschema.validate(instance=self.extended_data, schema=schema.schema)
            except jsonschema.exceptions.ValidationError as e:
                raise ValidationError(f"Extended data validation error: {e}")

    @classmethod
    def get_latest_schema(cls, tenant):
        content_type = ContentType.objects.get_for_model(cls)
        return (
            ExtensionSchema.objects.filter(
                content_type=content_type, **{get_tenant_field(): tenant}
            )
            .order_by("-version")
            .first()
        )
