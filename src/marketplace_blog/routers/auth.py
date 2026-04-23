from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.marketplace_blog.core.database import get_db
from src.marketplace_blog.core.security import create_access_token, verify_password
from src.marketplace_blog.schemas import UserLogin, UserRegister, UserResponse
from src.marketplace_blog.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["Аутентификация"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    """Регистрация нового пользователя"""
    user_service = UserService(db)
    new_user = await user_service.create_user(
        email=user_data.email, username=user_data.username, password=user_data.password
    )
    return new_user


@router.post("/login")
async def login(
    user_data: UserLogin, response: JSONResponse, db: AsyncSession = Depends(get_db)
):
    """Аутентификация — выдаёт токен в cookie"""
    user_service = UserService(db)
    user = await user_service.get_user_by_email(user_data.email)

    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    access_token = create_access_token(data={"sub": user.email})

    response = JSONResponse(content={"message": "Login successful", "user_id": user.id})
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        max_age=900,
        path="/",
    )
    return response


@router.post("/logout")
async def logout():
    """Выход — удаляем cookie"""
    response = JSONResponse(content={"message": "Logout successful"})
    response.delete_cookie("access_token", path="/")
    return response
