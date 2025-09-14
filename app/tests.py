import pytest_asyncio
import asyncio
import os
import pytest
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.DAO import CardDAO
from app.base import Base
from app.api.notes import Card, Category
from contextlib import asynccontextmanager
from app.api.schemas import CardContent, CardMeta
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///:memory:'
os.environ['DB_DRIVER'] = 'sqlite'


@pytest.fixture(scope='session')
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()
    asyncio.set_event_loop(None)


@pytest_asyncio.fixture(scope="function")
async def func_async_session():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={'check_same_thread': False},
        # poolclass=NullPool
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session_maker() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def sample_card(func_async_session):
    category = Category(cat_name="Test Category",)
    func_async_session.add(category)
    card = Card(title="Test Card", owner_id = 1, category_id=category.id)
    func_async_session.add(card)
    await func_async_session.commit()
    return card

@asynccontextmanager
async def fake_get_db_session(session):
    try:
        yield session
    except Exception as e:
        await session.rollback()
        raise e
    finally:
        await session.close()


@asynccontextmanager
async def fake_get_db_transaction(session):
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise e
    finally:
        await session.close()

class TestCard:
    @pytest.mark.asyncio
    async def test_get_card_by_id_from_bd(self, func_async_session, sample_card, monkeypatch):
        monkeypatch.setattr("app.DAO.get_db_session", lambda: fake_get_db_session(func_async_session))

        result = await CardDAO.get_card_by_id_from_bd(card_id=1, owner_id=1)
        assert result.id == 1
        assert result.title == "Test Card"

    @pytest.mark.asyncio
    async def test_get_cards_from_bd(self, func_async_session, sample_card, monkeypatch):
        monkeypatch.setattr('app.DAO.get_db_session', lambda: fake_get_db_session(func_async_session))

        result = await CardDAO.get_cards_from_bd(owner_id=1)
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_create_card_in_bd(self, func_async_session, monkeypatch):
        monkeypatch.setattr('app.DAO.get_db_session', lambda: fake_get_db_session(func_async_session))

        result = await CardDAO.create_card_in_bd(title='string', subtitle='string', content='string', owner_id=1,
                                                 attr={"category": 'string', "tags": ['string', 'string1']})
        assert isinstance(result, Card)

    @pytest.mark.asyncio
    async def test_update_card_in_bd(self, func_async_session, monkeypatch):
        monkeypatch.setattr('app.DAO.get_db_transaction', lambda: fake_get_db_transaction(func_async_session))

        result = await CardDAO.update_card_in_bd(card_id=1, owner_id=1,
                                                 data=CardContent(title='string', subtitle='string', content='string'),
                                                 meta=CardMeta(cat='string', tag=['string', 'string1']))

        assert isinstance(result, bool)
        assert result == True

    @pytest.mark.asyncio
    async def test_delete_card_from_bd(self, func_async_session, monkeypatch):
        monkeypatch.setattr('app.DAO.get_db_transaction', lambda: fake_get_db_transaction(func_async_session))

        result = await CardDAO.delete_card_from_bd(card_id=1, owner_id=1)

        assert isinstance(result, Card)