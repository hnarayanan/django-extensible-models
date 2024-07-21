from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.apps import apps

import jsonschema


def get_tenant_model():
    try:
        return apps.get_model(settings.EXTENSIBLE_MODELS_TENANT_MODEL)
    except AttributeError:
        raise ImproperlyConfigured(
            "EXTENSIBLE_MODELS_TENANT_MODEL must be set in settings"
        )


class ExtensionSchema(models.Model):

    schema = models.JSONField()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    tenant = models.ForeignKey(get_tenant_model(), on_delete=models.CASCADE)
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("content_type", "tenant", "version")

    def clean(self):
        super().clean()
        try:
            jsonschema.Draft7Validator.check_schema(self.schema)
        except jsonschema.exceptions.SchemaError as e:
            raise ValidationError(f"Invalid JSON Schema: {e}")

    def save(self, *args, **kwargs):
        if not self.pk:  # New schema
            max_version = (
                ExtensionSchema.objects.filter(
                    content_type=self.content_type, tenant=self.tenant
                ).aggregate(models.Max("version"))["version__max"]
                or 0
            )
            self.version = max_version + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Schema v{self.version} for {self.content_type} (Tenant: {self.tenant})"


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
            ExtensionSchema.objects.filter(content_type=content_type, tenant=tenant)
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
            ExtensionSchema.objects.filter(content_type=content_type, tenant=tenant)
            .order_by("-version")
            .first()
        )
