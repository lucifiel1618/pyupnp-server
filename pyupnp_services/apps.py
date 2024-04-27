from django.apps import AppConfig


class PyUPnPServicesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pyupnp_services'
    verbose_name = 'PyUPNP Services'

    def ready(self) -> None:
        import pyupnp_services.signals  # noqa
