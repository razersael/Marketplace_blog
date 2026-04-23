from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.marketplace_blog.core.database import get_db
from src.marketplace_blog.core.dependencies import get_current_user_id
from src.marketplace_blog.schemas import (
    CategoryCreate,
    CategoryListResponse,
    CategoryResponse,
)
from src.marketplace_blog.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["Категории"])


@router.get("", response_model=CategoryListResponse)
async def get_categories(db: AsyncSession = Depends(get_db)):
    """Получение списка всех категорий (публичный)"""
    category_service = CategoryService(db)
    categories = await category_service.get_all_categories()

    return CategoryListResponse(items=categories, total=len(categories))


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Создание категории (только авторизованные)"""
    category_service = CategoryService(db)
    return await category_service.create_category(
        name=category_data.name, description=category_data.description
    )
