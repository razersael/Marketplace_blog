from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from src.marketplace_blog.routers import auth, categories, images, posts
from fastapi.responses import JSONResponse
from jose import jwt, JWTError
from src.marketplace_blog.config import settings
from src.marketplace_blog.core.database import AsyncSessionLocal
from src.marketplace_blog.services.user_service import UserService

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("✅ База данных готова")
    yield


app = FastAPI(title="Marketplace Blog API", lifespan=lifespan)

app.state.testing = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


PUBLIC_PATHS = [
    "/auth",
    "/docs",
    "/redoc",
    "/openapi.json",
]

PUBLIC_PATHS = [
    "/auth",
    "/docs",
    "/redoc",
    "/openapi.json",
]


def is_public_path(path: str) -> bool:
    return any(path.startswith(p) for p in PUBLIC_PATHS)


def get_token_from_cookie(request: Request) -> str | None:
    return request.cookies.get("access_token")


def decode_jwt_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=["HS256"]
        )
        user_email = payload.get("sub")

        if not user_email:
            return None

        return {"email": user_email}

    except JWTError:
        return None


async def get_user_from_db(email: str):
    async with AsyncSessionLocal() as db:
        user_service = UserService(db)
        return await user_service.get_user_by_email(email)


async def authenticate_request(request: Request) -> tuple[bool, JSONResponse | None]:
    if is_public_path(request.url.path):
        return True, None

    token = get_token_from_cookie(request)
    if not token:
        return False, JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Missing access token"}
        )

    payload = decode_jwt_token(token)
    if not payload:
        return False, JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid or expired token"}
        )

    user = await get_user_from_db(payload["email"])
    if not user:
        return False, JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "User not found"}
        )

    request.state.user_id = user.id
    return True, None


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """
    Middleware для проверки JWT токена.
    """
    if getattr(app.state, "testing", False):
        return await call_next(request)

    is_authenticated, error_response = await authenticate_request(request)

    if not is_authenticated:
        return error_response

    return await call_next(request)


app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(posts.router)
app.include_router(images.router)


@app.get("/")
async def root():
    return {"message": "Marketplace Blog API", "status": "running"}
