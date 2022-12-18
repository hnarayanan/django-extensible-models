from django.contrib import admin

from .models import Contact, Company
from .base_models import ExtraFieldSchema


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):

    readonly_fields = ('id', 'created_at', 'updated_at', 'slug')
    list_display = ('title', 'description', 'birth_date', 'status')
    list_filter = ('status', 'birth_date', 'company')
    filter_horizontal = ('portals',)


class ContactInline(admin.StackedInline):
    model = Contact


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):

    readonly_fields = ('id', 'created_at', 'updated_at', 'slug')
    list_display = ('title', 'description', 'kind', 'status')
    list_filter = ('status', 'kind')
    filter_horizontal = ('portals',)
    inlines = [
        ContactInline,
    ]


@admin.register(ExtraFieldSchema)
class ExtraFieldSchemaAdin(admin.ModelAdmin):

    list_display = ('content_type', 'object_id', 'content_object', 'schema')
    filter_horizontal = ('portals',)
