from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from . import views

app_name = 'btc'

urlpatterns = [
    path('admin/', admin.site.urls, name='admin'),
    path('search/<str:id>', views.search, name='search'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)