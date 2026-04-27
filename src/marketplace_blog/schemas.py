from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


# =========== User =============
class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    created_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ======== Category ==========


class CategoryCreate(BaseModel):
    name: str
    description: str | None = None


class CategoryResponse(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CategoryListResponse(BaseModel):
    items: list[CategoryResponse]
    total: int


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ========== Posts ==========


class PostCreate(BaseModel):
    """Схема для создания поста"""

    title: str
    content: str
    category_id: int
    image_url: str | None = None


class PostUpdate(BaseModel):
    """Схема для обновления поста (все поля опциональны)"""

    title: str | None = None
    content: str | None = None
    category_id: int | None = None
    image_url: str | None = None


class PostResponse(BaseModel):
    """Схема для ответа с постом"""

    id: int
    title: str
    content: str
    image_url: str | None
    category_id: int
    author_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PostListResponse(BaseModel):
    """Схема для списка постов (с пагинацией)"""

    items: list[PostResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
