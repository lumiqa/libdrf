import datetime

from django.conf import settings
from rest_framework.settings import APISettings


USER_SETTINGS = getattr(settings, 'CRED', None)

DEFAULTS = {
    'JWT_ENCODE_HANDLER':
    'cred.utils.jwt_encode_handler',

    'JWT_DECODE_HANDLER':
    'cred.utils.jwt_decode_handler',

    'JWT_PAYLOAD_HANDLER':
    'cred.utils.jwt_payload_handler',

    'JWT_RESPONSE_PAYLOAD_HANDLER':
    'cred.utils.jwt_response_payload_handler',

    'JWT_SECRET_KEY': settings.SECRET_KEY,
    'JWT_ALGORITHM': 'HS256',
    'JWT_VERIFY': True,
    'JWT_VERIFY_EXPIRATION': True,
    'JWT_LEEWAY': 0,
    'JWT_EXPIRATION_DELTA': datetime.timedelta(seconds=300),
    'JWT_AUDIENCE': None,
    'JWT_ISSUER': None,

    'JWT_ALLOW_REFRESH': False,
    'JWT_REFRESH_EXPIRATION_DELTA': datetime.timedelta(days=7),

    'JWT_AUTH_HEADER_PREFIX': 'JWT',
}

# List of settings that may be in string import notation.
IMPORT_STRINGS = (
    'JWT_ENCODE_HANDLER',
    'JWT_DECODE_HANDLER',
    'JWT_PAYLOAD_HANDLER',
    'JWT_RESPONSE_PAYLOAD_HANDLER',
)

api_settings = APISettings(USER_SETTINGS, DEFAULTS, IMPORT_STRINGS)
