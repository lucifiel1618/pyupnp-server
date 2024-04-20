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

from django.contrib import admin
from django.urls import path, re_path
import filebrowser.sites
import pyupnp_services.views


# print(f'{settings.DEFAULT_FILE_STORAGE=}')
filebrowser.sites.site.storage.location = filebrowser.sites.site.storage.location + '/'
# print(f'{filebrowser.sites.site.storage.location=} + {filebrowser.sites.site.directory=}')
# print(f'{filebrowser.sites.site.urls}')
urlpatterns = [
    path('admin/filebrowser/', filebrowser.sites.site.urls),
    path('admin/', admin.site.urls),
    path('dev<int:device_id>/device_detail.xml', pyupnp_services.views.device_detail, name='device_detail'),
    path('dev<int:device_id>/srv<int:service_id>.xml', pyupnp_services.views.service_detail, name='service_detail'),
    path('dev<int:device_id>/srv<int:service_id>/ctl', pyupnp_services.views.service_control, name='service_control'),
    path('dev<int:device_id>/srv<int:service_id>/evt', pyupnp_services.views.service_event, name='service_event'),
    re_path(r'^media/(.*)', pyupnp_services.views.file_view)
]
