from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.base import Base
from app.service import settings

def get_db_url(async_mode: bool = True):
    driver = 'postgresql+asyncpg' if async_mode else 'posrgresql'
    return (
            f"{driver}://{settings.DB_USER}:{settings.DB_PASSWORD}@"
            f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
            )

engine = create_async_engine(get_db_url(), echo=True)
async_session = sessionmaker(engine, class_ = AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
