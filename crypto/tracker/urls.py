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
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name="home"),
    path('admin/', admin.site.urls),
    path('<str:coin>/', include('coin.urls')),
    path('signup', views.signup, name="signUp"),
    path('signin', views.signin, name="signIn"),
    path('signout', views.signout, name="signOut"),
    path('settings', views.acctSettings, name="acctSettings"),
    path('forgotpassword', views.forgotPass, name="forgotPass"),
    path('verify/<str:uidb64>', views.verifyEmail, name="verifyEmail"),
    path('passchange/<str:uidb64>/<str:token>/', views.passChange, name="passChange"),
    path('activate/<str:uidb64>/<str:token>/', views.activate, name="activate"),
    path('isUniqEmail', views.isUniqEmail, name="isUniqEmail"),
    path('isUniqUser', views.isUniqUserName, name="isUniqUserName"),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
