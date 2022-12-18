from django.contrib import admin
from django.contrib.sites.models import Site

from .models import Portal


admin.site.unregister(Site)


@admin.register(Portal)
class ExtraFieldSchemaAdin(admin.ModelAdmin):

    list_display = (
        "name",
        "domain",
    )
