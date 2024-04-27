"""
URL configuration for pyupnp_server project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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

import django.contrib.admin
import django.contrib.auth.views
from django.contrib.auth.decorators import login_required
from django.urls import include, path, re_path
import filebrowser.sites
import pyupnp_services.views
from . import views

# print(f'{settings.DEFAULT_FILE_STORAGE=}')
filebrowser.sites.site.storage.location = filebrowser.sites.site.storage.location + '/'
# print(f'{filebrowser.sites.site.storage.location=} + {filebrowser.sites.site.directory=}')
# print(f'{filebrowser.sites.site.urls}')
urlpatterns = [
    path(r'grappelli/', include('grappelli.urls')),
    path('admin/filebrowser/', filebrowser.sites.site.urls),
    path('admin/logout/', views.logout_view),
    path('admin/', django.contrib.admin.site.urls),
    path('', login_required(views.Index.as_view()), name='index'),
    path('i18n/', include('django.conf.urls.i18n')),
    path('accounts/profile/', views.AccountProfile.as_view(), name='account_profile'),
    re_path(r'^accounts/login/$', django.contrib.auth.views.LoginView.as_view(template_name='admin/login.html')),
    re_path(r'^accounts/logout/$', views.logout_view),
    path('accounts/', include('django.contrib.auth.urls')),
    path(
        'dev<int:device_id>/device_detail.xml',
        login_required(pyupnp_services.views.device_detail),
        name='device_detail'
    ),
    path(
        'dev<int:device_id>/srv<int:service_id>.xml',
        login_required(pyupnp_services.views.service_detail),
        name='service_detail'
    ),
    path(
        'dev<int:device_id>/srv<int:service_id>/ctl',
        login_required(pyupnp_services.views.service_control),
        name='service_control'
    ),
    path(
        'dev<int:device_id>/srv<int:service_id>/evt',
        login_required(pyupnp_services.views.service_event),
        name='service_event'
    ),
    re_path(r'^media/(.*)', pyupnp_services.views.file_view),
    re_path(r'^resource/(.*)', pyupnp_services.views.resource_access)
]
