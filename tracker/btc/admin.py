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
admin.site.register(Node, NodeAdmin)
