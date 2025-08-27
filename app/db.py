from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from models.base import Base

DATABASE_URL = 'postgresql+asyncpg://postgres:0m9i0l5l0e1rR!@localhost:5432/hub'

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_ = AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
