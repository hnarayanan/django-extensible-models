from django import forms
from django.forms import ModelForm

from .models import Contact
from .base_models import ExtraFieldSchema

def get_widget_for_field(field):
    if field["type"] == "string":
        if field.get("enum"):
            choices = [(value, value) for value in field["enum"]]
            return forms.ChoiceField(required=False, choices=choices)
        return forms.CharField(required=False)
    if field["type"] == "number":
        return forms.IntegerField(required=False)
    if field["type"] == "boolean":
        return forms.BooleanField(required=False)


class ContactForm(ModelForm):

    class Meta:
        model = Contact
        fields = ["title", "description", "birth_date", "company"]
        labels = {"title": "Name"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            if self.instance.extra_schema:
                schema = self.instance.extra_schema.schema
                extra = self.instance.extra
                for key, value in schema['properties'].items():
                    self.fields[key] = get_widget_for_field(value)
                    self.fields[key].label = value.get("description", key)
                    self.initial[key] = extra.get(key, None)

    def save(self, *args, **kwargs):
        if self.instance:
            if self.instance.extra_schema:
                extra = self.instance.extra
                schema = self.instance.extra_schema.schema
                for key, value in schema['properties'].items():
                    extra[key] = self.cleaned_data.get(key, {})

        return super().save(*args, **kwargs)
