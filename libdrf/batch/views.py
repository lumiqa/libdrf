import json
import logging

from django.db import transaction
from django.http.response import HttpResponseNotFound, HttpResponseServerError
from django.urls import resolve
from django.urls.exceptions import Resolver404
from rest_framework import generics, permissions
from rest_framework.response import Response

from .exceptions import BadBatchRequest
from .serializers import BatchRequestSerializer, BatchResponseSerializer
from .settings import batch_settings
from .utils import get_wsgi_request_object

logger = logging.getLogger(__name__)


def get_deserialized_response(wsgi_request):
    # Get the view / handler for this request
    try:
        view, args, kwargs = resolve(wsgi_request.path_info)
    except Resolver404 as exc:
        resp = HttpResponseNotFound()

    else:
        kwargs.update({"request": wsgi_request})

        # Let the view do his task.
        try:
            with transaction.atomic():
                resp = view(*args, **kwargs)
        except Exception as exc:
            logger.exception("Batch request server error")
            resp = HttpResponseServerError()

    headers = resp.headers.copy()

    # Convert HTTP response into simple dict type.
    d_resp = {
        "status_code": resp.status_code,
        "reason_phrase": resp.reason_phrase,
        "headers": headers,
        "path": wsgi_request.get_full_path(),
    }
    if hasattr(resp, "render"):
        resp.render()
        if not resp.content:
            body = None
        else:
            body = json.loads(resp.content)
    else:
        if not resp.content:
            body = None
        else:
            body = str(resp.content, "utf8")
    d_resp.update({"body": body})

    return d_resp


class BatchRequestView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, *args, **kwargs):

        serializer = BatchRequestSerializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        specs = serializer.validated_data["requests"]

        paths = ["{} {}".format(req["method"].upper(), req["path"]) for req in specs]
        logger.info("Batch requests:\n    {}".format("\n    ".join(paths)))
        requests = [
            get_wsgi_request_object(
                self.request,
                req["method"],
                req["path"],
                req.get("headers", {}),
                json.dumps(req["body"]) if req.get("body") else None,
            )
            for req in specs
        ]

        num_requests = len(requests)
        if num_requests > batch_settings.MAX_LIMIT:
            raise BadBatchRequest(
                "You can batch maximum of {} requests.".format(batch_settings.MAX_LIMIT)
            )
        responses = batch_settings.executor.execute(requests, get_deserialized_response)
        serializer = BatchResponseSerializer({"responses": responses})
        return Response(serializer.data)
