from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import MailingListPreference


@receiver(post_save, sender=User)
def create_mailing_preference(sender, instance, created, **kwargs):
    """Auto-create a MailingListPreference when a new User is created."""
    if created:
        MailingListPreference.objects.get_or_create(user=instance)
