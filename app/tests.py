import pytest_asyncio
import asyncio
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.DAO import CardDAO
from app.base import Base
from app.api.notes import Card, Category
from contextlib import asynccontextmanager

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def async_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def sample_card(async_session):
    category = Category(cat_name="Test Category",)
    card = Card(card_id=1, title="Test Card", owner_id = 1, category=category)
    async_session.add(card)
    await async_session.commit()
    return card


class TestCard:
    @pytest.mark.asyncio
    async def test_get_card_by_id_from_bd(self, async_session, sample_card, monkeypatch):
        @asynccontextmanager
        async def fake_get_db_session():
            async with async_session as s:
                yield s

        monkeypatch.setattr("app.DAO.get_db_session", fake_get_db_session)

        result = await CardDAO.get_card_by_id_from_bd(1)
        assert result.id == 1
        assert result.title == "Test Card"

