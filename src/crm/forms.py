from django import forms
from django.forms import ModelForm

from .models import Contact
from .base_models import ExtraFieldSchema


class ContactForm(ModelForm):

    class Meta:
        model = Contact
        fields = ["title", "description", "birth_date", "company", "extra"]
        labels = {"title": "Name"}
