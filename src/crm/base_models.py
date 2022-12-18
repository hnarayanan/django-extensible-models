import uuid

from django.db import models
from django.contrib.sites.models import Site

from django_extensions.db.models import TitleSlugDescriptionModel, ActivatorModel


class BaseModel(TitleSlugDescriptionModel, ActivatorModel):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    portals = models.ManyToManyField(Site)

    class Meta:
        abstract = True

    # modified_by =
    # extra = JSONField()
