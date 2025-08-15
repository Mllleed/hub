import enum
import logging
from db_request import create_card_in_bd, delete_card_from_bd, update_card_in_bd, get_card_from_bd
from fastapi import APIRouter, Query, Body, Path
from typing import Optional, Literal, Annotated
from api.schemas import HTTPStatus, CardContent, FilterParams
router = APIRouter()

"""
Роутер для взаимодействия с карточками
"""

logger = logging.getLogger(__name__)

@router.get('/', tags=['todos'])
async def read_users():
    return {'status': 'ok'}

# class FilterParamsCard(BaseModel):
#     title: Optional[str] = Field(
#             max_length = 30,
#             title = 'Название карточки',
#             decription = 'Просто название карточки',
#             example = 'Поездка в магазин',
#             )
#     subtitle: Optional[str] = Field(
#             max_length = 16,
#             title ='Описание карточки',
#             description='Короткое описание карточки',
#             )
#     content: Optional[str] = Field(
#             title = 'Содержимое карточки')
 

@router.get('/get_card/', tags=['todos'])
async def get_card(sort_param: Annotated[FilterParams, Query()] = None):
    try:
        if sort_param:
            logger.info(sort_param)
        res =  await get_card_from_bd()
        return res
    except Exception as e:
        logger.error(e)
        return HTTPStatus.BAD.value

@router.post('/create_card/', tags=['todos'])
async def create_card(data: Annotated[CardContent, Body(embed=True)]):
    """Обработчик. Создает карточку в базе данных"""
    try:
        args = [item[1] for item in data]
        await create_card_in_bd(*args)
        return HTTPStatus.OK.value 
    except Exception as e:
        logger.error(e)
        return HTTPStatus.BAD.value, e

@router.delete('/delete_card/{card_id}', tags=['todos'])
async def delete_card(card_id: Annotated[int, Path()]):
    """Обработчик. Удаляет запись по первичному ключу"""
    try:
        await delete_card_from_bd(card_id)
        return HTTPStatus.OK.value
    except Exception as e:
        logger.error(e)
        return HTTPStatus.BAD.value, e


@router.patch('/update_card/{card_id}')
async def udpate_card(card_id: Annotated[int, Path()],
                      data: Annotated[CardContent, Body(embed=True)]):
    '''Обрабочтик. Частичное обновление записи'''
    try:
        await update_card_in_bd(card_id, data)
        return HTTPStatus.OK.value
    except Exception as e:
        logger.error(ecreate_card_in_bd)
        return HTTPStatus.BAD.value, e
