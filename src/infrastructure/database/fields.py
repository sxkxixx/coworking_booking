import enum
from typing import Type

import peewee


class CharEnum(peewee.CharField):
    def __init__(self, _enum: Type[enum.Enum], *args, **kwargs):
        self._enum: Type[enum.Enum] = _enum
        super().__init__(*args, **kwargs)

    def db_value(self, value: enum.Enum) -> str:
        assert isinstance(value, self._enum), f'Enum object {value} is not instance of {self._enum}'
        value = self._enum(value)
        return str(value.value)

    def python_value(self, value: str) -> enum.Enum:
        return self._enum(value)
