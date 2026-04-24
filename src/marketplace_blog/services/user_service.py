import os

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.marketplace_blog.config import settings
from src.marketplace_blog.core.security import hash_password
from src.marketplace_blog.models.user import User
from src.marketplace_blog.tasks.email_tasks import send_welcome_email


class UserService:
    """Сервис для работы с пользователями. Содержит всю бизнес-логику."""

    @staticmethod
    async def _check_email_exists(db: AsyncSession, email: str) -> bool:
        """Проверяет, существует ли пользователь с таким email."""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def _check_username_exists(db: AsyncSession, username: str) -> bool:
        """Проверяет, существует ли пользователь с таким username."""
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def create_user(db: AsyncSession, email: str, username: str, password: str) -> User:
        """
        Создаёт нового пользователя.
        Вся логика проверок и создания здесь.
        """
        if await UserService._check_email_exists(db,email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        if await UserService._check_username_exists(db,username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken"
            )

        hashed_password = hash_password(password)

        new_user = User(email=email, username=username, hashed_password=hashed_password)

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        if not settings.testing:
            send_welcome_email.delay(email, username)

        return new_user

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
        """Находит пользователя по email."""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
