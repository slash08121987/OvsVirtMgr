from django.contrib import admin
from django import forms
from django.contrib.admin import AdminSite
from django.apps import apps

Ovs_Compute = apps.get_model('ovs_servers', 'Ovs_Compute')
Instance = apps.get_model('instance', 'Instance')
Compute = apps.get_model('servers', 'Compute')

class VirtAdminSite(AdminSite):
    site_header = 'Веб-сервер - Администрирование'


admin_site = VirtAdminSite()

admin_site.register(Compute)
admin_site.register(Instance)
admin_site.register(Ovs_Compute)