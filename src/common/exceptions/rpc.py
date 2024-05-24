from fastapi_jsonrpc import BaseError


class RegisterError(BaseError):
    CODE = -32001
    MESSAGE = 'Error while registering error'


class AuthenticationError(BaseError):
    CODE = -32002
    MESSAGE = 'Invalid credentials'


class SessionError(BaseError):
    CODE = -32003
    MESSAGE = 'Session is invalid'


class UnauthorizedError(BaseError):
    CODE = -32004
    MESSAGE = 'UnauthorizedError'


class ReservationException(BaseError):
    CODE = -32005
    MESSAGE = 'Reservation exception'


class UserNotExistsException(BaseError):
    CODE = -32006
    MESSAGE = 'User does not exist'


class ResetPasswordException(BaseError):
    CODE = -32007
    MESSAGE = "Reset password exception"


class CoworkingDoesNotExistException(BaseError):
    CODE = -32008
    MESSAGE = 'Coworking does not exists'
