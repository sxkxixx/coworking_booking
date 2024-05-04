from typing import Optional

import fastapi_jsonrpc as jsonrpc

from common.context import CONTEXT_USER
from common.dto.user import (
    UserProfile,
    TelegramInfoResponse,
    UpdateUserRequest,
    UserUpdateRequest,
    TokenResponse
)
from common.exceptions.rpc import Unauthorized
from common.session import TokenService
from infrastructure.database import User, UserTelegramInfo
from storage.user import AbstractUserRepository
from .abstract_rpc_router import AbstractRPCRouter


class UserRouter(AbstractRPCRouter):
    def __init__(
            self,
            user_repository: AbstractUserRepository,
            token_service: TokenService
    ) -> None:
        self.user_repository = user_repository
        self.token_service = token_service

    def build_entrypoint(self) -> jsonrpc.Entrypoint:
        entrypoint = jsonrpc.Entrypoint("/api/v1/user", tags=['USER'])
        entrypoint.add_method_route(self.get_profile)
        entrypoint.add_method_route(self.update_user_data)
        return entrypoint

    async def get_profile(self) -> UserProfile:
        user: User = CONTEXT_USER.get()
        if not user:
            raise Unauthorized()
        profile: Optional[UserTelegramInfo] = await self.user_repository.get_user_telegram_info(
            user.id)
        telegram_info = None
        if profile:
            telegram_info = TelegramInfoResponse.model_validate(profile, from_attributes=True)
        return UserProfile(
            id=user.id,
            email=user.email,
            last_name=user.last_name,
            first_name=user.first_name,
            patronymic=user.patronymic,
            is_student=user.is_student,
            avatar_filename=user.avatar_filename,
            telegram_info=telegram_info
        )

    async def update_user_data(self, values_set: UpdateUserRequest) -> UserUpdateRequest:
        user: User = CONTEXT_USER.get()
        if not user:
            raise Unauthorized()
        updated_user: User = await self.user_repository.update(
            user, **values_set.model_dump(exclude_none=True)
        )
        access_token = self.token_service.get_access_token(updated_user)
        return UserUpdateRequest(
            email=updated_user.email,
            last_name=updated_user.last_name,
            first_name=updated_user.first_name,
            patronymic=updated_user.patronymic,
            token=TokenResponse(access_token=access_token)
        )
