from sqlalchemy import select
from api.notes import Card, Category, Tag
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
SECRET_KEY = '123'
ALGORITHM = 'HS256'

class Service():
    @staticmethod
    async def get_or_create_category(session, name: str) -> Category:
        stmt = select(Category).where(Category.cat_name == name)
        result = await session.execute(stmt)
        category = result.scalar_one_or_none()

        if not category:
            category = Category(cat_name=name)
            session.add(category)
        return category

    @staticmethod
    async def get_or_create_tag(session, name: str) -> Tag:
        stmt = select(Tag).where(Tag.tag_name == name)
        result = await session.execute(stmt)
        tag = result.scalar_one_or_none()
        if not tag:
            tag = Tag(tag_name=name)
            session.add(tag)
        return tag

    @staticmethod
    async def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    async def verify_method(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    async def create_access_token(data: dict, expires_delta: timedelta = None):
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))
        to_encode.update({'exp': expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
