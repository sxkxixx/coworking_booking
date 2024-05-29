from typing import Optional

from common.session import TokenService
from infrastructure.database import User
from storage.user import AbstractUserRepository


class AuthRequired:
    def __init__(self, token_service: TokenService, user_repository: AbstractUserRepository):
        self.token_service = token_service
        self.user_repository = user_repository

    async def __call__(self, access_token: Optional[str]) -> Optional[User]:
        if not access_token:
            return None
        if not (payload := self.token_service.get_token_payload(access_token)):
            return None
        if not (email := payload.get('email', None)):
            return None
        user: Optional[User] = await self.user_repository.get(User.email == email)
        if not user:
            return None
        return user
