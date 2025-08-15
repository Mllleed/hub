import enum
from pydantic import BaseModel, Field
from typing import Optional, Literal

class HTTPStatus(enum.Enum):
    OK = 'GOOG JOB BROTHER'
    BAD = 'NOT GOOD'
    
class CardContent(BaseModel):
    title: Optional[str] = Field(default=None, description='desc of card', max_length=30)
    subtitle: Optional[str] = None
    content: Optional[str] = None


class FilterParams(BaseModel):
    order: Literal['desc', 'asc'] = 'desc'
    sort_by: Literal['created_at', 'id'] = 'id'
