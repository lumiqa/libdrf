import logging
import random
from datetime import date
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand
from django.db.models import Max

from ... import models

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = ""

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry_run',
            action='store_true',
            dest='dry_run',
            default=False,
            help='Dry run',
        )

    def handle(self, *args, **options):
        for language in config.LANGUAGES:
            for translation in models.Translation.objects.all():
                pass
