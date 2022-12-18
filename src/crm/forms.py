from django.forms import ModelForm

from .models import Contact


class ContactForm(ModelForm):

    class Meta:
        model = Contact
        fields = ["title", "description", "birth_date", "company"]
        labels = {"title": "Name"}
