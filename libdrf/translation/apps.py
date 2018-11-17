from django.apps import AppConfig


class TranslationConfig(AppConfig):
    name = 'libdrf.translation'

    def ready(self):
        # Importing decorated signal handlers here to avoid connecting
        # them multiple times and to avoid circular import issues
        from . import signals
