# Example usage

EXTENSIBLE_MODELS_TENANT_MODEL = 'your_app.YourTenantModel'
EXTENSIBLE_MODELS_TENANT_FIELD = 'your_tenant_field_name'


class ExampleModel(ExtensibleModelMixin, models.Model):
    name = models.CharField(max_length=100)
    tenant = models.ForeignKey(get_tenant_model(), on_delete=models.CASCADE)
    # other fields...

    def save(self, *args, **kwargs):
        self.full_clean()  # This will call validate_extended_data
        super().save(*args, **kwargs)


class ExampleModelForm(ExtensibleModelFormMixin, forms.ModelForm):

    class Meta:
        model = ExampleModel
        fields = ['name', 'tenant']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If tenant is not provided, try to get it from the instance
        if not self.tenant and self.instance.pk:
            self.tenant = self.instance.get_tenant()


class ExampleModelSerializer(ExtensibleModelSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = ExampleModel  # Your model that uses ExtensibleModelMixin
        fields = ['id', 'name']  # Include your model's fields here, excluding the tenant field


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
