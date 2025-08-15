from models.base import Base
from sqlalchemy import func 
from sqlalchemy import Column, Integer, String, DateTime, Text

class Card(Base):
    __tablename__ = 'card_object'

    id = Column(Integer, primary_key=True)
    title = Column(String(30))
    subtitle = Column(String(16))
    content = Column(Text)

    created_at = Column(DateTime(timezone=True),
                        server_default=func.now(), nullable=False) 
    updated_at = Column(DateTime(timezone=True),
                        server_default=func.now(), onupdate=func.now())
