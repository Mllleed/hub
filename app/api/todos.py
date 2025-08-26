from functools import wraps
import traceback
import enum
import logging
from db_request import create_card_in_bd, delete_card_from_bd, update_card_in_bd, get_cards_from_bd, search_cards_in_bd, get_card_by_id_from_bd
from fastapi import APIRouter, Query, Body, Path, HTTPException
from typing import Optional, Literal, Annotated, List
from api.schemas import HTTPStatus, CardContent, FilterParams, CardMeta, CardResponse
router = APIRouter()

"""
Роутер для взаимодействия с карточками
"""

logger = logging.getLogger(__name__)

def handle_resp_errors(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            raise
        except Exception as e:
            tb = traceback.format_exc() 
            logger.error(f'Ошибка обработчика {func.__name__}: {e}\n{tb}')
            raise HTTPException(status_code=500,
                                detail=f"Internal Server Error in {func.__name__}")
    return wrapper


@router.get('/', tags=['todos'])
async def read_users():
    return {'status': 'ok'}

@router.get('/get_card/{card_id}/',
           tags=['todos'],
           response_model=CardResponse)
@handle_resp_errors
async def get_card_by_id(card_id: Annotated[Optional[int], Path()]):
    """Обработчик. Возвращает карточку по  id"""
    card = await get_card_by_id_from_bd(card_id)
    return card

@router.get('/get_card/',
            tags=['todos'],
            response_model=List[CardResponse])
@handle_resp_errors
async def get_card(sort_param: Annotated[FilterParams, Query()] = None):
    '''Обработчик. Получает сортированный список карточек'''
    if sort_param:
        logger.info(sort_param)
    data = sort_param.dict()
    res =  await get_cards_from_bd(**data)
    return res


@router.post('/create_card/',
             tags=['todos'],
             response_model=CardResponse)
@handle_resp_errors
async def create_card(data: Annotated[CardContent, Body(embed=True)],
                      meta: Annotated[CardMeta, Query()]):
    """Обработчик. Создает карточку в базе данных"""
    #args = [item[1] for item in data]
    kwargs = meta.dict()
    card = await create_card_in_bd(data.title, data.subtitle, data.content,
                                   meta.dict())
    return card 


@router.delete('/delete_card/{card_id}', tags=['todos'])
@handle_resp_errors
async def delete_card(card_id: Annotated[int, Path()]):
    """Обработчик. Удаляет запись по первичному ключу"""
    await delete_card_from_bd(card_id)
    return HTTPStatus.OK.value


@router.patch('/update_card/{card_id}')
@handle_resp_errors
async def udpate_card(card_id: Annotated[int, Path()],
                      data: Annotated[CardContent, Body(embed=True)] = None,
                      meta: Optional[CardMeta] = None):
    '''Обрабочтик. Частичное обновление записи'''
    await update_card_in_bd(card_id, data, meta)
    return HTTPStatus.OK.value

@router.get('/search_card/', tags=['todos'])
@handle_resp_errors
async def search_card(q: Annotated[str, Query(max_length=16)]):
    '''Обработчик. Поиск карточки по тексту'''
    return await search_cards_in_bd(q)
