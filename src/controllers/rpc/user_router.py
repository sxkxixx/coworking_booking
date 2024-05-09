from typing import Optional

import fastapi_jsonrpc as jsonrpc

from common.context import CONTEXT_USER
from common.dto.user import (
    UpdateUserRequest,
    UserUpdateRequest,
    TokenResponse, UserResponseDTO
)
from common.exceptions.rpc import Unauthorized
from common.session import TokenService
from infrastructure.database import User
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

    async def get_profile(self) -> UserResponseDTO:
        user: Optional[User] = CONTEXT_USER.get()
        if not user:
            raise Unauthorized()
        return UserResponseDTO.model_validate(user, from_attributes=True)

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
