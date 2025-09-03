import logging
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from app.api.template import templates
from app.api.schemas import UserCreate
from app.site_data import menu_items
from app.DAO import CardDAO, UserDAO
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
        email: str = Form(),
        password: str = Form(),):
    user = UserCreate(username=username,
                      email=email,
                      password=password)
    await UserDAO.register_user_in_db(user)
    return user

@router.get('/login/', tags=['pages'],
            response_model=User)
async def login(authenticate_user: Request):

@router.get('/profile', tags=['pages'],
            response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})


@router.get('/cards/', tags=['pages'],
           response_class=HTMLResponse)
async def cards(request: Request):
    card_list = await CardDAO.get_cards_from_bd()
    template = templates.TemplateResponse('user.html', {'request': request,
                                                        'cards': card_list})
    return template
