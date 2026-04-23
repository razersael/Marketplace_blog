import uuid

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from fastapi import HTTPException, UploadFile, status

from src.marketplace_blog.config import settings


class ImageService:
    """Сервис для загрузки изображений в Minio"""

    def __init__(self):
        self.endpoint = settings.minio_endpoint
        self.access_key = settings.minio_access_key
        self.secret_key = settings.minio_secret_key
        self.bucket = settings.minio_bucket
        self.secure = settings.minio_secure
        self.client = boto3.client(
            "s3",
            endpoint_url=f"{'https' if self.secure else 'http'}://{self.endpoint}",
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=Config(signature_version="s3v4"),
        )

    async def upload_image(self, file: UploadFile) -> str:
        """
        Загружает изображение в Minio и возвращает публичный URL.
        """
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only image files are allowed (jpeg, png, gif, webp)",
            )

        # 2. Проверяем размер (максимум 5MB)
        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(0)

        if size > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File too large. Maximum size is 5MB",
            )

        file_extension = file.filename.split(".")[-1] if file.filename else "jpg"
        unique_filename = f"{uuid.uuid4()}.{file_extension}"

        try:
            contents = await file.read()  # Читаем содержимое

            self.client.put_object(
                Bucket=self.bucket,
                Key=unique_filename,
                Body=contents,
                ContentType=file.content_type,
            )
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload image: {e!s}",
            ) from e

        protocol = "https" if self.secure else "http"
        return f"{protocol}://{self.endpoint}/{self.bucket}/{unique_filename}"
