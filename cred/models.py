from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils import timezone

from . import managers


class User(AbstractBaseUser, PermissionsMixin):
    """Admin-compliant user with email as username"""

    email = models.EmailField(unique=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    password_reset = models.DateTimeField(blank=True, null=True)

    objects = managers.UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def __str__(self):
        return "{}{}".format(
            self.email,
            " [{}]".format(self.profile.name) if hasattr(self, 'profile') else ''
        )

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        return self.email

    def get_short_name(self):
        "Returns the short name for the user."
        return self.email

    def verify(self):
        self.is_verified = True
        self.save(update_fields=['is_verified'])

    def activate(self):
        self.is_active = True
        self.save(update_fields=['is_active'])

    def deactivate(self):
        self.is_active = True
        self.save(update_fields=['is_active'])

    def change_password(self, pw):
        self.set_password(pw)
        self.password_reset = timezone.now()
        self.save()
