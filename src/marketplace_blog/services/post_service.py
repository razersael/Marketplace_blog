from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.marketplace_blog.models.category import Category
from src.marketplace_blog.models.Post import DeletedPost, Post


class PostService:
    """Сервис для работы с постами"""

    @staticmethod
    async def create_post(
        db: AsyncSession,
        title: str,
        content: str,
        category_id: int,
        author_id: int,
        image_url: str | None = None,
    ) -> Post:
        """Создаёт новый пост"""
        category = await db.get(Category, category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with id {category_id} not found",
            )

        post = Post(
            title=title,
            content=content,
            category_id=category_id,
            author_id=author_id,
            image_url=image_url,
        )

        db.add(post)
        await db.commit()
        await db.refresh(post)

        return post

    @staticmethod
    async def get_post_by_id(db:AsyncSession, post_id: int) -> Post:
        """Получает активный пост по ID"""
        post = await db.get(Post, post_id)

        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
            )

        return post

    @staticmethod
    async def update_post(
        db: AsyncSession,
        post_id: int,
        author_id: int,
        title: str | None = None,
        content: str | None = None,
        category_id: int | None = None,
        image_url: str | None = None,
    ) -> Post:
        """Обновляет пост"""
        post = await PostService.get_post_by_id(db, post_id)

        if post.author_id != author_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only edit your own posts",
            )

        if category_id is not None:
            category = await db.get(Category, category_id)
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Category with id {category_id} not found",
                )
            post.category_id = category_id

        if title is not None:
            post.title = title
        if content is not None:
            post.content = content
        if image_url is not None:
            post.image_url = image_url

        await db.commit()
        await db.refresh(post)

        return post

    @staticmethod
    async def delete_post(db: AsyncSession, post_id: int, author_id: int) -> None:
        """Фейковое удаление поста — перенос в deleted_posts"""
        post = await PostService.get_post_by_id(db, post_id)

        if post.author_id != author_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own posts",
            )

        deleted_post = DeletedPost(
            original_id=post.id,
            title=post.title,
            content=post.content,
            image_url=post.image_url,
            category_id=post.category_id,
            author_id=post.author_id,
            created_at=post.created_at,
            deleted_at=datetime.utcnow(),
        )

        db.add(deleted_post)
        await db.delete(post)
        await db.commit()

    @staticmethod
    async def get_posts_list(
        db: AsyncSession,
        search: str | None = None,
        category_id: int | None = None,
        page: int = 1,
        page_size: int = 10,
    ):
        """Получает список активных постов с пагинацией и фильтрами"""
        max_page_size = 50
        if page_size > max_page_size:
            page_size = max_page_size

        query = select(Post)

        if category_id:
            query = query.where(Post.category_id == category_id)

        if search:
            search_query = func.plainto_tsquery("russian", search)
            query = query.where(Post.search_vector.op("@@")(search_query))
            query = query.order_by(
                func.ts_rank(Post.search_vector, search_query).desc()
            )
        else:
            query = query.order_by(Post.created_at.desc())

        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query)

        offset = (page - 1) * page_size
        query = query.order_by(Post.created_at.desc()).offset(offset).limit(page_size)

        result = await db.execute(query)
        posts = result.scalars().all()

        return posts, total or 0
