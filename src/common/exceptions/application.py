class CoworkingNonBusinessDayException(Exception):
    """Exception when there is attempt to create booking at not working date"""


class NotAllowedReservationTimeException(Exception):
    """Exception when there are not allowed time to create a reservation"""


class CoworkingNotExistsException(Exception):
    """Not exist coworking exception"""
