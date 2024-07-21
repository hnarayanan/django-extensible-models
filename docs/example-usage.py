# Example usage


class ExampleModelForm(ExtensibleModelFormMixin, forms.ModelForm):

    class Meta:
        model = ExampleModel
        fields = ["name", "tenant"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If tenant is not provided, try to get it from the instance
        if not self.tenant and self.instance.pk:
            self.tenant = self.instance.get_tenant()


class ExampleModelSerializer(
    ExtensibleModelSerializerMixin, serializers.ModelSerializer
):
    class Meta:
        model = ExampleModel  # Your model that uses ExtensibleModelMixin
        fields = [
            "id",
            "name",
        ]  # Include your model's fields here, excluding the tenant field


@admin.register(ExtensionSchema)
class ExtensionSchemaAdmin(ExtensionSchemaAdmin):
    pass


# Example of how to use the mixin with your model admin
@admin.register(ExampleModel)
class ExampleModelAdmin(ExtensibleModelAdminMixin, admin.ModelAdmin):
    list_display = ("name", "get_tenant", "schema_version")

    def get_tenant(self, obj):
        return self._get_tenant(obj)

    get_tenant.short_description = "Tenant"


class Product(ExtensibleModelMixin):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)


# forms.py
from extensible_models.forms import ExtensibleModelForm


class ProductForm(ExtensibleModelForm):
    class Meta:
        model = Product
        fields = ["name", "price"]  # Extensible fields will be added automatically


###############

# pip install django-extensible-models

# settings.py
INSTALLED_APPS = [
    # ...
    "extensible_models",
    # ...
]

EXTENSIBLE_MODELS_TENANT_MODEL = "your_app.YourTenantModel"
EXTENSIBLE_MODELS_TENANT_FIELD = "your_tenant_field_name"

# models.py
from django.db import models
from extensible_models.models import ExtensibleModelMixin


class ExampleModel(ExtensibleModelMixin, models.Model):
    name = models.CharField(max_length=100)

    def save(self, *args, **kwargs):
        self.full_clean()  # This will call validate_extended_data
        super().save(*args, **kwargs)


### Customizing the Admin Interface

If you need to customize the admin interface for the `ExtensionSchema` model, you can unregister the default registration and register your own:

```python
# In your project's admin.py

from django.contrib import admin
from extensible_models.models import ExtensionSchema

# Unregister the default admin registration
admin.site.unregister(ExtensionSchema)

class CustomExtensionSchemaAdmin(admin.ModelAdmin):
    # Your custom admin options here
    pass

# Register the model with your custom admin class
admin.site.register(ExtensionSchema, CustomExtensionSchemaAdmin)
