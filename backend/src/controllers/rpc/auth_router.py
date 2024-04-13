from datetime import datetime
from typing import Optional

import fastapi_jsonrpc as jsonrpc
from fastapi import Response
from peewee import IntegrityError

from common.dto.user import UserCreateDTO, UserResponseDTO, Login, SessionResponse
from common.hasher import Hasher
from common.session import TokenService, Session
from infrastructure.database import User
from storage.session.session_repository import SessionRepository
from storage.user.abstract_user_repository import AbstractUserRepository
from .abstract_rpc_router import AbstractRPCRouter
from .exceptions import RegisterError, AuthenticationError


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

    async def login(self, data: Login, response: Response) -> SessionResponse:
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
            expires=datetime.utcnow() + self.session_repository.session_ttl
        )
        return SessionResponse(access_token=access_token)
