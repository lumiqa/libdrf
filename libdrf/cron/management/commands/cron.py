import logging
from time import sleep

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
        return "{}({})".format(
            self.cmd,
            ", ".join(
                [repr(arg) for arg in self.args]
                + ["{}={!r}".format(k, v) for k, v in self.kwargs.items()]
            ),
        )

    def should_run(self):
        return timezone.now().timestamp() >= self.next_run

    def enqueue(self):
        self.queue.enqueue(call_command, self.cmd, *self.args, **self.kwargs)
        for next_run in self.time_iterator:
            if next_run > timezone.now():
                logger.info("Next run for {} at {}".format(self, next_run))
                self.next_run = next_run
                break
            logger.info("Skipping next run in the past: {}".format(next_run))


class Command(BaseCommand):
    """"Schedule tasks periodically

    Runs management commands on a schedule. Example config:

    LIBDRF_CRON = {
        "default_queue": "cron",
        "jobs": [
            {"cron": "0 * * * *", "cmd": "run_task", "args": ["arg1"], "kwargs": {"kwarg1": "foo"}},
            ...
        ]
    }

    """

    help = "Start scheduling cron jobs to RQ"

    def run(self):
        logger.info("Checking {} cron jobs".format(len(self.jobs)))
        for job in self.jobs:
            if job.should_run():
                logger.info("Scheduling job: {}".format(job))
                job.enqueue()

    def handle(self, *args, **options):
        cron_settings = getattr(settings, "LIBDRF_CRON", {})
        default_queue = cron_settings.get("default_queue", "cron")
        job_specs = cron_settings.get("jobs", [])

        if not job_specs:
            logger.warning("No jobs in LIBDRF_CRON['jobs']")
            return

        self.jobs = [
            Job(
                j["cron"],
                j["cmd"],
                j.get("queue", default_queue),
                *j.get("args", []),
                **j.get("kwargs", {})
            )
            for j in job_specs
        ]

        logger.info(
            "Running with {} jobs:\n {}".format(
                len(self.jobs),
                "\n".join("\t{} -> {}".format(job.cron, job) for job in self.jobs),
            )
        )
        while True:
            self.run()
            sleep(60)
