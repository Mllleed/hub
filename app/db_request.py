from service import Service
from fastapi import HTTPException
from functools import wraps
from sqlalchemy import select, update, asc, desc, inspect, or_, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError
from db import async_session
from api.schemas import CardContent, CardResponse, CardMeta, UserOut, UserCreate
from api.notes import Card, Category, Tag, User
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
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

@asynccontextmanager
async def get_db_session():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


@handle_db_errors
async def register_user_in_db(userdata: UserCreate) -> User:
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
        session.flush()
        session.refresh(user)
    return user




@handle_db_errors
async def get_card_by_id_from_bd(card_id: int) -> Card:
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
                 selectinload(Card.tags)).where(Card.id == card_id)
        logger.debug(stmt)
        result = await session.execute(stmt)
        card = result.scalars().first()
        if card is None:
            raise HTTPException(status_code=404, detail='Карточка не найдена')
    return card


@handle_db_errors
async def get_cards_from_bd(order: str = 'desc',
                           sort_by: str = 'created_at',
                           cat: Optional[str] = None,
                           tag: Optional[str] = None,
                           limit: int = 5,
                           offset: int = 0) -> list[Card]:
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
    valid_columns =  {col.key for col in inspect(Card).mapper.column_attrs}

    if sort_by not in valid_columns:
        raise HTTPException(
                status_code=400,
                detail='Недопустивый параметр сортировки')

    async with get_db_session() as session:
        stmt = select(Card).options(
                selectinload(Card.category),
                selectinload(Card.tags))
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

@handle_db_errors
async def create_card_in_bd(title: str, subtitle: str, content: str,
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
                    category=category, tags=tag_objs)


        session.add(card)
        session.flush()
    logger.info(f'Запись с {card.id} создана')
    return card

@handle_db_errors
async def delete_card_from_bd(id: int) -> Card:
    """Удаляет карточку в БД.

    Args:
        id: Первичный ключ записи
    Returns:
        Bool
    Raises:
        HTTPException: При ошибках валидации или БД
    """
    async with get_db_transaction() as session:
        card = await session.get(Card, id)
        if card is None:
            logger.warning(f'Запись с {id} не найдена')
            raise HTTPException(status_code=404, detail='Карточка не найдена')

        session.delete(card)
    logger.info(f'Запись с {id} удалена')
    return card

@handle_db_errors
async def update_card_in_bd(card_id: int, data: Optional[CardContent] = None,
                            meta: Optional[CardMeta] = None) -> bool:
    """Обновляет карточку в БД.

    Args:
        id: Первичный ключ записи
        data: Список заголовков записи:
            title: Заголовок карточки
            subtitle: Подзаголовок
            content: Содержание

    Returns:
        Bool
    Raises:
        HTTPException: При ошибках валидации или БД
    """
    async with get_db_transaction() as session:
        card = await session.get(Card, card_id)
        if not card:
            return False

        if meta and meta.cat:
            category = await Service.get_or_create_category(session, meta.cat)
            card.category = category

        if meta and meta.tag:
            new_tags = set(meta.tag)
            curent_tags = {t.tag_name: t for t in card.tags}

            for tag_name in new_tags - current_tags.keys():
                tag = await Service.get_or_create_tag(session, tag_name)
                card.tags.append(tag)
                
            for tag in current_tags.keys() - new_tags:
                card.tags.remove(current_tags[tag_name])

        if data:
            for key, value in data.dict(exclude_unset=True).items():
                setattr(card, key, value)

    logger.info(f'Запись с id {card_id} обновлена')
    return True

@handle_db_errors
async def search_cards_in_bd(q: str) -> list[Card]:
    """Поиск карточки по тексту(ilike)
    
        Args:
            q: Текст
        Raises:
            HTTPExecption: Если карточка не найдена
        Returns:
            list[Card]
    """
    async with get_db_session() as session:
        stmt = (
                select(Card)
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
