import re
from unittest import mock

from django.core import mail
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .settings import login_settings

from . import factories, models

jwt_decode_handler = login_settings.JWT_DECODE_HANDLER


class RegistrationTestCase(APITestCase):

    @override_settings(USER_ACTIVATION=True)
    def test_email_registration(self):
        reg_payload = {
            'email': 'customer@example.com',
            'password': 'banana',
        }

        outbox_size = len(mail.outbox)

        resp = self.client.post(reverse('register'), reg_payload)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        # Check user and customer are inactive
        u = models.User.objects.get(email=reg_payload.get('email'))
        self.assertFalse(u.is_verified)

        # Get the validation code from the email
        self.assertEqual(len(mail.outbox), outbox_size + 1)
        registration_email = mail.outbox[-1]
        match = re.search(r'/activate/(.+?)/(\S+)', registration_email.body)
        self.assertIsNotNone(match)
        user_id, token = match.groups()

        # Validate
        val_payload = {
            'user_id': user_id,
            'token': token,
        }
        resp = self.client.post(reverse('activate'), val_payload)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        # Check that user is active
        u.refresh_from_db()
        self.assertTrue(u.is_verified)

    @override_settings(USER_ACTIVATION=False)
    def test_email_registration_existing_email(self):
        factories.UserFactory(email='test@example.com')
        reg_payload = {
            'email': 'test@example.com',
            'password': 'banana',
        }
        resp = self.client.post(reverse('register'), reg_payload)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_email_login(self):
        user = factories.UserFactory(email='test@example.com')
        user.set_password('supersecret')
        user.save()
        payload = {'email': 'test@example.com', 'password': 'supersecret'}
        resp = self.client.post(reverse('login'), payload)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(len(resp.json()['token']) > 0)
        payload = {'email': 'Test@example.com', 'password': 'supersecret'}
        resp = self.client.post(reverse('login'), payload)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(len(resp.json()['token']) > 0)

    def test_change_password_authenticated(self):
        user = factories.UserFactory(email='test@example.com')
        user.set_password('supersecret')
        user.save()
        self.client.force_authenticate(user)
        payload = {'old_password': 'banana', 'password': 'newpass'}
        resp = self.client.post(reverse('change-password'), payload)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        payload = {'old_password': 'supersecret', 'password': 'newpass'}
        resp = self.client.post(reverse('change-password'), payload)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    @override_settings(USER_ACTIVATION=False)
    def test_email_case_sensitivity(self):
        reg_payload = {
            'email': 'Test@example.com',
            'password': 'banana',
        }
        resp = self.client.post(reverse('register'), reg_payload)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(models.User.objects.count(), 1)
        self.assertEqual(models.User.objects.get().email, 'test@example.com')

    @mock.patch.multiple(
        'login.authentication.GoogleOauth2TokenAuthentication',
        validate_token=mock.DEFAULT,
        fetch_email=mock.DEFAULT
    )
    def test_google_registration(self, validate_token, fetch_email):
        validate_token.return_value = None
        fetch_email.return_value = 'customer@example.com'

        reg_payload = {
            'access_token': 'banana',
        }

        resp = self.client.post(reverse('validate_google_token'), reg_payload)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        token = resp.json()['token']
        payload = jwt_decode_handler(token)
        u = models.User.objects.get(pk=payload.get('user_id'))
        self.assertFalse(u.has_usable_password())
        self.assertTrue(u.is_verified)
