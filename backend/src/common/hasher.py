from passlib.context import CryptContext


class Hasher:
    def __init__(self):
        self.__schemes = ['sha512_crypt']
        self.context = CryptContext(schemes=self.__schemes)

    def get_hash(self, char_sequence: str) -> str:
        return self.context.hash(char_sequence)

    def validate_plain(self, password: str, hashed_password: str) -> bool:
        return self.context.verify(password, hashed_password)
