"""tracker URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.views.generic import RedirectView
from . import views

app_name = 'coin'
urlpatterns = [
    path('', views.home, name="home"),
    path('<uuid:session_id>', views.session, name='session'),
    path('basic', views.go_to_default_session),
    path('<uuid:session_id>/getKnown', views.get_known, name="getKnown"),
    path('<uuid:session_id>/change', views.change), #Change
    path('<uuid:session_id>/group/c', views.ExplorerView.as_view(), name='group'),
    path('<uuid:session_id>/getTxs', views.TransactionsAPIView.as_view(), name='get_txs'),
    path('<uuid:session_id>/getGraph', views.GraphAPIView.as_view(), name='getGraph'),
    path('<uuid:session_id>/addr/<str:addr>', views.ExplorerView.as_view(), name='addr'),
    path('<uuid:session_id>/group/<uuid:group_id>', views.ExplorerView.as_view(), name='group'),
    path('<uuid:session_id>/addSession', views.copy_session, name="copySession"),
    path('getTx/<str:tx>', views.get_tx),
    path('isUniqSession', views.is_uniq_session),
    path('isValidAddr', views.ValidAddressView.as_view()),
    path('addSession', views.add_session),
    path('delSession', views.del_session),
    path('editSession', views.edit_session),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)