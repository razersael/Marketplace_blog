from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.marketplace_blog.config import get_async_db_url

engine = create_async_engine(
    get_async_db_url(),
    echo=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

