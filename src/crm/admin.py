from django.contrib import admin

from .models import Contact, Company


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):

    readonly_fields = ('id', 'created_at', 'updated_at', 'slug')
    list_display = ('title', 'description', 'birth_date', 'status')
    list_filter = ('status', 'birth_date', 'company')


class ContactInline(admin.StackedInline):
    model = Contact


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):

    readonly_fields = ('id', 'created_at', 'updated_at', 'slug')
    list_display = ('title', 'description', 'kind', 'status')
    list_filter = ('status', 'kind')
    inlines = [
        ContactInline,
    ]
    
