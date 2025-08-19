import enum
from pydantic import BaseModel, Field
from typing import Optional, Literal, List  

class HTTPStatus(enum.Enum):
    OK = 'GOOG JOB BROTHER'
    BAD = 'NOT GOOD'


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

    class Config:
        orm_mode = True

class TagResponse(BaseModel):
    id: int
    tag_name: Optional[str] = None

    class Config:
        orm_mode = True

class CardResponse(BaseModel):
    id: int
    title: Optional[str] 
    subtitle: Optional[str]
    content: Optional[str]
    category: Optional[CategoryResponse]
    tags: Optional[List[TagResponse]]

    class Config:
        orm_mode = True
class FilterParams(BaseModel):
    order: Literal['desc', 'asc'] = 'desc'
    sort_by: Literal['created_at', 'id', 'title', 'subtitle', 'category', 'tags '] = 'id'
