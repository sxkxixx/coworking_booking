import logging
from functools import wraps
from typing import Callable, Optional

from common.context import CONTEXT_USER
from common.exceptions.rpc import UnauthorizedError
from infrastructure.database import User

logger = logging.getLogger(__name__)


def login_required(handler: Callable) -> Callable:
    @wraps(handler)
    async def inner(*args, **kwargs):
        logger.info(f"Check user at method {handler.__name__}")
        user: Optional[User] = CONTEXT_USER.get()
        if not user:
            logger.error(f"User unauthorized for handler {handler.__name__}")
            raise UnauthorizedError()
        logger.info("User(email=%s) request handler=%s", user.email, handler.__name__)
        return await handler(*args, **kwargs)

    return inner
