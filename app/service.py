import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import select
from app.api.notes import Category, Tag
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from fastapi import Request, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='action/login/')


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

    @staticmethod
    async def create_access_token(data: dict, expires_delta: timedelta = None):
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=60))
        to_encode.update({'exp': expire})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    @staticmethod
    async def decode_access_token(token: str):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError:
            raise HTTPException(
                    status_code=401,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                    )

    @staticmethod
    async def get_current_owner_id(token: str = Depends(oauth2_scheme)) -> int:
        try:
            payload = await Service.decode_access_token(token)
            owner_id: int = payload.get("sub")
            if owner_id is None:
                raise HTTPException(
                        status_code=401,
                        detail="Invalid_token")
            return int(owner_id)
        except JWTError:
            raise HTTPException(status_code=401, detail='Invalid_token')

