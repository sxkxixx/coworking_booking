from typing import Optional

import fastapi_jsonrpc as jsonrpc

from common.dto.user import ResetPasswordRequest
from common.exceptions.rpc import UserNotExistsException, ResetPasswordException
from common.hasher import Hasher
from common.service.reset_password_send_service import PasswordResetSendService
from infrastructure.database import User, PasswordResetToken
from storage.password_reset_token import AbstractPasswordResetTokenRepository
from storage.user import AbstractUserRepository
from .abstract_rpc_router import AbstractRPCRouter


class UserSettingsRouter(AbstractRPCRouter):
    def __init__(
            self,
            user_repository: AbstractUserRepository,
            password_reset_token_repository: AbstractPasswordResetTokenRepository,
            send_service: PasswordResetSendService,
            hasher: Hasher,
    ):
        self.user_repository = user_repository
        self.password_reset_token_repository = password_reset_token_repository
        self.send_service = send_service
        self.hasher = hasher

    def build_entrypoint(self) -> jsonrpc.Entrypoint:
        ep = jsonrpc.Entrypoint(path="/api/v1/user/settings", tags=['USER SETTINGS'])
        ep.add_method_route(self.request_reset_password_link, errors=[UserNotExistsException])
        ep.add_method_route(self.reset_password, errors=[ResetPasswordException])
        return ep

    async def request_reset_password_link(self, email: str, fingerprint: str) -> None:
        """
        Запрос на смену пароля, после выполнения метода приходит письмо на почту с ссылкой,
        содержащую информацию о пользователе
        """
        user: Optional[User] = await self.user_repository.get(User.email == email)
        if not user:
            raise UserNotExistsException()
        reset_token: PasswordResetToken = await self.password_reset_token_repository.create(
            user, fingerprint
        )
        await self.send_service.send(reset_token, user)

    async def reset_password(self, data: ResetPasswordRequest) -> None:
        password_reset: Optional[PasswordResetToken] = (
            await self.password_reset_token_repository.get(data.token, data.email)
        )
        if not password_reset or password_reset.fingerprint != data.fingerprint:
            raise ResetPasswordException()
        user: User = password_reset.user
        await self.user_repository.update_password(user, data.password)
        await self.password_reset_token_repository.mark_token_as_used(password_reset)
