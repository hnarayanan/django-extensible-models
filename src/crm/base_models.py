import uuid
import json

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from django_extensions.db.models import TitleSlugDescriptionModel, ActivatorModel

from portals.models import Portal


class PortalRelatedModel(models.Model):

    portals = models.ManyToManyField(Portal, blank=True)

    class Meta:
        abstract = True


class ExtraFieldSchema(PortalRelatedModel):

    schema = models.JSONField()  # Should be valid JSON Schema
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField(null=True)
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self):
        return json.dumps(self.schema, indent=2)

    def get_portal_names(self):
        return "\n".join([portal.name for portal in self.portals.all()])

    get_portal_names.short_description = "Portals"


class ExtraFieldModel(models.Model):

    extra = models.JSONField(null=True, blank=True)
    _extra_schema = GenericRelation(ExtraFieldSchema)

    class Meta:
        abstract = True

    @property
    def extra_schema(self):
        return self._extra_schema.first()


class BaseModel(
    TitleSlugDescriptionModel, ActivatorModel, PortalRelatedModel, ExtraFieldModel
):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # modified_by =

    class Meta:
        abstract = True
