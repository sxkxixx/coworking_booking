from fastapi_jsonrpc import BaseError


class RegisterError(BaseError):
    CODE = -32001
    MESSAGE = 'Error while registering error'


class AuthenticationError(BaseError):
    CODE = -32002
    MESSAGE = 'Incorrect email or password'
