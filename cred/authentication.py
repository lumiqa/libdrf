import logging

import requests
from django.conf import settings
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication
from rest_framework_jwt.settings import api_settings

from . import models

logger = logging.getLogger(__name__)

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER


class BaseSocialTokenAuthentication(BaseAuthentication):
    """
    Base class for exchanging a social access token for a JWT

    Validates that the token matches this app's client id, then
    fetches the profile info and finds or creates a user based on
    the account email.
    """

    def validate_token(self, token, request):
        raise NotImplementedError

    def fetch_email(self, token):
        raise NotImplementedError

    def authenticate(self, request):
        token = request.data.get('access_token', request.data.get('id_token'))
        if not token:
            return None

        email = self.validate_token(token, request)
        if not email:
            email = self.fetch_email(token)

        # Get or create user
        try:
            user = models.User.objects.get(email=email)
        except models.User.DoesNotExist:
            user = models.User.objects.create_user(email=email, is_active=True, is_verified=True)
            user.set_unusable_password()
            user.save()

        if not user.is_active:
            logger.info('{} is not active'.format(user))
            raise exceptions.AuthenticationFailed('Invalid user')

        if not user.is_verified:
            logger.info('{} is not verified'.format(user))
            raise exceptions.AuthenticationFailed('Invalid user')

        # Create a JWT
        payload = jwt_payload_handler(user)
        jwt = jwt_encode_handler(payload)

        return user, jwt


class GoogleOauth2TokenAuthentication(BaseSocialTokenAuthentication):
    """
    Auth backend to exchange a Google Oauth2 token for a JWT

    Validates that the token matches this app's client id, then
    fetches the profile info and finds or creates a user based on
    the google account email.
    """
    validation_url = 'https://www.googleapis.com/oauth2/v3/tokeninfo'
    user_url = 'https://www.googleapis.com/plus/v1/people/me'
    client_ids = settings.GOOGLE_OAUTH2_CLIENT_IDS

    def validate_token(self, token, request):
        # Validate token and make sure it's intended for this app
        param = 'id_token' if 'id_token' in request.data else 'access_token'
        resp = requests.get(self.validation_url, params={param: token})
        if not resp.ok:
            logger.info('Failed to validate Google Oauth2 token: {}'.format(resp.content))
            raise exceptions.AuthenticationFailed('Invalid token')
        payload = resp.json()
        if payload.get('aud') not in self.client_ids:
            logger.warning('Google Oauth2 token audience did not match client id: {} != {}'.format(payload.get('aud'), self.client_id))
            raise exceptions.AuthenticationFailed('Invalid token')
        email = payload.get('email')
        return email if payload.get('email_verified') else None

    def fetch_email(self, token):
        # Fetch user information
        resp = requests.get(self.user_url, params={'access_token': token})
        if not resp.ok:
            logger.info('Failed to get user data from Google Oauth2 token: {}'.format(resp.content))
            raise exceptions.AuthenticationFailed('Invalid token')

        payload = resp.json()
        email = [item['value'] for item in payload.get('emails', []) if item['type'] == 'account']
        if not email:
            logger.info('No google user email found')
            raise exceptions.AuthenticationFailed('Invalid user payload: {}'.format(payload))

        return email[0]


class FacebookTokenAuthentication(BaseSocialTokenAuthentication):
    """Auth backend to exchange a Facebook token for a JWT

    Validates that the token matches this app's client id and finds or
    creates a user based on the facebook account email.

    """

    validation_url = 'https://graph.facebook.com/debug_token'
    user_url = 'https://graph.facebook.com/me'
    app_id = settings.FACEBOOK_APP_ID
    app_secret = settings.FACEBOOK_APP_SECRET

    def validate_token(self, token, request):
        # Validate token and make sure it's intended for this app
        resp = requests.get(
            self.validation_url,
            params={
                'input_token': token,
                'access_token': '{}|{}'.format(self.app_id, self.app_secret)
            }
        )
        if not resp.ok:
            logger.info('Failed to validate Facebook token: {}'.format(resp.content))
            raise exceptions.AuthenticationFailed('Invalid token')
        payload = resp.json()['data']
        if payload.get('app_id') != self.app_id:
            logger.warning('Facebook token app id did not match app id: {} != {}'.format(
                payload.get('app_id'),
                self.app_id
            ))
            raise exceptions.AuthenticationFailed('Invalid token')
        if not payload.get('is_valid'):
            logger.warning('Facebook token was not valid: {}'.format(payload))
            raise exceptions.AuthenticationFailed('Invalid token')

    def fetch_email(self, token):
        # Fetch user information
        resp = requests.get(self.user_url, params={'access_token': token, 'fields': 'email'})
        if not resp.ok:
            logger.info('Failed to fetch user data from Facebook token: {}'.format(resp.content))
            raise exceptions.AuthenticationFailed('Invalid token')

        payload = resp.json()
        email = payload.get('email')
        if not email:
            logger.info('No facebook user email found')
            raise exceptions.AuthenticationFailed('Missing account email')
        return email
