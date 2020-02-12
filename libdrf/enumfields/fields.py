from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.fields import BLANK_CHOICE_DASH
from django.forms import TypedChoiceField
from django.forms.fields import TypedMultipleChoiceField
from django.utils.encoding import force_text


class EnumChoiceFieldMixin(object):
    def prepare_value(self, value):
        # Widgets expect to get strings as values.

        if value is None:
            return ''
        if hasattr(value, "value"):
            value = value.value
        return force_text(value)

    def valid_value(self, value):
        if hasattr(value, "value"):  # Try validation using the enum value first.
            if super(EnumChoiceFieldMixin, self).valid_value(value.value):
                return True
        return super(EnumChoiceFieldMixin, self).valid_value(value)


class EnumChoiceField(EnumChoiceFieldMixin, TypedChoiceField):
    pass


class EnumMultipleChoiceField(EnumChoiceFieldMixin, TypedMultipleChoiceField):
    pass


class CastOnAssignDescriptor(object):
    """
    A property descriptor which ensures that `field.to_python()` is called on _every_ assignment to the field.

    This used to be provided by the `django.db.models.subclassing.Creator` class, which in turn
    was used by the deprecated-in-Django-1.10 `SubfieldBase` class, hence the reimplementation here.
    """

    def __init__(self, field):
        self.field = field

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        return obj.__dict__[self.field.name]

    def __set__(self, obj, value):
        obj.__dict__[self.field.name] = self.field.to_python(value)


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

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def value_to_string(self, obj):
        """
        This method is needed to support proper serialization. While its name is value_to_string()
        the real meaning of the method is to convert the value to some serializable format.
        Since most of the enum values are strings or integers we WILL NOT convert it to string
        to enable integers to be serialized natively.
        """
        value = self._get_val_from_obj(obj)
        return value.value if value else None

    def formfield(self, form_class=None, choices_form_class=None, **kwargs):
        if not choices_form_class:
            choices_form_class = EnumChoiceField
        return super(EnumFieldMixin, self).formfield(form_class=form_class, choices_form_class=choices_form_class, **kwargs)

    def contribute_to_class(self, cls, name):
        super(EnumFieldMixin, self).contribute_to_class(cls, name)
        setattr(cls, name, CastOnAssignDescriptor(self))

    def get_choices(self, include_blank=True, blank_choice=BLANK_CHOICE_DASH):
        # Force enum fields' options to use the `value` of the enumeration
        # member as the `value` of SelectFields and similar.
        return [
            (i.value if isinstance(i, self.enum) else i, display)
            for (i, display)
            in super(EnumFieldMixin, self).get_choices(include_blank, blank_choice)
        ]


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
            [(i, getattr(i, 'label', i.name)) for i in self.enum]
        )
        super().__init__(**kwargs)
        self.validators = []

    def get_prep_value(self, value):
        if value is None:
            return None

        if isinstance(value, self.enum):
            return value.value

        try:
            return int(value)
        except ValueError:
            return self.to_python(value).value

        return int(value)
