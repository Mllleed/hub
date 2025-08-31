from pydantic import BaseModel, Field, EmailStr, ConfigDict 
from typing import Optional, Literal, List  
from datetime import datetime


class CookieMeta(BaseModel):
    acces_token: str
    bearer: str


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserIn(BaseModel):
    username: str
    password: str

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
