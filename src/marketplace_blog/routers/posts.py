from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.marketplace_blog.core.database import get_db
from src.marketplace_blog.core.dependencies import get_current_user_id
from src.marketplace_blog.schemas import (
    PostCreate,
    PostListResponse,
    PostResponse,
    PostUpdate,
)
from src.marketplace_blog.services.post_service import PostService

router = APIRouter(prefix="/posts", tags=["Посты"])


@router.get("", response_model=PostListResponse)
async def get_posts_list(
    search: str | None = Query(None, description="Поиск по заголовку и содержанию"),
    category_id: int | None = Query(None, description="Фильтр по категории"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(10, ge=1, description="Элементов на странице (макс 50)"),
    db: AsyncSession = Depends(get_db),
):
    """Получение списка постов (публичный, с пагинацией)"""
    post_service = PostService(db)
    posts, total = await post_service.get_posts_list(
        search=search, category_id=category_id, page=page, page_size=page_size
    )

    max_page_size = 50
    actual_page_size = page_size if page_size <= max_page_size else max_page_size

    total_pages = (total + page_size - 1) // page_size

    return PostListResponse(
        items=posts,
        total=total,
        page=page,
        page_size=actual_page_size,
        total_pages=total_pages,
    )


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, db: AsyncSession = Depends(get_db)):
    """Получение одного поста (публичный)"""
    post_service = PostService(db)
    return await post_service.get_post_by_id(post_id)


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_data: PostCreate,
    db: AsyncSession = Depends(get_db),
    author_id: int = Depends(get_current_user_id),
):
    """Создание нового поста (только авторизованные)"""
    post_service = PostService(db)
    return await post_service.create_post(
        title=post_data.title,
        content=post_data.content,
        category_id=post_data.category_id,
        author_id=author_id,
        image_url=post_data.image_url,
    )


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: int,
    post_data: PostUpdate,
    db: AsyncSession = Depends(get_db),
    author_id: int = Depends(get_current_user_id),
):
    """Обновление поста (только автор)"""
    post_service = PostService(db)
    return await post_service.update_post(
        post_id=post_id,
        author_id=author_id,
        title=post_data.title,
        content=post_data.content,
        category_id=post_data.category_id,
        image_url=post_data.image_url,
    )


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    author_id: int = Depends(get_current_user_id),
):
    """Фейковое удаление поста (только автор)"""
    post_service = PostService(db)
    await post_service.delete_post(post_id=post_id, author_id=author_id)
    return None
