from django.contrib import admin
from .models import Node

class NodeAdmin(admin.ModelAdmin):
    def delete_queryset(self, request, queryset):
        if Node.objects.count() == len(queryset):
            queryset[0].delete(allNodes = True)
            Node.objects.all().delete()
        else:
            for e in queryset:
                e.delete()
    def refresh(self, request, queryset):
        for e in queryset:
            e.refresh()
    refresh.short_description = 'Refresh Selected Nodes'
    list_display = ['name', 'BTC_Address', 'minTx', 'tx_Since', 'category']
    actions = ['refresh']
admin.site.register(Node, NodeAdmin)
