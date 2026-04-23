from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.marketplace_blog.models.category import Category


class CategoryService:
    """Сервис для работы с категориями"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_category(
        self, name: str, description: str | None = None
    ) -> Category:
        """Создаёт новую категорию"""
        existing = await self.db.execute(select(Category).where(Category.name == name))
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with name '{name}' already exists",
            )

        category = Category(name=name, description=description)

        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)

        return category

    async def get_all_categories(self) -> list[Category]:
        """Возвращает все категории"""
        result = await self.db.execute(select(Category).order_by(Category.name))
        return result.scalars().all()

    async def get_category_by_id(self, category_id: int) -> Category | None:
        """Находит категорию по ID"""
        result = await self.db.execute(
            select(Category).where(Category.id == category_id)
        )
        return result.scalar_one_or_none()
