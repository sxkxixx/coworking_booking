import logging

import fastapi_jsonrpc as jsonrpc

from common.context import CONTEXT_USER
from common.decorators import login_required
from common.dto.user import (
    UpdateUserRequest,
    UserResponseDTO
)
from common.session import TokenService
from infrastructure.database import User
from storage.user import AbstractUserRepository
from .abstract_rpc_router import AbstractRPCRouter

logger = logging.getLogger(__name__)


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

    @login_required
    async def get_profile(self) -> UserResponseDTO:
        user: User = CONTEXT_USER.get()
        return UserResponseDTO.model_validate(user, from_attributes=True)

    @login_required
    async def update_user_data(self, values_set: UpdateUserRequest) -> UserResponseDTO:
        user: User = CONTEXT_USER.get()
        logger.info("Updating User(email=%s) params with values to set %s", user.email, values_set)
        updated_user: User = await self.user_repository.update(
            user, **values_set.model_dump(exclude_none=True)
        )
        logger.info("User(email=%s) data was updated", user.email)
        return UserResponseDTO.model_validate(updated_user, from_attributes=True)
