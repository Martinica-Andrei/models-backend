from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from db import Base

class BookCategories(Base):
    __tablename__ = "book_categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(500), nullable=False)
    book_id = Column(Integer(), ForeignKey('book.id'), nullable=False)

    book = relationship('Book', back_populates='categories')