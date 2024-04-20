from django.apps import AppConfig

default_app_config = 'pyupnp_services.PyUPnPServicesConfig'


class PyUPnPServicesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pyupnp_services'
