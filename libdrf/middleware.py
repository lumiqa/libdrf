import logging
from collections import Counter
from operator import itemgetter
from pprint import pformat

from django.db import connection
from django.test import override_settings

logger = logging.getLogger(__name__)


class LogSQLMiddleware:

    calls = Counter()
    queries = Counter()

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """Log the SQL queries that the request ran"""
        with override_settings(DEBUG=True):
            response = self.get_response(request)
        logger.info(
            "SQL Queries for request {}:\n{}".format(
                request.path,
                "\n".join(
                    "    [{}]: {}".format(q["time"], q["sql"])
                    for q in connection.queries
                ),
            )
        )
        logger.info(
            "Total SQL Queries for request {}: {}".format(
                request.path, len(connection.queries)
            )
        )
        self.calls[request.path] += 1
        self.queries[request.path] += len(connection.queries)
        averages = [
            (ep, self.queries[ep] / float(self.calls[ep]) if self.calls[ep] else 0.0)
            for ep in self.queries
        ]
        averages.sort(key=itemgetter(1))
        logger.info(
            "Endpoint averages:\n{}".format(
                "\n".join("{}: {}".format(ep, avg) for ep, avg in averages)
            )
        )
        return response
