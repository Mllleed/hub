from fastapi import HTTPException
from functools import wraps
from sqlalchemy import select, update, asc, desc, inspect
from sqlalchemy.exc import SQLAlchemyError
from db import async_session
from api.schemas import CardContent
from api.notes import Card
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

def handle_db_errors(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except SQLAlchemyError as e:
            logger.error(f'Ошибка в БД {func.__name__}: {e}')
            raise HTTPException(status_code=500, detail='Ошибка базы данных')
        except Exception as e:
            logger.critical(f'Критическая ошибка в {func.__name__}: {e}')
            raise HTTPException(status_code=500, detail='Внутрення ошибка сервера')
    return wrapper

@asynccontextmanager
async def get_db_session():
    async with async_session() as session:
        async with session.begin():
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

@handle_db_errors
async def get_card_from_bd(order: str = 'desc',
                           sort_by: str = 'created_at') -> list[Card]:
    """Получает все записи из БД и сортирует.

    Args:
        order: Оператор сортировки
        sort_by: Параметр сортировки
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
        stmt = select(Card) # Не использую session.begin() так как никаких изменений
            
        if order.lower() == 'desc':
            stmt = stmt.order_by(desc(getattr(Card, sort_by))) # order_by метод CursorResult
        else:                                                   #getattr возвращает атрибут модели
            stmt = stmt.order_by(asc(getattr(Card, sort_by)))

        res = await session.execute(stmt)
        cards = res.scalars().all()
        return cards

@handle_db_errors
async def create_card_in_bd(title: str, subtitle: str, content: str):
    """Создает новую карточку в БД.

    Args:
        title: Заголовок карточки
        subtitle: Подзаголовок
        content: Содержание

    Returns:
        Card: Созданный объект карточки

    Raises:
        HTTPException: При ошибках валидации или БД
    """
    async with get_db_session() as session:
        card = Card(title=title, subtitle=subtitle, content=content)
        session.add(card)
        await session.flush()
    logger.info(f'Запись с {id} создана')
    return card

@handle_db_errors
async def delete_card_from_bd(id: int):
    """Удаляет карточку в БД.

    Args:
        id: Первичный ключ записи
    Returns:
        Bool
    Raises:
        HTTPException: При ошибках валидации или БД
    """
    async with get_db_session() as session:
        card = await session.get(Card, id)
        if card is None:
            logger.warning(f'Запись с {id} не найдена')
            return False
        await session.delete(card)
    logger.info(f'Запись с {id} удалена')
    return True

@handle_db_errors
async def update_card_in_bd(id: int, data: CardContent):
    """Создает новую карточку в БД.

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
    async with async_session() as session:
        async with session.begin():
            stmt = (update(Card)
                .where(Card.id == id)
                .values(data.dict(exclude_unset=True)))
            result = await session.execute(stmt)

            if result.rowcount == 0:
                await session.rollback()
                return False
    #   card = result.scalar_one_or_none()

    #   for field, value in data.dict(exclude_unset=True).items():
    #       if getattr(card, field) != value:
    #           setattr(card, field, value) # setattr(class, value, new_value)
    logger.info(f'Запись с id {id} обновлена')
    return True



