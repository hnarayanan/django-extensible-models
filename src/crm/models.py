from django.db import models

from .base_models import BaseModel


class Contact(BaseModel):

    birth_date = models.DateField(null=True, blank=True)
    company = models.ForeignKey(
        "crm.Company",
        related_name="contacts",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    def __str__(self):
        return self.title


class Company(BaseModel):

    COMPANY_KINDS = (
        ("IC", "Investment Company"),
        ("MC", "Fund Management Company"),
        ("SP", "Service Provider"),
    )

    kind = models.CharField(max_length=2, choices=COMPANY_KINDS, null=True, blank=True)

    class Meta:
        verbose_name_plural = "companies"

    def __str__(self):
        return self.title
