from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from jose import JWTError, jwt

from src.marketplace_blog.config import settings
from src.marketplace_blog.core.database import AsyncSessionLocal
from src.marketplace_blog.routers import auth, categories, images, posts
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


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """
    Middleware для проверки JWT токена.
    """
    if getattr(app.state, "testing", False):
        return await call_next(request)

    path = request.url.path

    if any(path.startswith(p) for p in PUBLIC_PATHS):
        return await call_next(request)

    token = request.cookies.get("access_token")

    if not token:
        return JSONResponse(status_code=401, content={"detail": "Missing access token"})

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        user_email = payload.get("sub")

        if not user_email:
            raise JWTError("No email in token")

    except JWTError:
        return JSONResponse(
            status_code=401, content={"detail": "Invalid or expired token"}
        )

    async with AsyncSessionLocal() as db:
        user_service = UserService(db)
        user = await user_service.get_user_by_email(user_email)

        if not user:
            return JSONResponse(status_code=401, content={"detail": "User not found"})

        request.state.user_id = user.id

    return await call_next(request)


app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(posts.router)
app.include_router(images.router)


@app.get("/")
async def root():
    return {"message": "Marketplace Blog API", "status": "running"}
