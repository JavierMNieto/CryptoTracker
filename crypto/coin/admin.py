from django.contrib import admin
from .models import Node, Group, Session, Coin
from django.utils.safestring import mark_safe
from django.urls import reverse

class EditLinkToInlineObject(object):
    def edit_link(self, instance):
        url = reverse('admin:%s_%s_change' % (
            instance._meta.app_label,  instance._meta.model_name),  args=[instance.pk] )
        if instance.pk:
            return mark_safe(u'<a href="{u}">Edit</a>'.format(u=url))
        else:
            return ''

class NodeInline(EditLinkToInlineObject, admin.TabularInline):
    model = Node
    extra = 0
    fields = ['edit_link', 'name', 'addr']
    readonly_fields = ('edit_link', )

class GroupInline(EditLinkToInlineObject, admin.TabularInline):
    model  = Group
    extra = 0
    fields = ['edit_link', 'name']
    readonly_fields = ('edit_link', )

class SessionInline(EditLinkToInlineObject, admin.TabularInline):
    model = Session
    extra = 0
    fields = ['edit_link', 'name']
    readonly_fields = ('edit_link', )

class CoinInline(EditLinkToInlineObject, admin.TabularInline):
    model = Coin
    extra = 0
    fields = ['edit_link', 'name']
    readonly_fields = ('edit_link', 'name')

class GroupAdmin(admin.ModelAdmin):
    fields = ["name", "minBal", "maxBal", "minTx", "maxTx", "minTime", "maxTime", "minTotal", "maxTotal", "minTxsNum", "maxTxsNum", "minAvg", "maxAvg"]
    inlines = (NodeInline, )

class SessionAdmin(admin.ModelAdmin):
    fields = ["name"]
    inlines = (GroupInline, )

class CoinAdmin(admin.ModelAdmin):
    fields = ["name", "user"]
    readonly_fields = ('name', )
    inlines = (SessionInline, )

admin.site.register(Node)
admin.site.register(Group, GroupAdmin)
admin.site.register(Session, SessionAdmin)
admin.site.register(Coin, CoinAdmin)