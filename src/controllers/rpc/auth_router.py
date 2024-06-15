import logging
from typing import Optional

import fastapi_jsonrpc as jsonrpc
from fastapi import Response, Request
from peewee import IntegrityError

from common.context import CONTEXT_USER
from common.decorators import login_required
from common.dto.user import (
    UserCreateDTO,
    UserResponseDTO,
    Login,
    TokenResponse,
    ChangePasswordRequest
)
from common.exceptions.rpc import (
    RegisterError,
    AuthenticationError,
    SessionError,
    UnauthorizedError
)
from common.hasher import Hasher
from common.session import TokenService, Session
from common.utils import utc_with_zone
from infrastructure.database import User
from storage.session.session_repository import SessionRepository
from storage.user.abstract_user_repository import AbstractUserRepository
from .abstract_rpc_router import AbstractRPCRouter

logger = logging.getLogger(__name__)


class AuthRouter(AbstractRPCRouter):
    """Auth user router"""

    def __init__(
            self,
            user_repository: AbstractUserRepository,
            hasher: Hasher,
            token_service: TokenService,
            session_repository: SessionRepository,
    ):
        self.user_repository = user_repository
        self.hasher = hasher
        self.token_service = token_service
        self.session_repository = session_repository

    def build_entrypoint(self) -> jsonrpc.Entrypoint:
        entrypoint = jsonrpc.Entrypoint(path='/api/v1/auth', tags=['AUTH'])
        entrypoint.add_method_route(self.register, errors=[RegisterError])
        entrypoint.add_method_route(self.login, errors=[AuthenticationError])
        entrypoint.add_method_route(self.refresh_session, errors=[SessionError])
        entrypoint.add_method_route(self.logout, errors=[SessionError])
        entrypoint.add_method_route(self.change_password, errors=[UnauthorizedError, SessionError])
        return entrypoint

    async def register(self, data: UserCreateDTO) -> UserResponseDTO:
        """
        Register User
        :param data: UserCreateDTO
        :return: UserResponseDTO
        """
        try:
            logger.info("Registering user with email = %s", data.email)
            user: User = await self.user_repository.create(data)
        except IntegrityError:
            logger.error("User with email = %s already exists", data.email)
            raise RegisterError(data='User with current email already exists')
        logger.info("Success registering User(id=%s, email=%s)", user.id, user.email)
        return UserResponseDTO.model_validate(user, from_attributes=True)

    async def login(self, data: Login, response: Response) -> TokenResponse:
        """
        Authentication user
        :param data: Login
        :param response: Response
        :return: TokenResponse
        """
        logger.info("Authentication user with email = %s", data.email)
        user: Optional[User] = await self.user_repository.get(User.email == data.email)
        if not user:
            logger.error("User with email = %s not found", data.email)
            raise AuthenticationError()
        if not self.hasher.validate_plain(data.password, user.hashed_password):
            logger.error("User(email=%s) has bad credentials", user.email)
            raise AuthenticationError()
        access_token: str = self.token_service.get_access_token(user)
        session = Session(user_id=user.id, email=user.email, fingerprint=data.fingerprint)
        session_id = await self.session_repository.setex(session)
        logger.info("Session created for User(email=%s)", user.email)
        response.set_cookie(
            key='refresh_token',
            value=session_id,
            httponly=True,
            path='/api/v1/auth',
            expires=utc_with_zone() + self.session_repository.session_ttl
        )
        return TokenResponse(access_token=access_token)

    async def refresh_session(
            self,
            fingerprint: str,
            request: Request,
            response: Response
    ) -> TokenResponse:
        """
        Refresh Session
        :param fingerprint: Browser fingerprint
        :param request: Request
        :param response: Response
        :return: TokenResponse
        """
        session_id: Optional[str] = request.cookies.get('refresh_token')
        if not session_id:
            logger.error("No refresh_token at cookies")
            raise SessionError()
        session: Optional[Session] = await self.session_repository.get(session_id)
        response.delete_cookie('refresh_token')
        if not session:
            logger.error("Session has expired or was not created for token %s", session_id)
            raise SessionError()
        await self.session_repository.delete(session_id)
        if fingerprint != session.fingerprint:
            logger.error(
                "Incorrect fingerprint for Session(id=%s, email=%s)",
                session_id, session.email
            )
            raise SessionError()
        user: Optional[User] = await self.user_repository.get(User.email == session.email)
        if not user:
            logger.critical("User with email = %s not found", session.email)
            raise SessionError()
        new_access_token: str = self.token_service.get_access_token(user)
        new_session = Session(user_id=user.id, email=user.email, fingerprint=fingerprint)
        session_id: str = await self.session_repository.setex(new_session)
        logger.info("New session created for user = %s", user.email)
        response.set_cookie(
            key='refresh_token',
            value=session_id,
            httponly=True,
            path='/api/v1/auth',
            expires=utc_with_zone() + self.session_repository.session_ttl
        )
        return TokenResponse(access_token=new_access_token)

    async def logout(self, fingerprint: str, request: Request, response: Response) -> None:
        """
        Delete user session
        :param fingerprint: Fingerprint
        :param request: Request
        :param response: Response
        :return: None
        """
        session_id: Optional[str] = request.cookies.get('refresh_token')
        if not session_id:
            logger.error("No refresh_token at cookies")
            raise SessionError()
        response.delete_cookie('refresh_token')
        session: Optional[Session] = await self.session_repository.get(session_id)
        if not session:
            logger.error("Session has expired or was not created for token %s", session_id)
            raise SessionError()
        if session.fingerprint != fingerprint:
            logger.exception(
                "Incorrect fingerprint for Session(id=%s, email=%s)",
                session_id, session.email
            )
            raise SessionError()
        await self.session_repository.delete(session_id)
        logger.info("User(email=%s) logged out, session deleted", session.email)
        return None

    @login_required
    async def change_password(
            self,
            data: ChangePasswordRequest,
            request: Request,
            response: Response
    ) -> None:
        user: User = CONTEXT_USER.get()
        if not (session_id := request.cookies.get('refresh_token', None)):
            logger.error("No refresh_token at cookies for user = %s", user.email)
            raise SessionError()
        response.delete_cookie('refresh_token')
        if not (session := await self.session_repository.get(session_id)):
            logger.error("User's(email=%s) session not found", user.email)
            raise SessionError()
        if not (session.fingerprint == data.fingerprint and session.email == user.email):
            logger.error("User(email=%s) has incorrect session params", user.email)
            raise SessionError()
        await self.session_repository.delete(session_id)
        await self.user_repository.update_password(user, data.password)
        logger.info("User(email=%s)'s password was updated", user.email)
        return None
