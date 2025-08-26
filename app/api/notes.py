from models.base import Base
from sqlalchemy import func 
from sqlalchemy import Integer, Column, String, DateTime, Text, ForeignKey, Table
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional

tag_table = Table(
    'card_tag',
    Base.metadata,
    Column('card_id', Integer, ForeignKey('card_object.id', ondelete='CASCADE')),
    Column('tag_id', Integer, ForeignKey('tag.id', ondelete='CASCADE'))
)

class Card(Base):
    __tablename__ = 'card_object'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[Optional[str]] = mapped_column(String(15)) 
    subtitle: Mapped[Optional[str]] = mapped_column(String(30))
    content: Mapped[Optional[str]] = mapped_column(Text)

    category_id: Mapped[int] = mapped_column(Integer, ForeignKey('category.id', ondelete='SET NULL'))
    category: Mapped[Optional["Category"]] = relationship('Category', back_populates='cards')

    tags: Mapped[Optional[list["Tag"]]] = relationship(
        secondary=tag_table,
        back_populates='cards',
        passive_deletes=True
    )

    created_at: Mapped[str] = mapped_column(DateTime(timezone=True),
                        server_default=func.now(), nullable=False) 
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True),
                        server_default=func.now(), onupdate=func.now())
    

class Category(Base):
    __tablename__ = 'category'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cat_name: Mapped[str] = mapped_column(String(12), unique=True)

    cards: Mapped[list['Card']] = relationship(
        'Card',
        back_populates='category',
    )

class Tag(Base):
    __tablename__ = 'tag'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tag_name: Mapped[str] = mapped_column(String(12), unique=True)

    cards: Mapped[list['Card']] = relationship(
        'Card',
        secondary=tag_table,
        back_populates='tags',
        passive_deletes=True
    )

