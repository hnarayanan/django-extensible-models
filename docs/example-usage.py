# shell
pip install django-extensible-models

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


# admin.py
from django.contrib import admin
from extensible_models.admin import ExtensibleModelAdminMixin

@admin.register(ExampleModel)
class ExampleModelAdmin(ExtensibleModelAdminMixin, admin.ModelAdmin):
    list_display = ("name")


# forms.py
from django import forms
from extensible_models.forms import ExtensibleModelForm


class ExampleModelForm(ExtensibleModelFormMixin, forms.ModelForm):

    class Meta:
        model = ExampleModel
        fields = ["name",]


# serializers.py

class ExampleModelSerializer(
    ExtensibleModelSerializerMixin, serializers.ModelSerializer
):
    class Meta:
        model = ExampleModel
        fields = [
            "id",
        ]
