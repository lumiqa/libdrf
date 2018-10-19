from django.core.exceptions import ValidationError
from django.db import models


class EnumFieldMixin:

    def to_python(self, value):
        if value is None or value == '':
            return None
        if isinstance(value, self.enum):
            return value
        for m in self.enum:
            if value == m:
                return m
            if value == m.value or str(value) == str(m.value) or str(value) == str(m):
                return m
            if value == m.name or str(value) == str(m.name):
                return m
        raise ValidationError(
            '%s is not a valid value for enum %s' % (value, self.enum),
            code="invalid_enum_value"
        )

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs['enum'] = self.enum
        kwargs.pop('choices', None)
        return name, path, args, kwargs


class EnumCharField(EnumFieldMixin, models.CharField):

    def __init__(self, enum, **kwargs):
        self.enum = enum
        kwargs.setdefault("max_length", 10)
        kwargs.setdefault(
            "choices",
            [(i.name, getattr(i, 'label', i.name)) for i in self.enum]
        )
        super().__init__(**kwargs)
        self.validators = []

    def get_prep_value(self, value):
        if value is None:
            return None

        if isinstance(value, self.enum):
            return value.value

        return str(value)

    def to_python(self, value):
        if value is None or value == '':
            return None
        if isinstance(value, self.enum):
            return value
        for m in self.enum:
            if value == m:
                return m
            if value == m.value or str(value) == str(m.value) or str(value) == str(m):
                return m
        raise ValidationError('%s is not a valid value for enum %s' % (value, self.enum), code="invalid_enum_value")


class EnumIntegerField(EnumFieldMixin, models.IntegerField):

    def __init__(self, enum, **kwargs):
        self.enum = enum
        kwargs.setdefault(
            "choices",
            [(i.name, getattr(i, 'label', i.name)) for i in self.enum]
        )
        super().__init__(**kwargs)
        self.validators = []

    def get_prep_value(self, value):
        if value is None:
            return None

        if isinstance(value, self.enum):
            return value.value

        return int(value)
