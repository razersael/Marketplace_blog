from fastapi import APIRouter, File, UploadFile, status

from src.marketplace_blog.services.image_service import ImageService

router = APIRouter(prefix="/images", tags=["Изображения"])


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_image(file: UploadFile = File(...)):
    """
    Загружает изображение в Minio и возвращает URL.
    """
    image_service = ImageService()
    image_url = await image_service.upload_image(file)

    return {"image_url": image_url}
