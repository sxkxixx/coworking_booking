import http
import logging
from http import HTTPStatus
from typing import Optional

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from common.context import CONTEXT_USER
from common.utils.image_validators import is_valid_image_signature
from infrastructure.database import User
from storage.s3_repository import S3Repository
from storage.user import AbstractUserRepository

logger = logging.getLogger(__name__)


class ImageRouter:
    def __init__(self, user_repository: AbstractUserRepository, s3_repository: S3Repository):
        self.user_repository = user_repository
        self.s3_repository = s3_repository

    def build_api_router(self) -> APIRouter:
        router = APIRouter(prefix='/api/v1', tags=['IMAGE'])
        router.add_api_route('/image', endpoint=self.upload_avatar, methods=['POST'])
        router.add_api_route(
            '/image/{filename}',
            endpoint=self.response_image,
            methods=['GET'],
            response_class=FileResponse
        )
        return router

    async def upload_avatar(self, image: UploadFile = File()) -> str:
        user: Optional[User] = CONTEXT_USER.get()
        if not user:
            logger.info("Attempt to upload avatar as anonymous")
            raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED.value)
        if not await is_valid_image_signature(image):
            logger.exception("Attempt to upload image with incorrect signature")
            raise HTTPException(
                status_code=http.HTTPStatus.BAD_REQUEST,
                detail="Invalid image signature"
            )
        if user.avatar_filename:
            logger.info("Deleting existing avatar of User(email=%s)", user.email)
            await self.s3_repository.delete_file(user.avatar_filename)
        logger.info("Upload avatar for User(email=%s)", user.email)
        filename = await self.s3_repository.upload_file(image)
        await self.user_repository.set_avatar(user, filename)
        logger.info("User(email=%s) successfully uploaded %s", user.email, filename)
        return filename

    async def response_image(self, filename: str) -> StreamingResponse:
        """Возвращает поток байтов изображения из S3 хранилища"""
        return StreamingResponse(self.s3_repository.get_file_stream(filename))
