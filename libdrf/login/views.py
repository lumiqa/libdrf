import logging

from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.reverse import reverse

from . import authentication, models, serializers, utils
from .settings import login_settings

logger = logging.getLogger(__name__)


# Social auth

class BaseTokenExchangeView(generics.GenericAPIView):
    """
    Base class to validate a social token and return a JWT
    """
    serializer_class = serializers.SocialTokenValidationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        return Response({'token': request.auth}, status=status.HTTP_200_OK)


class GoogleTokenExhangeView(BaseTokenExchangeView):
    """
    Exchange a valid Google Oauth2 token for a JWT token.

    Creates a new user if no user with matching email is found.
    """
    authentication_classes = [authentication.GoogleOauth2TokenAuthentication]


class FacebookTokenExhangeView(BaseTokenExchangeView):
    """
    Exchange a valid Facebook access token for a JWT token.

    Creates a new user if no user with matching email is found.
    """
    authentication_classes = [authentication.FacebookTokenAuthentication]


# Email account auth flow

class RegistrationView(generics.GenericAPIView):
    """
    Register user via email and password. Sends activation email.
    """
    serializer_class = serializers.RegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        verified = False if login_settings.USER_ACTIVATION else True

        user = models.User.objects.create_user(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password'],
            is_verified=verified
        )
        logger.info('Registered user {}'.format(user.pk))
        if not user.is_verified:
            self.send_activation_email(user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def send_activation_email(self, user):
        token = default_token_generator.make_token(user)
        url = login_settings.ACTIVATION_LINK_BUILDER(user, token)

        html_message = render_to_string(
            'login/email-activation.html',
            {'url': url, 'email': login_settings.EMAIL_FROM}
        )
        text_message = render_to_string(
            'login/email-activation.txt',
            {'url': url, 'email': login_settings.EMAIL_FROM}
        )
        logger.info('Sending activation email to user {}'.format(user.pk))
        send_mail(
            subject=_('confirm_email_subject'),
            message=text_message,
            html_message=html_message,
            from_email=login_settings.EMAIL_FROM,
            recipient_list=[user.email],
        )


class UnregistrationView(generics.GenericAPIView):
    """
    Delete user unless they already have a profile.

    Use when cancelling registration process.

    """
    serializer_class = serializers.RegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            profile = self.request.user.profile
        except ObjectDoesNotExist:
            self.request.user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            raise PermissionDenied


class ResendActivationView(RegistrationView):
    """
    Resends activation email for provided address
    """
    serializer_class = serializers.ResendActivationSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = models.User.objects.get(
                is_verified=False,
                email=serializer.validated_data['email']
            )
        except models.User.DoesNotExist:
            pass
        else:
            self.send_activation_email(user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ActivationView(generics.GenericAPIView):
    """
    Activate a user with the user id and token from the validation email
    """
    serializer_class = serializers.ActivationSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user
        user.verify()
        payload = utils.jwt_payload_handler(user)
        jwt = utils.jwt_encode_handler(payload)
        response_data = utils.jwt_response_payload_handler(jwt)
        return Response(response_data)


class ResetPasswordView(generics.GenericAPIView):
    """
    Send a password reset link
    """
    serializer_class = serializers.ResetPasswordSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = models.User.objects.get(
                email__iexact=serializer.validated_data['email']
            )
        except models.User.DoesNotExist:
            pass
        else:
            self.send_reset_password_email(user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def send_reset_password_email(self, user):
        path = reverse(
            'change-password-link',
            kwargs={
                'user_id': user.id,
                'token': default_token_generator.make_token(user)
            }
        )
        url = self.request.build_absolute_uri(path)
        html_message = render_to_string(
            'login/email-password-change.html',
            {'url': url, 'email': login_settings.EMAIL_FROM}
        )
        text_message = render_to_string(
            'login/email-password-change.txt',
            {'url': url, 'email': login_settings.EMAIL_FROM}
        )
        logger.info('Reset link for {}: {}'.format(user, url))
        send_mail(
            subject="Återställning av lösenord",
            message=text_message,
            html_message=html_message,
            from_email=login_settings.EMAIL_FROM,
            recipient_list=[user.email],
        )


class ChangePasswordLinkView(generics.GenericAPIView):
    """
    Change password using email token
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.ChangePasswordLinkSerializer

    def put(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        serializer.user.set_password(serializer.validated_data['password'])
        serializer.user.save()

        payload = utils.jwt_payload_handler(serializer.user)
        jwt = utils.jwt_encode_handler(payload)
        response_data = utils.jwt_response_payload_handler(jwt)
        return Response(response_data)


class ChangePasswordView(generics.GenericAPIView):
    """
    Change password while logged in
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.ChangePasswordAuthenticatedSerializer

    def put(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        serializer.user.set_password(serializer.validated_data['password'])
        serializer.user.save()

        payload = utils.jwt_payload_handler(serializer.user)
        jwt = utils.jwt_encode_handler(payload)
        response_data = utils.jwt_response_payload_handler(jwt)
        return Response(response_data)


class LoginView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.LoginSerializer

    def post(self, request):
        serializer = self.get_serializer(
            data=request.data
        )
        if serializer.is_valid():
            user = serializer.validated_data.get('user') or request.user
            token = serializer.validated_data.get('token')
            response_data = utils.jwt_response_payload_handler(
                token,
                user,
                request
            )
            return Response(response_data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.EmptySerializer

    def post(self, *args, **kwargs):
        # TODO: Perform token blacklisting or whatever here..
        return Response(status=status.HTTP_200_OK)


class UserView(generics.RetrieveAPIView):
    serializer_class = serializers.UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
