import factory

from . import models


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.User

    email = factory.Sequence(lambda n: "user{}@example.com".format(n))
    password = 'supersecret'
    is_active = True
    is_verified = True
