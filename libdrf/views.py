from rest_framework import status
from rest_framework.response import Response


class ReadWriteSerializerMixin:
    """
    Support for overriding serializer based on read/write
    serialization
    """

    def get_write_serializer(self, *args, **kwargs):
        return self.get_serializer(serializer_direction="write", *args, **kwargs)

    def get_read_serializer(self, *args, **kwargs):
        return self.get_serializer(serializer_direction="read", *args, **kwargs)

    def get_serializer(self, *args, **kwargs):
        """
        Return the serializer instance that should be used for validating and
        deserializing input, and for serializing output.
        """
        direction = kwargs.pop("serializer_direction", "read")
        serializer_class = self.get_serializer_class(serializer_direction=direction)
        kwargs["context"] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)

    def get_serializer_class(self, serializer_direction=""):
        serializer_variable = "{}_serializer_class".format(serializer_direction)
        serializer_class = getattr(self, serializer_variable, self.serializer_class)
        assert serializer_class is not None, (
            "'%s' should either include a `serializer_class` attribute, "
            "or override the `get_serializer_class()` method." % self.__class__.__name__
        )
        return serializer_class

    def perform_create(self, serializer):
        return serializer.save()

    def perform_update(self, serializer):
        return serializer.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_write_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        serializer = self.get_read_serializer(serializer.instance)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_write_serializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        instance = self.perform_update(serializer)
        serializer = self.get_read_serializer(instance)
        return Response(serializer.data)
