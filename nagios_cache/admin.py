from django.contrib import admin

from nagios_cache.models import NagiosServiceStatus, NagiosHostStatus, NagiosHostgroup
from nagios_cache.models import NagiosServicegroup


class NagiosHostStatusAdmin(admin.ModelAdmin):
    list_filter = ['status']
    list_display = ['host_name', 'status', 'has_been_acknowledged', 'status_information', 'last_check']
    search_fields = ['host_name', 'status_information']


class NagiosServiceStatusAdmin(NagiosHostStatusAdmin):
    list_display = ['host', 'service_description'] + NagiosHostStatusAdmin.list_display
    search_fields = ['service_description'] + NagiosHostStatusAdmin.search_fields


class NagiosHostgroupAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


class NagiosServicegroupAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


admin.site.register(NagiosHostStatus, NagiosHostStatusAdmin)
admin.site.register(NagiosServiceStatus, NagiosServiceStatusAdmin)
admin.site.register(NagiosServicegroup, NagiosServicegroupAdmin)
admin.site.register(NagiosHostgroup, NagiosHostgroupAdmin)

