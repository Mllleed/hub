from fastapi import HTTPException
from sqlalchemy import select, update, asc, desc
from sqlalchemy.exc import SQLAlchemyError
from db import async_session
from api.schemas import CardContent
from api.notes import Card
import logging

logger = logging.getLogger(__name__)

async def get_card_from_bd(order: str = 'desc',
                           sort_by: str = 'created_at'):
    '''Сессия, возвращает сортированный список записей'''
    try:
        async with async_session() as session:
            stmt = select(Card)
            
            if order.lower() == 'desc':
                stmt = stmt.order_by(desc(getattr(Card, sort_by)))
            else:
                stmt = stmt.order_by(asc(getattr(Card, sort_by)))

            res = await session.execute(stmt)
            cards = res.scalars().all()
            return cards
    except SQLAlchemyError as e:
        logger.error(f'Ошибка при получении записей: {e}')
        raise
    except Exception as e:
        logger.critical(f'Критическая ошибка при получении записей: {e}')
        raise

async def create_card_in_bd(title: str, subtitle: str, content: str):
    """Сессия. Транзакция, проводит создание записи в БД"""
    try:
        async with async_session() as session:
            async with session.begin():
                card = Card(title=title, subtitle=subtitle, content=content)
                session.add(card)
        logger.info(f'Запись с {id} создана')
    except SQLAlchemyError as e:
        logger.error(f'Ошибка при создании записи: {e}')
        raise
    except Exception as e:
        logger.error(f'Критическая ошибка при создании: {e}')
        raise

async def delete_card_from_bd(id: int):
    """Сессия. Транзакция, проводит удаление записи по первичному ключу"""
    try:
        async with async_session() as session:
            async with session.begin():
                card = await session.get(Card, id)
                if card is None:
                    logger.warning(f'Запись с {id} не найдена')
                    return False
                await session.delete(card)
        logger.info(f'Запись с {id} удалена')
        return True
    except SQLAlchemyError as e:
        logger.error(f'Ошибка при удалении записи: {e}')
        raise
    except Exception as e:
        logger.critical(f'Критическая ошибка при удалении: {e}')
        raise
        
async def update_card_in_bd(id: int, data: CardContent):
    """Сессия. Транзакция, проводит частичное обновленеи записи"""
    try:
        async with async_session() as session:
            async with session.begin():
                stmt = select(Card).where(Card.id == id)
                result = await session.execute(stmt)
                card = result.scalar_one_or_none()

        
                for field, value in data.dict(exclude_unset=True).items():
                    if getattr(card, field) != value:
                        setattr(card, field, value)
        logger.info(f'Запись с id {id} обновлена')
        return True
    except SQLAlchemyError as e:
        logger.error(f'Ошибка при обновлении записи: {e}')
        raise
    except Exception as e:
        logger.critical(f'Критическая ошибка при обновлении: {e}')
        raise



