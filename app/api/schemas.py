from hmac import compare_digest

from pydantic import BaseModel, Field, EmailStr, ConfigDict, validator, ValidationError

from typing import Optional, Literal, List, Union, Any  

from datetime import timedelta, datetime

from app.utils._utils import get_uuid, get_now_ts, get_now
from app.utils.exceptions import (AccessTokenRequiredError, JWTDecodeError, FreshTokenRequiredError,
                                  RefreshTokenRequiredError, TokenTypeError, CSRFError)

from fastapi import Form

from app.types._types import (StringOrSequence, DateTimeExpression, Numeric,
                              AlgorithmType, Sequence, TokenType, TokenLocation)
from app.token import create_token, decode_token

class CookieMeta(BaseModel):
    acces_token: str
    bearer: str

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserAuth(BaseModel):
    username: str
    password: str

def as_form(
        username: str = Form(...),
        password: str = Form(...)) -> UserAuth:
    return UserAuth(username=username, password=password)
class UserLogin(BaseModel):
    id: int
    token: str

class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr 
    
    model_config = ConfigDict(from_attributes=True)

class CardContent(BaseModel):
    title: Optional[str] = Field(default=None, description='desc of card', max_length=30)
    subtitle: Optional[str] = None
    content: Optional[str] = None


class CardMeta(BaseModel):
    cat: Optional[str] = Field(default=None, max_length=12)
    tag: Optional[List[str]] = Field(default=None)


class CardRequest(BaseModel):
    data: CardContent
    meta: CardMeta

class CategoryResponse(BaseModel):
    id: int
    cat_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class TagResponse(BaseModel):
    id: int
    tag_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class CardResponse(BaseModel):
    id: int
    title: Optional[str] = None
    subtitle: Optional[str] = None
    content: Optional[str] = None
    category: Optional[CategoryResponse] = None
    tags: Optional[List[TagResponse]] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class FilterParams(BaseModel):
    order: Literal['desc', 'asc'] = 'desc'
    sort_by: Literal['created_at', 'id', 'title', 'subtitle'] = 'id'
    cat: Optional[str] = None
    tag: Optional[str] = None
    limit: Optional[int] = 5
    offset: Optional[int] = 0


class TokenPayload(BaseModel):
    jti: Optional[str] = Field(default_factory=get_uuid)
    iss: Optional[str] = None
    sub: str
    aud: Optional[StringOrSequence] = None
    exp: Optional[DateTimeExpression] = None
    nbf: Optional[Union[Numeric, DateTimeExpression]] = None
    iat: Optional[Union[Numeric, DateTimeExpression]] = Field(default_factory=lambda: int(get_now_ts()))
    type: Optional[str] = Field(
            default='access',
            description='token type',
            )
    csrf: Optional[str] = ""
    scopes: Optional[list[str]] = None
    fresh: bool = False

    @property
    def issued_at(self) -> datetime:
        if isinstance(self.iat, (float, int)):
            return datetime.datetime.fromtimestamp(self.iat, tz=datetime.timezone.utc)
        if isinstance(self.iat, datetime.datetime):
            return self.iat
        else:
            raise TypeError("'iat' claim should be of type float | int | datetime.datetime")

    @property
    def expiry_datetime(self) -> datetime:
        if isinstance(self.exp, datetime):
            return self.exp
        elif isinstance(self.exp, timedelta):
            return self.issued_at + self.exp
        elif isinstance(self.exp, (float, int)):
            return datetime.datetime.fromtimestamp(self.exp, tz=datetime.timezone.utc)
        else:
             raise TypeError("'exp' claim should be of type float | int | datetime.datetime")

    @property
    def time_until_expiry(self) -> timedelta:
        return self.expiry_datetime - get_now()

    @property
    def time_since_issued(self) -> timedelta:
        return get_now() - self.issued_at

    @validator('exp', 'nbf', pre=True)
    def _set_default_ts(
            cls, value: Union[float, int, datetime, timedelta]) -> Union[float, int]:
        if isinstance(value, datetime):
            return value.timestamp()
        elif isinstance(value, timedelta):
            return (get_now() + value).timestamp()
        return value

    def encode(
            self,
            key: str,
            algorithm: AlgorithmType = "HS256",
            ignore_errors: bool = True,
            headers: Optional[dict[str, Any]] = None,
            data: Optional[dict[str, Any]] = None,
            ) -> str:
        return create_token(
                key=key,
                algorithm=algorithm,
                uid = str(self.sub),
                jti=self.jti,
                issued=self.iat,
                type=self.type,
                expiry=self.exp,
                fresh=self.fresh,
                csrf=self.csrf,
                audience=self.aud,
                issuer=self.iss,
                not_before=self.nbf,
                ignore_errors=ignore_errors,
                headers=headers,
                data=data,
                )
    @classmethod
    def decode(cls,
        token: str,
        key: str,
        algorithms: Optional[Sequence[AlgorithmType]] = None,
        audience: Optional[StringOrSequence] = None,
        issuer: Optional[str] = None,
        verify: bool = True,) -> "TokenPayload":

        if algorithms is None:
            algorithms = ["HS256"]
        payload = decode_token(
                token=token,
                key=key,
                algorithms=algorithms,
                audience=audience,
                issuer=issuer,
                verify=verify,
                )

        return cls.model_validate(payload)

class RequestToken(BaseModel):
    token: str = Field(..., decsription="The token to verify")
    csrf: Optional[str] = None
    type: TokenType = 'access'
    location: TokenLocation

    def verify(
            self, key: str,
            algorithms: Optional[Sequence[AlgorithmType]]= None,
            audience: Optional[StringOrSequence] = None,
            issuer: Optional[str] = None,
            verify_jwt: bool = True,
            verify_type: bool = True,
            verify_csrf: bool = True,
            verify_fresh: bool = False) -> TokenPayload:
        if algorithms is None:
            algorithms = ["HS256"]
        try:
            decoded_token = decode_token(
                    token=self.token,
                    key=key,
                    algorithms=algorithms,
                    verify=verify_jwt,
                    audience=audience,
                    issuer=issuer,
                    )
            payload = TokenPayload.model_validate(decoded_token)
        except JWTDecodeError as e:
            raise JWTDecodeError(*e.args) from e
        except ValidationError as e:
            raise JWTDecodeError(*e.args) from e

        if verify_type and (self.type != payload.type):
            error_msg = f"'{self.type}' token requied, '{payload.type}' token received"
            if self.type == 'access':
                raise AccessTokenRequiredError(error_msg)
            elif self.type == 'refresh':
                raise RefreshTokenRequiredError(error_msg)
            raise TokenTypeError(error_msg)

        if verify_fresh and not payload.fresh:
            raise FreshTokenRequiredError("Fresh token required")

        if verify_csrf and self.location == 'cookies':
            if self.csrf is None:
                 raise CSRFError(f"Missing CSRF token in {self.location}")
            if payload.csrf is None:
                raise CSRFError("Cookies token missing CSRF claim")
            if not compare_digest(self.csrf, payload.csrf):
                raise CSRFError("CSRF token mismatch")

        return payload
