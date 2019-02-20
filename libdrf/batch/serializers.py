from rest_framework import serializers


class BatchRequestItemSerializer(serializers.Serializer):
    path = serializers.CharField()
    method = serializers.ChoiceField(
        choices=[
            ("get", "get"),
            ("post", "post"),
            ("put", "put"),
            ("patch", "patch"),
            ("delete", "delete"),
            ("GET", "GET"),
            ("POST", "POST"),
            ("PUT", "PUT"),
            ("PATCH", "PATCH"),
            ("DELETE", "DELETE"),
        ]
    )
    body = serializers.DictField(required=False)
    headers = serializers.DictField(required=False)

    def validate_method(self, method):
        return method.lower()


class BatchRequestSerializer(serializers.Serializer):
    requests = BatchRequestItemSerializer(many=True)


class BatchResponseItemSerializer(serializers.Serializer):
    status_code = serializers.IntegerField()
    reason_phrase = serializers.CharField()
    body = serializers.JSONField()
    headers = serializers.DictField(required=False)


class BatchResponseSerializer(serializers.Serializer):
    responses = BatchResponseItemSerializer(many=True)
