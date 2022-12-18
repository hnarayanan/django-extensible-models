from django.contrib import admin

from .models import Fund


@admin.register(Fund)
class FundAdmin(admin.ModelAdmin):

    readonly_fields = ('id', 'created_at', 'updated_at', 'slug')
    list_display = ('title', 'description', 'inception_date', 'status')
    list_filter = ('status', 'inception_date', 'company')
    filter_horizontal = ('portals',)
