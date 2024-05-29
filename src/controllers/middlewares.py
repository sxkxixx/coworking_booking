from typing import Optional

from fastapi import Request, Response

from common.context import CONTEXT_USER
from common.dependencies.auth import AuthRequired
from common.session import TokenService
from infrastructure.database import User
from storage.user import AbstractUserRepository


class AuthMiddleware:
    def __init__(
            self,
            token_service: TokenService,
            user_repository: AbstractUserRepository
    ):
        self.auth_dependency = AuthRequired(token_service, user_repository)

    async def __call__(self, request: Request, call_next):
        user: Optional[User] = await self.auth_dependency(request.headers.get("Authorization"))
        CONTEXT_USER.set(user)
        response: Response = await call_next(request)
        return response
