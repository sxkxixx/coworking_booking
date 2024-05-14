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


class Weekday(enum.Enum):
    """Enum для определения дня недели"""

    MONDAY: int = 0
    TUESDAY: int = 1
    WEDNESDAY: int = 2
    THURSDAY: int = 3
    FRIDAY: int = 4
    SATURDAY: int = 5
    SUNDAY: int = 6


class BookingStatus(enum.Enum):
    NEW: str = 'new'
    AWAIT_CONFIRM: str = 'await_confirm'
    CONFIRMED: str = 'confirmed'
    CANCELLED: str = 'cancelled'
    PASSED: str = 'passed'


class PasswordTokenEnum(enum.Enum):
    NEW = 'new'
    USED = 'used'
