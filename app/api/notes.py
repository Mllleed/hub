from app.base import Base
from sqlalchemy import func, text
from sqlalchemy import Integer, Column, String, DateTime, Text, ForeignKey, Table
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional

tag_table = Table(
    'card_tag',
    Base.metadata,
    Column('card_id', Integer, ForeignKey('card_object.id', ondelete='CASCADE')),
    Column('tag_id', Integer, ForeignKey('tag.id', ondelete='CASCADE'))
)

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    
    is_user: Mapped[bool] = mapped_column(default=True, server_default=text('true'), nullable=False)
    is_admin: Mapped[bool] = mapped_column(default=False, server_default=text('false'), nullable=False)

    cards: Mapped['Card'] = relationship('Card', cascade='all, delete-orphan')

class Card(Base):
    __tablename__ = 'card_object'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[Optional[str]] = mapped_column(String(15)) 
    subtitle: Mapped[Optional[str]] = mapped_column(String(30))
    content: Mapped[Optional[str]] = mapped_column(Text)

    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))

    category_id: Mapped[int | None] = mapped_column(Integer, ForeignKey('category.id', ondelete='SET NULL'), nullable=True)
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

