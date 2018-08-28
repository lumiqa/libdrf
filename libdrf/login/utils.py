import jwt
from rest_framework.exceptions import AuthenticationFailed
from .settings import login_settings
from datetime import datetime
from calendar import timegm

from .models import User


def jwt_get_secret_key(payload=None):
    try:
        user = User.objects.active().get(pk=payload.get('user_id'))
    except User.DoesNotExist:
        raise AuthenticationFailed('Invalid user')

    if user.password_reset:
        return '{}:{}:{}'.format(
            login_settings.JWT_SECRET_KEY,
            user.pk,
            user.password_reset.timestamp()
        )
    else:
        return '{}:{}'.format(
            login_settings.JWT_SECRET_KEY,
            user.pk
        )


def jwt_payload_handler(user):
    payload = {
        'user_id': user.pk,
        'exp': datetime.utcnow() + login_settings.JWT_EXPIRATION_DELTA
    }

    # Include original issued at time for a brand new token,
    # to allow token refresh
    if login_settings.JWT_ALLOW_REFRESH:
        payload['orig_iat'] = timegm(
            datetime.utcnow().utctimetuple()
        )

    return payload


def jwt_encode_handler(payload):
    key = jwt_get_secret_key(payload)
    return jwt.encode(
        payload,
        key,
        login_settings.JWT_ALGORITHM
    ).decode('utf-8')


def jwt_decode_handler(token):
    options = {
        'verify_exp': login_settings.JWT_VERIFY_EXPIRATION,
    }
    # get user from token, BEFORE verification, to get user secret key
    unverified_payload = jwt.decode(token, None, False)
    secret_key = jwt_get_secret_key(unverified_payload)
    return jwt.decode(
        token,
        secret_key,
        login_settings.JWT_VERIFY,
        options=options,
        leeway=login_settings.JWT_LEEWAY,
        audience=login_settings.JWT_AUDIENCE,
        issuer=login_settings.JWT_ISSUER,
        algorithms=[login_settings.JWT_ALGORITHM]
    )


def jwt_response_payload_handler(token, user=None, request=None):
    return {
        'token': token
    }


def activation_link_builder(user, token):
    return '{}/activate/{}/{}'.format(
        login_settings.WEBSITE_BASE_URL,
        user.id,
        token
    )
