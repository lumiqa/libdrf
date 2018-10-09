from enum import Enum


class FlexEnum(Enum):
    """Enum that can be compared to instances of their value"""

    @classmethod
    def as_choices(cls):
        return [(e.value, e.name) for e in cls]

    def __str__(self):
        return self.name

    def __hash__(self):
        return super().__hash__()

    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other
        if isinstance(other, int):
            return self.value == other
        else:
            return super().__eq__(other)
