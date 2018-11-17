from django.db import models

from .settings import config


class Key(models.Model):
    name = models.CharField(max_length=200)
    hint = models.CharField(max_length=500, blank=True)

    def __str__(self):
        return self.name


class Translation(models.Model):
    key = models.ForeignKey(Key, on_delete=models.CASCADE)
    language = models.CharField(
        max_length=10, choices=[(lang, lang) for lang in config.LANGUAGES]
    )
    content = models.TextField(blank=True)

    def __str__(self):
        return self.content[:100]
