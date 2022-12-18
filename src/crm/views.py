from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.urls import reverse

from .models import Contact
from .forms import ContactForm


class ContactListView(ListView):

    model = Contact
    template_name = "crm/contact-list.html"
    context_object_name = "contacts"


class ContactDetailView(DetailView):

    model = Contact
    template_name = "crm/contact-detail.html"
    context_object_name = "contact"


class ContactCreateView(CreateView):

    template_name = "crm/contact-create.html"
    form_class = ContactForm
    success_url = "/contacts/create/"

    def get_success_url(self):
        return reverse("contact-detail", args=(self.object.id,))


class ContactUpdateView(UpdateView):

    model = Contact
    form_class = ContactForm
    template_name = "crm/contact-update.html"

    def get_success_url(self):
        return reverse("contact-detail", args=(self.object.id,))
