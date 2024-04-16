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

    MONDAY: str = 'monday'
    TUESDAY: str = 'tuesday'
    WEDNESDAY: str = 'wednesday'
    THURSDAY: str = 'thursday'
    FRIDAY: str = 'friday'
    SATURDAY: str = 'saturday'
    SUNDAY: str = 'sunday'


class BookingStatus(enum.Enum):
    NEW: str = 'new'
    AWAIT_CONFIRM: str = 'await_confirm'
    CONFIRMED: str = 'confirmed'
    CANCELLED: str = 'cancelled'
