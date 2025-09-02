import aiofiles
from functools import wraps
import traceback
import enum
import logging
from app.db_request import create_card_in_bd, delete_card_from_bd, update_card_in_bd, get_cards_from_bd, search_cards_in_bd, get_card_by_id_from_bd, register_user_in_db, login_user_in_db
from fastapi import APIRouter, Query, Body, Path, HTTPException, Request
from typing import Optional, Literal, Annotated, List, Any
from app.api.schemas import CardContent, FilterParams, CardMeta, CardResponse, UserCreate, UserOut, UserIn, CookieMeta
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from app.site_data import menu_items
from app.api.template import templates
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


@router.get('/', tags=['todos'],
            response_class=HTMLResponse)
async def index_html(request: Request):
    return templates.TemplateResponse('.html', {
        'request': request,})

@router.post('/register/',
             tags=['registration'],
             response_model=UserOut,
             status_code=201)
@handle_resp_errors
async def register_user(userdata: UserCreate) -> Any: 
    """Обработчик. Регистрация пользователя"""
    result = await register_user_in_db(userdata)
    return UserOut.model_validate(result)
    
@router.post('/login/',
             tags=['login'],
             response_model=CookieMeta)
@handle_resp_errors
async def login_user(userdata: UserIn) -> Any:
    """Обработчик. Авторизация пользователя"""
    result = await login_user_in_db(userdata)
    response = JSONResponse(content=result)
    response.set_cookie(
            key='access_token',
            value=result['access_token'],
            httponly=True,
            secure=True,
            samesite='strict',
            max_age=60 * 15,
            )
    return response

@router.get('/get_card/{card_id}/',
           tags=['Card'],
           response_model=CardResponse)
@handle_resp_errors
async def get_card_by_id(card_id: Annotated[Optional[int], Path()]):
    """Обработчик. Возвращает карточку по id"""
    card = await get_card_by_id_from_bd(card_id)
    return card


@router.get('/get_card/',
            tags=['Card'],
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
             tags=['Card'],
             response_model=CardResponse,
             status_code=201)
@handle_resp_errors
async def create_card(data: Annotated[CardContent, Body(embed=True)],
                      meta: Annotated[CardMeta, Query()]):
    """Обработчик. Создает карточку в базе данных"""
    #args = [item[1] for item in data]
    kwargs = meta.dict()
    card = await create_card_in_bd(data.title, data.subtitle, data.content,
                                   meta.dict())
    return card 


@router.delete('/delete_card/{card_id}', tags=['Card'])
@handle_resp_errors
async def delete_card(card_id: Annotated[int, Path()]):
    """Обработчик. Удаляет запись по первичному ключу"""
    await delete_card_from_bd(card_id)
    return HTTPStatus.OK.value


@router.patch('/update_card/{card_id}', tags=['Card'])
@handle_resp_errors
async def update_card(card_id: Annotated[int, Path()],
                      data: Annotated[CardContent, Body(embed=True)] = None,
                      meta: Optional[CardMeta] = None):
    '''Обрабочтик. Частичное обновление записи'''
    await update_card_in_bd(card_id, data, meta)
    return HTTPStatus.OK.value

@router.get('/search_card/', tags=['Card'])
@handle_resp_errors
async def search_card(q: Annotated[str, Query(max_length=16)]):
    '''Обработчик. Поиск карточки по тексту'''
    return await search_cards_in_bd(q)
