import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.api.schemas import TokenPayload, RequestToken
from app.api.notes import Category, Tag

from sqlalchemy import select

from passlib.context import CryptContext

from jose import JWTError


from fastapi import Response, Request
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import RedirectResponse

from app.types._types import DateTimeExpression, StringOrSequence, TokenLocations, SameSitePolicy, AlgorithmType, T

from typing import Optional, Any, overload, Literal

from app.utils._utils import get_uuid, get_now_ts
from app.utils.exceptions import MissingTokenError

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
    JWT_ALGORITHM: AlgorithmType = 'HS256'
    ACCESS_TOKEN_EXPIRES: str
    REFRESH_TOKEN_EXPIRES: str

    JWT_DECODE_AUDIENCE: Optional[StringOrSequence] = None
    JWT_DECODE_ISSUER: Optional[str] = None

    JWT_COOKIE_CSRF_PROTECT: bool = True
    JWT_TOKEN_LOCATION: TokenLocations = Field(default_factory=lambda: ["headers"])
    JWT_ENCODE_AUDIENCE: Optional[StringOrSequence] = None
    JWT_ENCODE_ISSUER: Optional[str] = None

    JWT_ACCESS_COOKIE_NAME: str = "access_token_cookie"
    JWT_ACCESS_COOKIE_PATH: str = "/"
    JWT_ACCESS_CSRF_COOKIE_NAME: str = "csrf_access_token"
    JWT_ACCESS_CSRF_COOKIE_PATH: str = "/"

    JWT_REFRESH_CSRF_COOKIE_NAME: str = "csrf_refresh_token"
    JWT_REFRESH_CSRF_COOKIE_PATH: str = "/"
    JWT_REFRESH_CSRF_COOKIE_NAME: str = "csrf_refresh_token"
    JWT_REFRESH_CSRF_COOKIE_PATH: str = "/"
    JWT_REFRESH_COOKIE_NAME: str = "refresh_token_cookie"
    JWT_REFRESH_COOKIE_PATH: str = "/"

    JWT_COOKIE_DOMAIN: Optional[str] = None
    JWT_COOKIE_SAMESITE: Optional[SameSitePolicy] = "lax"
    JWT_COOKIE_SECURE: bool = True
    JWT_COOKIE_HTTP_ONLY: bool = True
    JWT_COOKIE_MAX_AGE: Optional[int] = None
    JWT_CSRF_IN_COOKIES: bool = True

    def has_location(self, location: str) -> bool:
        return location in self.JWT_TOKEN_LOCATION



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
    

class Auth:
    def _create_payload(self, uid: str, type: str,
                              fresh: bool = False,
                              expiry: Optional[DateTimeExpression] = None,
                              data: Optional[DateTimeExpression] = None,
                              audience: Optional[StringOrSequence] = None,
                              **kwargs: Any,
                              ) -> TokenPayload:
        if data is None:
            data = {}

        exp = expiry
        if exp is None:
            exp = settings.ACCESS_TOKEN_EXPIRES if type == 'access' else settings.REFRESH_TOKEN_EXPIRES

        csrf = ""
        if settings.has_location("cookies") and settings.JWT_COOKIE_CSRF_PROTECT:
            csrf = get_uuid()

        aud = audience
        if aud is None:
            aud = settings.JWT_ENCODE_AUDIENCE

        return TokenPayload(
                sub=uid, fresh=fresh, exp=exp,
                type=type, iss=settings.JWT_ENCODE_ISSUER, aud=aud,
                csrf=csrf,
                nbf=None,
                **data,
                )

    def _create_token(self, uid: str, type: str, 
                            fresh: bool = False,
                            headers: Optional[dict[str, Any]] = None,
                            expiry: Optional[DateTimeExpression] = None,
                            data: Optional[dict[str, Any]] = None,
                            audience: Optional[StringOrSequence] = None,
                            **kwargs: Any ) -> str:
        payload = self._create_payload(
            uid=uid,
            type=type,
            fresh=fresh,
            expiry=expiry,
            data=data,
            audience=audience,
            **kwargs,
        )
        return payload.encode(key=settings.SECRET_KEY,
                algorithm=settings.JWT_ALGORITHM,
                )

    def _decode_token(
        self,
        token: str,
        verify: bool = True,
        audience: Optional[StringOrSequence] = None,
        issuer: Optional[str] = None,
    ) -> TokenPayload:
        return TokenPayload.decode(
            token=token,
            key=settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            verify=verify,
            audience=audience or settings.JWT_DECODE_AUDIENCE,
            issuer=issuer or settings.JWT_DECODE_ISSUER,
        )

    def create_access_token(self,
            uid: str,
            fresh: bool = False,
            headers: Optional[dict[str, Any]] = None,
            expiry: Optional[DateTimeExpression] = None,
            data: Optional[dict[str, Any]] = None,
            audience: Optional[StringOrSequence] = None,
            *args: Any,
            **kwargs: Any,) -> str:
        return self._create_token(
                uid=uid,
                type='access',
                fresh=fresh,
                headers=headers,
                expiry=expiry,
                data=data,
                audience=audience,
                ) 

    def create_refresh_token(
        self,
        uid: str,
        headers: Optional[dict[str, Any]] = None,
        expiry: Optional[DateTimeExpression] = None,
        data: Optional[dict[str, Any]] = None,
        audience: Optional[StringOrSequence] = None,
        *args: Any,
        **kwargs: Any,
    ) -> str:

        return self._create_token(
            uid=uid,
            type="refresh",
            headers=headers,
            expiry=expiry,
            data=data,
            audience=audience,
        )

    def _set_cookies(
            self, token: str, type: str, response: Response,
            max_age: Optional[int] = None,
            *args: Any,
            **kwargs: Any,) -> None:
        if type == 'access':
            token_key = settings.JWT_ACCESS_COOKIE_NAME
            token_path = settings.JWT_ACCESS_COOKIE_PATH
            csrf_key = settings.JWT_ACCESS_CSRF_COOKIE_NAME
            csrf_path = settings.JWT_ACCESS_CSRF_COOKIE_PATH
        elif type == 'refresh':
            token_key = settings.JWT_REFRESH_COOKIE_NAME
            token_path = settings.JWT_REFRESH_COOKIE_PATH
            csrf_key = settings.JWT_REFRESH_CSRF_COOKIE_NAME
            csrf_path = settings.JWT_REFRESH_CSRF_COOKIE_PATH
        else:
            raise ValueError("Token type must be 'access' | 'refresh'")
        response.set_cookie(
                key=token_key,
                value=token,
                path=token_path,
                domain=settings.JWT_COOKIE_DOMAIN,
                samesite=settings.JWT_COOKIE_SAMESITE,
                secure=settings.JWT_COOKIE_SECURE,
                httponly=settings.JWT_COOKIE_HTTP_ONLY,
                max_age=max_age or settings.JWT_COOKIE_MAX_AGE,)

        if settings.JWT_COOKIE_CSRF_PROTECT and settings.JWT_CSRF_IN_COOKIES:
            csrf = self._decode_token(token=token, verify=True).csrf
            str_csrf = csrf if csrf is not None else ""
            response.set_cookie(
                key=csrf_key,
                value=str_csrf,
                path=csrf_path,
                domain=settings.JWT_COOKIE_DOMAIN,
                samesite=settings.JWT_COOKIE_SAMESITE,
                secure=settings.JWT_COOKIE_SECURE,
                httponly=False,
                max_age=max_age or settings.JWT_COOKIE_MAX_AGE,
            )

    def set_access_cookies(
            self,
            token: str, response: Response,
            max_age: Optional[int] = None) -> None:
        self._set_cookies(token=token, type='access', response=response, max_age=max_age)

    def set_refresh_cookies(
            self, token: str, response: Response,
            max_age: Optional[int] = None) -> None:
        self._set_cookies(token=token, type='refresh', response=response, max_age=max_age)

    @overload
    async def _get_token_from_request(
            self, request: Request,
            locations: Optional[TokenLocations]= None,
            refresh: bool = False,
            optional: Literal[False] = False,) -> RequestToken: ...

    @overload
    async def _get_token_from_request(
            self, request: Request,
            locations: Optional[TokenLocations] = None,
            refresh: bool = False,
            optional: Literal[True] = True) -> Optional[RequestToken]: ...

    async def _get_token_from_request(
            self, request: Request,
            locations: Optional[TokenLocations] = None,
            refresh: bool = False,
            optional: bool = False) -> Optional[RequestToken]:

        if locations is None:
            default_locations = set(self.config.JWT_TOKEN_LOCATION)
            locations = list(default_locations.intersection(['cookies', 'json']) if refresh else default_locations)

            try:
                return await auth._get_token_from_request(
                        request=request,
                        refresh=refresh,
                        locations=locations,)
            except MissingTokenError:
                if optional:
                    return None
                raise
    @staticmethod
    async def get_current_owner_id(request: Request) -> Optional[T]:
        access_token = request.cookies.get('access_token_cookie')
        refresh_token = request.cookies.get('refresh_token_cookie')

        if not access_token:
            return RedirectResponse(url='/auth/', status_code=303)

        try:
            payload = auth._decode_token(token=access_token)

            if not payload.exp is None:
                if payload.exp < get_now_ts():
                    raise JWTError('expired')
            return int(payload.sub)
        except JWTError:
            if refresh_token:
                try:
                    refresh_payload = auth._decode_token(refresh_token)
                    new_access = auth.create_access_token(uid=refresh_payload.sub)
                    
                    response = RedirectResponse(url=request.url.path, status_code=303)
                    response.set_cookie(
                            key='access_token',
                            value=new_access,
                            httponly=True,
                            max_age=settings.ACCESS_TOKEN_EXPIRES.total_seconds(),
                            )
                    return response
                except JWTError:
                    pass
        return RedirectResponse(url='/auth/', status_code=303)

    async def get_access_token_from_request(self, request: Request,
                                            locations: Optional[TokenLocations] = None
                ) -> RequestToken:
        return await self._get_token_from_request(request, optional=False, locations=locations)

    async def get_refresh_token_from_request(self, request: Request,
                                             locations: Optional[TokenLocations] = None) -> RequestToken:
        return await self._get_token_from_request(request, refresh=True, optional=False, locations=locations)

auth = Auth()
