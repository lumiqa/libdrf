import logging
import time

import django_rq
from croniter import croniter
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

logger = logging.getLogger(__name__)


class Job:

    def __init__(self, cron, cmd, queue, *args, **kwargs):
        self.cron = cron
        self.cmd = cmd
        self.queue = django_rq.get_queue(queue)
        self.args = args
        self.kwargs = kwargs
        self.time_iterator = croniter(self.cron, timezone.now())
        self.next_run = next(self.time_iterator)

    def __str__(self):
        return '{}({})'.format(
            self.cmd,
            ', '.join(
                [repr(arg) for arg in self.args] +
                ['{}={!r}'.format(k, v) for k, v in self.kwargs.items()]
            )
        )

    def should_run(self):
        return timezone.now().timestamp() >= self.next_run

    def enqueue(self):
        self.queue.enqueue(call_command, self.cmd, *self.args, **self.kwargs)
        self.next_run = next(self.time_iterator)


class Command(BaseCommand):
    help = "Start scheduling cron jobs to RQ"

    def handle(self, *args, **options):
        cron_settings = getattr(settings, 'LIBDRF_CRON', {})
        default_queue = cron_settings.get('default_queue', 'cron')
        job_specs = cron_settings.get('jobs', [])

        if not job_specs:
            logger.warning("No jobs in LIBDRF_CRON['jobs']")
            return

        jobs = [
            Job(
                j['cron'],
                j['cmd'],
                j.get('queue', default_queue),
                *j.get('args', []),
                **j.get('kwargs', {})
            )
            for j in job_specs
        ]

        logger.info('Running with {} jobs:\n {}'.format(
            len(jobs),
            '\n'.join('\t{} -> {}'.format(job.cron, job) for job in jobs)
        ))
        while True:
            for job in jobs:
                if job.should_run():
                    logger.info('Scheduling job: {}'.format(job))
                    job.enqueue()
            time.sleep(30)
