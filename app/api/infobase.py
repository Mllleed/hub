import logging
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from app.api.template import templates
from app.api.schemas import UserCreate
from app.site_data import menu_items
from app.DAO import CardDAO, UserDAO
from pydantic import EmailStr
from typing import Annotated
from app.service import Service

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
async def login(userdata: Annotated[OAuth2PasswordRequestForm, Depends()]):
    result = await UserDAO.login_user_in_db(userdata)
    response = RedirectResponse(url='/cards/', status_code=303)

    response.set_cookie(
        key='access_token',
        value=result['access_token'],
        httponly=True,
        secure=True,
        samesite='strict',
        max_age=60 * 15,
    )
    return response


@router.get('/profile', tags=['pages'],
            response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})


@router.get('/cards/', tags=['pages'],
           response_class=HTMLResponse)
async def cards(request: Request):
    token = request.cookies.get('access_token')
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    owner_id = await Service.get_current_owner_id(token)
    card_list = await CardDAO.get_cards_from_bd(owner_id=owner_id)
    template = templates.TemplateResponse('user.html', {'request': request,
                                                        'cards': card_list})
    return template
