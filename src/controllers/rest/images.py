from http import HTTPStatus
from typing import Optional

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from common.context import CONTEXT_USER
from common.dto.image import ImageUrl
from infrastructure.database import User
from storage.s3_repository import S3Repository
from storage.user import AbstractUserRepository


class ImageRouter:
    def __init__(
            self,
            user_repository: AbstractUserRepository,
            s3_repository: S3Repository,
    ):
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

    async def upload_avatar(self, image: UploadFile = File()) -> ImageUrl:
        user: Optional[User] = CONTEXT_USER.get()
        if not user:
            raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED.value)
        filename, pre_signed_url = await self.s3_repository.upload_file(image)
        await self.user_repository.set_avatar(user, filename)
        return ImageUrl(pre_singed_url=pre_signed_url)

    async def response_image(self, filename: str) -> StreamingResponse:
        """Возвращает поток байтов изображения из S3 хранилища"""
        return StreamingResponse(self.s3_repository.get_file_stream(filename))
