from django.db import models
from django.contrib.sites.models import Site

from crm.base_models import BaseModel
from crm.models import Company


class Fund(BaseModel):

    inception_date = models.DateField(null=True, blank=True)
    company = models.ForeignKey(
        Company, null=True, blank=True, on_delete=models.SET_NULL
    )
