from django.db.models import signals
from django.dispatch import receiver
from django.conf import settings
from .models import UserProfile


@receiver(signals.post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(signals.post_save, sender=settings.AUTH_USER_MODEL)
def save_profile(sender, instance, **kwargs):
    instance.userprofile.save()
