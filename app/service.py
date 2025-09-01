import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import select
from app.api.notes import Card, Category, Tag
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Settings(BaseSettings):
    DB_HOST: str
    DB_SYNC_URL: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    SECRET_KEY: str
    ALGORITHM: str

    model_config = SettingsConfigDict(
            env_file=os.path.join(BASE_DIR, ".env"),
            env_file_encoding="utf-8"
            )



settings = Settings()

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
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
