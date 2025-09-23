import traceback

import logging

from functools import wraps

from fastapi import APIRouter, Query, Body, Path, HTTPException

from typing import Optional, Annotated, List, Any

from app.api.schemas import CardContent, FilterParams, CardMeta, CardResponse, UserCreate, UserOut, CardRequest
from app.auth import auth
from app.DAO import CardDAO, UserDAO



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
            )
async def index_html():
    """Это рофлс."""
    pass

@router.post('/register/',
             tags=['registration'],
             response_model=UserOut,
             status_code=201)
@handle_resp_errors
async def register_user(userdata: UserCreate) -> Any: 
    """Обработчик. Регистрация пользователя."""
    result = await UserDAO.register_user_in_db(userdata)
    return UserOut.model_validate(result)
    
# @router.post('/login/',
#              tags=['login'],
#              response_model=CookieMeta)
# @handle_resp_errors
# async def login_user(userdata: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Any:
#     """Обработчик. Авторизация пользователя."""
#     result = await UserDAO.login_user_in_db(userdata)
#     response = JSONResponse(content=result)
#     response.set_cookie(
#             key='access_token',
#             value=result['access_token'],
#             httponly=True,
#             secure=False,
#             samesite=None,
#             max_age=60 * 15,
#             )
#     return response

@router.get('/get_card/{card_id}/',
           tags=['Card'],
           response_model=CardResponse)
@handle_resp_errors
async def get_card_by_id(card_id: Annotated[Optional[int], Path(...,)],
                         uid = auth.CURRENT_SUBJECT):
    """Обработчик. Возвращает карточку по id."""
    card = await CardDAO.get_card_by_id_from_bd(card_id, uid.id)
    return card


@router.get('/get_card/',
            tags=['Card'],
            response_model=List[CardResponse])
@handle_resp_errors
async def get_cards(uid = auth.CURRENT_SUBJECT,
                    sort_param: Annotated[FilterParams, Query()] = None):
    """Обработчик. Получает сортированный список карточек."""
    uid = await uid
    if sort_param:
        logger.info(sort_param)
    data = sort_param.model_dump()
    res =  await CardDAO.get_cards_from_bd(uid.id, **data)
    return res


@router.post('/create_card/',
             tags=['Card'],
             response_model=CardResponse,
             status_code=201)
@handle_resp_errors
async def create_card(payload: CardRequest,
                      uid = auth.CURRENT_SUBJECT):
    """Обработчик. Создает карточку в базе данных."""
    uid = await uid
    card = await CardDAO.create_card_in_bd(payload.data.title, payload.data.subtitle, payload.data.content,
                                           uid.id, payload.meta.model_dump())
    return card 


@router.delete('/delete_card/{card_id}', tags=['Card'])
@handle_resp_errors
async def delete_card(card_id: Annotated[int, Path(...)],
                      uid = auth.CURRENT_SUBJECT):
    """Обработчик. Удаляет запись по первичному ключу."""
    uid = await uid
    await CardDAO.delete_card_from_bd(card_id, uid.id)
    return HTTPException(status_code=204, detail='Картчка удалена')


@router.patch('/update_card/{card_id}', tags=['Card'])
@handle_resp_errors
async def update_card(card_id: Annotated[int, Path(...)],
                      uid = auth.CURRENT_SUBJECT,
                      data: Annotated[CardContent, Body(embed=True)] = None,
                      meta: Optional[CardMeta] = None):
    """Обрабочтик. Частичное обновление записи."""
    uid = await uid
    await CardDAO.update_card_in_bd(card_id, uid.id, data, meta)
    return HTTPException(status_code=200, detail='Обновление выполнено')

@router.get('/search_card/', tags=['Card'])
@handle_resp_errors
async def search_card(q: Annotated[str, Query(max_length=16)],
                      uid = auth.CURRENT_SUBJECT):
    """Обработчик. Поиск карточки по тексту"""
    uid = await uid
    return await CardDAO.search_cards_in_bd(q, uid.id)
