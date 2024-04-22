import contextvars

from infrastructure.database import User

CONTEXT_USER: contextvars.ContextVar[User] = contextvars.ContextVar('CONTEXT_USER')
