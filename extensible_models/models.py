import jsonschema

from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.db.models import UniqueConstraint
from django.utils.module_loading import import_string

from .utils import get_tenant_field, get_tenant_model


def setup_extension_schema():
    """
    This function dynamically adds the tenant field and uniqueness
    constraint to the ExtensionSchema model.

    This function is called in the AppConfig.ready() method (in
    apps.py) to ensure that app registry is fully populated before the
    model is adjusted.
    """

    tenant_field_name = get_tenant_field()
    tenant_model = get_tenant_model()
    ExtensionSchema = import_string('extensible_models.models.ExtensionSchema')

    ExtensionSchema.add_to_class(tenant_field_name, models.ForeignKey(tenant_model, on_delete=models.CASCADE))
    ExtensionSchema._meta.constraints.append(
        UniqueConstraint(
            fields=['content_type', 'version', tenant_field_name],
            name=f'unique_content_type_{tenant_field_name}_version'
        )
    )


class ExtensionSchema(models.Model):

    schema = models.JSONField()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """
        The empty constraint below is dynamically updated when
        setup_extension_schema() is called in AppConfig.ready().
        """

        constraints = []

    def clean(self):
        super().clean()
        try:
            jsonschema.Draft7Validator.check_schema(self.schema)
        except jsonschema.exceptions.SchemaError as e:
            raise ValidationError(f"Invalid JSON Schema: {e}")

    def save(self, *args, **kwargs):
        tenant_field_name = get_tenant_field()
        if not self.pk:  # New schema
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
