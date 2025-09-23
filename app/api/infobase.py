import logging

from authx.schema import RequestToken

from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

from app.api.template import templates
from app.api.schemas import UserCreate, UserAuth, as_form
from app.site_data import menu_items
from app.DAO import CardDAO, UserDAO
from app.auth import auth

from pydantic import EmailStr

from typing import Annotated

router = APIRouter()

"""Основные обработчик / """
logger = logging.getLogger(__name__)
templates.env.globals['menu'] = menu_items

@router.get('/registration/', tags=['pages'],
            response_class=HTMLResponse)
async def reg(request: Request):
    return templates.TemplateResponse('reg_form.html', {'request': request})


@router.post('/register_form/', tags=['pages'],
             response_model=UserCreate)
async def reg_form(
        username: str = Form(),
        email: EmailStr = Form(),
        password: str = Form(),):
    user = UserCreate(username=username,
                      email=email,
                      password=password)
    await UserDAO.register_user_in_db(user)
    return user

@router.get('/auth/', tags=['pages'],
            response_class=HTMLResponse)
async def log(request: Request):
    return templates.TemplateResponse('login_form.html', {'request': request})

@router.post('/login_form/', tags=['pages'])
async def login(userdata: Annotated[UserAuth, Depends(as_form)]):
    user_id = await UserDAO.login_user_in_db(userdata)
    response = RedirectResponse(url='/cards/', status_code=303)
    
    access_token = auth.create_access_token(uid=str(user_id))
    refresh_token = auth.create_refresh_token(uid=str(user_id))

    auth.set_access_cookies(token=access_token, response=response)
    auth.set_refresh_cookies(token=refresh_token, response=response)

    return response


@router.get('/profile', tags=['pages'],
            response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})


@router.get('/cards/', tags=['pages'],)
async def cards(request: Request, uid = auth.CURRENT_SUBJECT):
    try:
        uid = await uid
        card_list = await CardDAO.get_cards_from_bd(owner_id=uid.id)
        template = templates.TemplateResponse('user.html', {'request': request,
                                                        'cards': card_list})
        return template
    except Exception as e:
        raise HTTPException(401, detail={"message": str(e)}) from e
