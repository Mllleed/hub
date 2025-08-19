from models.base import Base
from sqlalchemy import func 
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Table
from sqlalchemy.orm import relationship


tag_table = Table(
    'card_tag',
    Base.metadata,
    Column('card_id', Integer, ForeignKey('card_object.id', ondelete='CASCADE')),
    Column('tag_id', Integer, ForeignKey('tag.id', ondelete='CASCADE'))
)

class Card(Base):
    __tablename__ = 'card_object'

    id = Column(Integer, primary_key=True)
    title = Column(String(30))
    subtitle = Column(String(16))
    content = Column(Text)

    category_id = Column(Integer, ForeignKey('category.id', ondelete='SET NULL'))
    category = relationship('Category', back_populates='cards')

    tags = relationship(
        'Tag',
        secondary=tag_table,
        back_populates='cards',
        passive_deletes=True
    )

    created_at = Column(DateTime(timezone=True),
                        server_default=func.now(), nullable=False) 
    updated_at = Column(DateTime(timezone=True),
                        server_default=func.now(), onupdate=func.now())
    

class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    cat_name = Column(String(12), unique=True)

    cards = relationship(
        'Card',
        back_populates='category',
        passive_deletes=True
    )

class Tag(Base):
    __tablename__ = 'tag'

    id = Column(Integer, primary_key=True)
    tag_name = Column(String(12), unique=True)

    cards = relationship(
        'Card',
        secondary=tag_table,
        back_populates='tags',
        passive_deletes=True
    )

