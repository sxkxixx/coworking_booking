from typing import Optional

import fastapi_jsonrpc as jsonrpc
from fastapi import Response, Request
from peewee import IntegrityError

from common.dto.user import UserCreateDTO, UserResponseDTO, Login, TokenResponse
from common.hasher import Hasher
from common.session import TokenService, Session
from common.utils import utc_with_zone
from infrastructure.database import User
from storage.session.session_repository import SessionRepository
from storage.user.abstract_user_repository import AbstractUserRepository
from .abstract_rpc_router import AbstractRPCRouter
from common.exceptions.rpc import RegisterError, AuthenticationError, SessionError


def parse_email_to_user_id(email: str) -> str:
    """
    Splits email to user id:

    parse_email_to_user_id(name.surname@gmail.com) = "name.surname"
    """
    return email[:email.rfind('@')]


class AuthRouter(AbstractRPCRouter):
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
        entrypoint.add_method_route(self.register)
        entrypoint.add_method_route(self.login)
        entrypoint.add_method_route(self.refresh_session)
        return entrypoint

    async def register(self, data: UserCreateDTO) -> UserResponseDTO:
        try:
            user: User = await self.user_repository.create(
                id=parse_email_to_user_id(data.email),
                email=data.email,
                hashed_password=self.hasher.get_hash(data.password),
                last_name=data.last_name,
                first_name=data.first_name,
                patronymic=data.patronymic,
                is_student=data.is_student
            )
        except IntegrityError:
            raise RegisterError(data='User with current email already exists')
        return user

    async def login(self, data: Login, response: Response) -> TokenResponse:
        user: Optional[User] = await self.user_repository.get(User.email == data.email)
        if not user:
            raise AuthenticationError()
        if not self.hasher.validate_plain(data.password, user.hashed_password):
            raise AuthenticationError()
        access_token: str = self.token_service.get_access_token(user)
        session = Session(user_id=user.id, email=user.email, fingerprint=data.fingerprint)
        session_id = await self.session_repository.setex(session)
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
        session_id: Optional[str] = request.cookies.get('refresh_token')
        if session_id:
            raise SessionError()
        session: Optional[Session] = await self.session_repository.get(session_id)
        response.delete_cookie('refresh_token')
        if not session:
            raise SessionError()
        await self.session_repository.delete(session_id)
        if fingerprint != session.fingerprint:
            raise SessionError()
        user: Optional[User] = await self.user_repository.get(User.email == session.email)
        if not user:
            raise SessionError()
        assert session.fingerprint == fingerprint
        new_access_token: str = self.token_service.get_access_token(user)
        new_session = Session(user_id=user.id, email=user.email, fingerprint=fingerprint)
        session_id: str = await self.session_repository.setex(new_session)
        response.set_cookie(
            key='refresh_token',
            value=session_id,
            httponly=True,
            path='/api/v1/auth',
            expires=utc_with_zone() + self.session_repository.session_ttl
        )
        return TokenResponse(access_token=new_access_token)

    async def logout(self, fingerprint: str, request: Request, response: Response) -> None:
        session_id: Optional[str] = request.cookies.get('refresh_token')
        if not session_id:
            raise SessionError()
        response.delete_cookie('refresh_token')
        session: Optional[Session] = await self.session_repository.get(session_id)
        if not session:
            raise SessionError()
        if session.fingerprint != fingerprint:
            raise SessionError()
        await self.session_repository.delete(session_id)
        return None