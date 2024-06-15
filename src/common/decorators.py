import http
import logging
from functools import wraps
from typing import Callable, Optional

from fastapi import HTTPException

from common.context import CONTEXT_USER
from common.exceptions.rpc import UnauthorizedError, NotAdminException
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


def admin_required(handler: Callable) -> Callable:
    @wraps(handler)
    async def inner(*args, **kwargs):
        logger.info(f"Check admin at method {handler.__name__}")
        user: Optional[User] = CONTEXT_USER.get()
        if not user:
            logger.error(f"User unauthorized for handler {handler.__name__}")
            raise UnauthorizedError()

        if not user.is_admin:
            logger.error("User(email=%s) is not admin", user.email)
            raise NotAdminException()

        logger.info("User(email=%s) request handler=%s", user.email, handler.__name__)
        return await handler(*args, **kwargs)

    return inner


def rest_admin(handler: Callable) -> Callable:
    @wraps(handler)
    async def inner(*args, **kwargs):
        logger.info(f"Check admin at method {handler.__name__}")
        user: Optional[User] = CONTEXT_USER.get()
        if not user:
            logger.error(f"User unauthorized for handler {handler.__name__}")
            raise HTTPException(status_code=http.HTTPStatus.UNAUTHORIZED)

        if not user.is_admin:
            logger.error("User(email=%s) is not admin", user.email)
            raise HTTPException(status_code=http.HTTPStatus.FORBIDDEN)

        logger.info("User(email=%s) request handler=%s", user.email, handler.__name__)
        return await handler(*args, **kwargs)

    return inner
