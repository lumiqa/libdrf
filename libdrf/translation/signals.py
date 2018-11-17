import logging

from django.db.models import signals
from django.dispatch import receiver

from . import models
from .settings import config

logger = logging.getLogger(__name__)


@receiver(signals.post_save, sender="translation.Key")
def key_post_save(sender, instance, **kwargs):
    for language in config.LANGUAGES:
        translation, created = models.Translation.objects.get_or_create(
            key=instance, language=language
        )
