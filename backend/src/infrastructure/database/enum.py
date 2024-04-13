import enum


class OnDelete(enum.Enum):
    CASCADE: str = 'CASCADE'
    SET_NULL: str = 'SET NULL'
    RESTRICT: str = 'RESTRICT'
    SET_DEFAULT: str = 'SET DEFAULT'


class PlaceType(enum.Enum):
    """Enum для определения типа места для бронирования"""

    MEETING_ROOM: str = 'meeting_room'
    """Комната для переговоров"""

    TABLE: str = 'table'
    """Стол"""
