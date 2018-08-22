import re

from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from rest_framework import exceptions, serializers
from rest_framework_jwt.settings import api_settings

from . import models

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER


class SocialTokenValidationSerializer(serializers.Serializer):
    access_token = serializers.CharField()


class ActivationSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    token = serializers.CharField()

    def validate_user_id(self, value):
        try:
            self.user = models.User.objects.get(pk=value)
        except models.User.DoesNotExist:
            raise serializers.ValidationError("Invalid user_id")
        return value

    def validate(self, attrs):
        # HOTFIX: remove get params from token. Remove this when app
        # is updated.
        match = re.match(r'[\w-]+', attrs['token'])
        if not match:
            raise serializers.ValidationError('Invalid validation token')

        attrs['token'] = match.group(0)
        if not default_token_generator.check_token(self.user, attrs['token']):
            raise serializers.ValidationError('Invalid validation token')
        return attrs


class RegistrationSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.User
        fields = [
            'email',
            'password',
        ]

    def validate_email(self, value):
        try:
            models.User.objects.get(email__iexact=value)
        except models.User.DoesNotExist:
            return value.lower()
        raise serializers.ValidationError('existing user')


class ResendActivationSerializer(serializers.Serializer):
    email = serializers.EmailField()


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'})

    def validate_email(self, value):
        return value.lower()

    def validate(self, attrs):
        credentials = {
            'email': attrs.get('email'),
            'password': attrs.get('password')
        }

        if not all(credentials.values()):
            raise serializers.ValidationError('invalid credentials')

        user = authenticate(**credentials)
        if not user:
            raise serializers.ValidationError('invalid credentials')

        if not user.is_verified:
            raise exceptions.PermissionDenied('unverified user')

        payload = jwt_payload_handler(user)

        return {
            'token': jwt_encode_handler(payload),
            'user': user
        }


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.User
        fields = [
            'id',
            'email',
        ]


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.CharField()


class ChangePasswordAuthenticatedSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=False)
    password = serializers.CharField(min_length=6)

    def validate(self, attrs):
        user = self.context['request'].user
        if user.has_usable_password() and not user.check_password(attrs['old_password']):
            # Keep 'non_field_errors' for mobile apps
            raise serializers.ValidationError({'old_password': 'Invalid old password' , 'non_field_errors': 'Invalid old password'})
        self.user = user
        return attrs


class ChangePasswordLinkSerializer(ActivationSerializer):
    password = serializers.CharField(min_length=6)
