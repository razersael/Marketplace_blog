import os

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.marketplace_blog.core.security import hash_password
from src.marketplace_blog.models.user import User
from src.marketplace_blog.tasks.email_tasks import send_welcome_email


class UserService:
    """Сервис для работы с пользователями. Содержит всю бизнес-логику."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _check_email_exists(self, email: str) -> bool:
        """Проверяет, существует ли пользователь с таким email."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none() is not None

    async def _check_username_exists(self, username: str) -> bool:
        """Проверяет, существует ли пользователь с таким username."""
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none() is not None

    async def create_user(self, email: str, username: str, password: str) -> User:
        """
        Создаёт нового пользователя.
        Вся логика проверок и создания здесь.
        """
        if await self._check_email_exists(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        if await self._check_username_exists(username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken"
            )

        hashed_password = hash_password(password)

        new_user = User(email=email, username=username, hashed_password=hashed_password)

        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)

        if os.environ.get("TESTING") != "true":
            send_welcome_email.delay(email, username)

        return new_user

    async def get_user_by_email(self, email: str) -> User | None:
        """Находит пользователя по email."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
