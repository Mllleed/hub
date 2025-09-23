import os

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.api.notes import Category, Tag

from sqlalchemy import select

from passlib.context import CryptContext

from jose import JWTError

from fastapi import Response, Request, Depends

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

    model_config = SettingsConfigDict(
            env_file=os.path.join(BASE_DIR, ".env"),
            env_file_encoding="utf-8"
            )

settings = Settings()

class Service:
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



