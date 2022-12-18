import uuid
import json

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.contrib.sites.models import Site


from django_extensions.db.models import TitleSlugDescriptionModel, ActivatorModel


class ExtraFieldSchema(models.Model):

    schema = models.JSONField() # Should be valid JSON Schema
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return json.dumps(self.schema, indent=2)

    class Meta:
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    portals = models.ManyToManyField(Site)


class ExtraFieldModel(models.Model):

    extra = models.JSONField(default=dict)
    extra_schema = GenericRelation(ExtraFieldSchema)

    class Meta:
        abstract = True


class BaseModel(TitleSlugDescriptionModel, ActivatorModel, ExtraFieldModel):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    portals = models.ManyToManyField(Site)
    # modified_by =

    class Meta:
        abstract = True
