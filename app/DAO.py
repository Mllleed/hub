from app.service import Service
from fastapi import HTTPException
from functools import wraps
from sqlalchemy import select, asc, desc, inspect, or_, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError
from app.db import async_session
from app.api.schemas import CardContent, CardMeta, UserCreate, UserIn
from app.api.notes import Card, Category, Tag, User
from contextlib import asynccontextmanager
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def handle_db_errors(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except SQLAlchemyError as e:
            logger.error(f'Ошибка в БД {func.__name__}: {e}', exc_info=True)
            raise HTTPException(status_code=500, detail='Ошибка базы данных')
        except Exception as e:
            logger.critical(f'Критическая ошибка в {func.__name__}: {e}', exc_info=True)
            raise HTTPException(status_code=500, detail='Внутрення ошибка сервера')
    return wrapper

@asynccontextmanager
async def get_db_transaction():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
        finally: 
            await session.close()

@asynccontextmanager
async def get_db_session():
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()


class CardDAO:
    @classmethod
    @handle_db_errors
    async def get_card_by_id_from_bd(cls, card_id: int, owner_id: int) -> Card:
        """Возвращает карточку id

        Args:
            card_id: id карточки

        Returns:
            Card: Карточка
        Raises:
            HTTPException: При отсутствии карточки
        """

        async with get_db_session() as session:
            stmt = select(Card).options(
                selectinload(Card.category),
                selectinload(Card.tags)).where(and_(Card.id == card_id, Card.owner_id == owner_id))
            logger.debug(stmt)
            result = await session.execute(stmt)
            card = result.scalar_one_or_none()
            if card is None:
                raise HTTPException(status_code=404, detail='Карточка не найдена')
        return card

    @classmethod
    @handle_db_errors
    async def get_cards_from_bd(cls, owner_id: int, order: str = 'desc',
                                sort_by: str = 'created_at',
                                cat: Optional[str] = None,
                                tag: Optional[str] = None,
                                limit: int = 5,
                                offset: int = 0,) -> list[Card]:
        """Получает все записи из БД и сортирует.

        Args:
            order: Оператор сортировки
            sort_by: Параметр сортировки
            cat: Категория
            tag: тэг
        Returns:
            cards: Отсортированный список записей
        Raises:
            HTTPException: При ошибках валидации или БД
        """
        valid_columns = {col.key for col in inspect(Card).mapper.column_attrs}

        if sort_by not in valid_columns:
            raise HTTPException(
                status_code=400,
                detail='Недопустивый параметр сортировки')

        async with get_db_session() as session:
            stmt = select(Card).options(
                selectinload(Card.category),
                selectinload(Card.tags)).where(Card.owner_id == owner_id)
            if cat and tag:
                stmt = (
                    stmt.join(Card.category)
                    .join(Card.tags)
                    .where(and_(Category.cat_name == cat, Tag.tag_name == tag))
                )
            elif cat:
                stmt = stmt.join(Card.category).where(Category.cat_name == cat)
            elif tag:
                stmt = stmt.join(Card.tags).where(Tag.tag_name == tag)

            col = getattr(Card, sort_by)
            stmt = stmt.order_by(desc(col) if order.lower() == 'desc' else asc(col))
            stmt = stmt.limit(limit).offset(offset)

            res = await session.execute(stmt.distinct())
            cards = res.scalars().unique().all()
        return cards
    @classmethod
    @handle_db_errors
    async def create_card_in_bd(cls, title: str, subtitle: str, content: str, owner_id: int,
                                attr: Optional[dict] = None) -> Card:
        """Создает новую карточку в БД.

        Args:
            title: Заголовок карточки
            subtitle: Подзаголовок
            content: Содержание
            attr: Словарь с метаданным
                category: Категория
                tag: тэг
        Returns:
            Card: Созданный объект карточки

        Raises:
            HTTPException: При ошибках валидации или БД
        """
        async with get_db_transaction() as session:
            category = None
            tag_objs = []

            if attr:
                if attr.get('cat'):
                    category = await Service.get_or_create_category(session, attr['cat'])

                if attr.get('tag'):
                    tag_objs = [
                        await Service.get_or_create_tag(session, t)
                        for t in attr['tag']
                    ]

            card = Card(title=title, subtitle=subtitle, content=content,
                        category=category, tags=tag_objs, owner_id=owner_id)

            session.add(card)
            await session.flush()
        logger.info(f'Запись с {card.id} создана')
        return card

    @classmethod
    @handle_db_errors
    async def delete_card_from_bd(cls, card_id: int, owner_id: int) -> Card:
        """Удаляет карточку в БД.

        Args:
            card_id: Первичный ключ записи
        Returns:
            Bool
        Raises:
            HTTPException: При ошибках валидации или БД
        """
        async with get_db_transaction() as session:
            stmt = select(Card).where(Card.id == card_id, Card.owner_id == owner_id)
            card = await session.execute(stmt)
            card = card.scalar_one_or_none()
            if card is None:
                logger.warning(f'Запись с {card_id} не найдена')
                raise HTTPException(status_code=404, detail='Карточка не найдена')
            await session.delete(card)

        logger.info(f'Запись с {card_id} удалена')
        return card

    @classmethod
    @handle_db_errors
    async def update_card_in_bd(cls, card_id: int, owner_id: int, data: Optional[CardContent] = None,
                                meta: Optional[CardMeta] = None) -> bool:
        """Обновляет карточку в БД.

        Args:
            card_id: Первичный ключ записи
            data: Список заголовков записи:
                title: Заголовок карточки
                subtitle: Подзаголовок
                content: Содержание
            meta:
                category: Категория
                tags: Список тэгов
        Returns:
            Bool
        Raises:
            HTTPException: При ошибках валидации или БД
        """
        async with get_db_transaction() as session:
            stmt = (select(Card)
                    .options(selectinload(Card.tags), selectinload(Card.category))
                    .where(Card.id == card_id, Card.owner_id == owner_id))
            card = await session.execute(stmt)
            card = card.scalar_one_or_none()
            if not card:
                return False

            if meta and meta.cat:
                category = await Service.get_or_create_category(session, meta.cat)
                card.category = category

            if meta and meta.tag:
                new_tags = set(meta.tag)
                current_tags = {t.tag_name: t for t in card.tags}

                for tag_name in new_tags - current_tags.keys():
                    tag = await Service.get_or_create_tag(session, tag_name)
                    card.tags.append(tag)

                for tag_name in current_tags.keys() - new_tags:
                    card.tags.remove(current_tags[tag_name])

            if data:
                for key, value in data.model_dump(exclude_unset=True).items():
                    setattr(card, key, value)

        logger.info(f'Запись с id {card_id} обновлена')
        return True

    @classmethod
    @handle_db_errors
    async def search_cards_in_bd(cls, q: str, owner_id: int) -> list[Card]:
        """Поиск карточки по тексту(ilike)

            Args:
                q: Текст
            Raises:
                HTTPExecption: Если карточка не найдена
            Returns:
                list[Card]
        """
        async with get_db_session() as session:
            stmt = select(Card).where(Card.owner_id == owner_id)
            stmt = (
                stmt
                .options(selectinload(Card.category), selectinload(Card.tags))
                .outerjoin(Card.category)
                .outerjoin(Card.tags)
                .where(or_(
                    Card.title.ilike(f"%{q}%"),
                    Card.subtitle.ilike(f"%{q}%"),
                    Card.content.ilike(f"%{q}%"),
                    Category.cat_name.ilike(f"%{q}%"),
                    Tag.tag_name.ilike(f"%{q}%"),
                )
                )
            )
            logger.debug(stmt)
            result = await session.execute(stmt)
        return result.scalars().unique().all()


class UserDAO:
    @classmethod
    @handle_db_errors
    async def register_user_in_db(cls, userdata: UserCreate) -> User:
        """Регистрирует нового пользователя

        Args:
            userdata:
                username: Имя пользователя
                email: Электронная почта
                password: нехэшированный пароль
        Returns:
            User: ORM объект пользователя
        Raises:
            HTTPException в случае неудачи регистрации
        """
        async with get_db_transaction() as session:
            user = User(
                username=userdata.username,
                email=userdata.email,
                hashed_password=await Service.hash_password(userdata.password))
            session.add(user)
            await session.flush()
            await session.refresh(user)
        return user

    @classmethod
    @handle_db_errors
    async def login_user_in_db(cls, userdata: UserIn) -> dict:
        """ Аутентификация/Авторизация пользователя

        Args:
            userdata:
                username: Имя пользователя
                password: нехэшированный пароль
        Returns:
            dict: Данные токена
        Raises:
            HTTPException в случае неудачи аутентификации
        """
        stmt = select(User).where(User.username == userdata.username).limit(1)
        async with get_db_session() as session:
            result = await session.execute(stmt)
            user = result.scalars().first()
        if not user or not await Service.verify_method(userdata.password, user.hashed_password):
            raise HTTPException(status_code=401, detail='Неверный логин или пароль')

        token = await Service.create_access_token(data={'sub': str(user.id)})
        return {'access_token': token, 'token_type': 'bearer'}


