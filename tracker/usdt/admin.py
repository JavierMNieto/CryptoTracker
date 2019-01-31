from django.contrib import admin
from .models import Node

class NodeAdmin(admin.ModelAdmin):
    def delete_queryset(self, request, queryset):
        for e in queryset:
            e.delete()
admin.site.register(Node, NodeAdmin)
