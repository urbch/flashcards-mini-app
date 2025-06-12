from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True)

class Deck(Base):
    __tablename__ = "decks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    is_language_deck = Column(Boolean, default=False)
    source_lang = Column(String, nullable=True)
    target_lang = Column(String, nullable=True)

    # Добавляем связи для каскадного удаления
    cards = relationship("Card", back_populates="deck", cascade="all, delete-orphan")
    lang_cards = relationship("LangCard", back_populates="deck", cascade="all, delete-orphan")

class LangCard(Base):
    __tablename__ = "lang_cards"
    id = Column(Integer, primary_key=True, index=True)
    deck_id = Column(Integer, ForeignKey("decks.id", ondelete="CASCADE"))
    word = Column(String)
    translation = Column(String)
    
    deck = relationship("Deck", back_populates="lang_cards")

class Card(Base):
    __tablename__ = "cards"
    id = Column(Integer, primary_key=True, index=True)
    deck_id = Column(Integer, ForeignKey("decks.id", ondelete="CASCADE"))
    term = Column(String)
    definition = Column(String)
    
    deck = relationship("Deck", back_populates="cards")
