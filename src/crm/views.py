from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView

from .models import Contact
from .forms import ContactForm


class ContactCreateView(CreateView):

    template_name = "crm/contact-create.html"
    form_class = ContactForm
    success_url = "/contacts/create/"

    def form_valid(self, form):
        print("Update form was successfuly submitted")
        return super().form_valid(form)


class ContactDetailView(DetailView):

    model = Contact
    template_name = "crm/contact-detail.html"
    context_object_name = "contact"


class ContactUpdateView(UpdateView):

    template_name = "crm/contact-update.html"
    form_class = ContactForm
    success_url = "/contacts/create/"

    def form_valid(self, form):
        print("Create form was successfuly submitted")
        return super().form_valid(form)
