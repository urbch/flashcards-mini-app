from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey, Boolean
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
    is_language_deck = Column(Boolean, default=False)  # Отличает языковые колоды
    source_lang = Column(String, nullable=True)        # Исходный язык
    target_lang = Column(String, nullable=True)        # Целевой язык

class LangCard(Base):
    __tablename__ = "lang_cards"
    id = Column(Integer, primary_key=True, index=True)
    deck_id = Column(Integer, ForeignKey("decks.id"))
    word = Column(String)
    translation = Column(String)

class Card(Base):
    __tablename__ = "cards"
    id = Column(Integer, primary_key=True, index=True)
    deck_id = Column(Integer, ForeignKey("decks.id"))
    term = Column(String)
    definition = Column(String)