from django.db import models

from extensible_models.models import ExtensibleModelMixin


class Tenant(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class ExampleModel(ExtensibleModelMixin, models.Model):
    name = models.CharField(max_length=100)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def get_tenant(self):
        return self.tenant


class OtherModel(ExtensibleModelMixin, models.Model):
    name = models.CharField(max_length=100)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def get_tenant(self):
        return self.tenant


class ParentModel(ExtensibleModelMixin, models.Model):
    name = models.CharField(max_length=100)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def get_tenant(self):
        return self.tenant


class ChildModel(ParentModel):
    child_name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} - {self.child_name}"


# This model doesn't use ExtensibleModelMixin, for testing purposes
class NonExtensibleModel(models.Model):
    name = models.CharField(max_length=100)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


# Model with a different tenant field name
class CustomTenantFieldModel(ExtensibleModelMixin, models.Model):
    name = models.CharField(max_length=100)
    custom_tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def get_tenant(self):
        return self.custom_tenant
