from datetime import timedelta, datetime
from typing import Any, Optional

from jose import jwt

from infrastructure.database import User


class TokenService:
    ALGORITHM = 'HS256'

    def __init__(self, secret_key: str, access_token_ttl: timedelta):
        self.secret_key = secret_key
        self.access_token_ttl = access_token_ttl

    def get_access_token(self, user: User) -> str:
        data = {'id': user.id, 'email': user.email, 'is_student': user.is_student}
        return self.__get_encode_token(self.access_token_ttl, **data)

    def __get_encode_token(self, ttl: timedelta, **kwargs) -> str:
        data = kwargs.copy()
        expire = datetime.utcnow() + ttl
        data.update({"exp": expire})
        return jwt.encode(data, self.secret_key, self.ALGORITHM)

    def get_token_payload(self, token: str) -> Optional[dict[str, Any]]:
        try:
            return jwt.decode(token, self.secret_key, [self.ALGORITHM])
        except jwt.JWTError:
            return None
