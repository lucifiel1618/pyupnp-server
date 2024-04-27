from django.contrib import admin
from . import models

admin.site.register(
    (
        models.Location,
        models.UserProfile,
        models.Device
    )
)
