from typing import Optional

import fastapi_jsonrpc as jsonrpc

from common.context import CONTEXT_USER
from common.dto.user import (
    UpdateUserRequest,
    UserResponseDTO
)
from common.exceptions.rpc import UnauthorizedError
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
            raise UnauthorizedError()
        return UserResponseDTO.model_validate(user, from_attributes=True)

    async def update_user_data(self, values_set: UpdateUserRequest) -> UserResponseDTO:
        user: User = CONTEXT_USER.get()
        if not user:
            raise UnauthorizedError()
        updated_user: User = await self.user_repository.update(
            user, **values_set.model_dump(exclude_none=True)
        )
        return UserResponseDTO.model_validate(updated_user, from_attributes=True)
