import os
from typing import AsyncGenerator

import aioboto3
from fastapi import UploadFile

from infrastructure.config import ObjectStorageSettings

CHUNK_SIZE = 16 * 1024


class S3Repository:
    def __init__(self, settings: ObjectStorageSettings):
        self.service_name = 's3'
        self.endpoint = settings.S3_ENDPOINT_URL
        self.bucket = settings.BUCKET_NAME
        self.session = aioboto3.Session(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.REGION_NAME,
        )

    async def upload_file(self, file: UploadFile) -> str:
        unique_filename = self._get_unique_filename(file.filename)
        async with self.session.client(self.service_name, endpoint_url=self.endpoint) as client:
            await client.upload_fileobj(file, self.bucket, unique_filename)
        return unique_filename

    async def get_file_stream(self, filename: str) -> AsyncGenerator[bytes, None]:
        async with self.session.client(self.service_name, endpoint_url=self.endpoint) as client:
            try:
                response = await client.get_object(Bucket=self.bucket, Key=filename)
            except Exception:
                yield b""
            else:
                while bytes_data := await response['Body'].read(CHUNK_SIZE):
                    yield bytes_data

    async def delete_file(self, filename: str) -> None:
        async with self.session.client(self.service_name, endpoint_url=self.endpoint) as client:
            await client.delete_object(Bucket=self.bucket, Key=filename)

    def _get_unique_filename(self, original_name: str) -> str:
        extension = original_name.split('.')[-1]
        return f'{os.urandom(16).hex()}.{extension}'
