from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import SessionLocal, Base, engine
from models import User, Deck

app = FastAPI()

# Создание таблиц
Base.metadata.create_all(bind=engine)

# Модель для создания колоды
class DeckCreate(BaseModel):
    user_id: int
    name: str

# Получение сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/decks/")
async def create_deck(deck: DeckCreate, db: Session = Depends(get_db)):
    db_deck = Deck(user_id=deck.user_id, name=deck.name)
    db.add(db_deck)
    db.commit()
    db.refresh(db_deck)
    return {"id": db_deck.id, "name": db_deck.name}

@app.get("/decks/{user_id}")
async def get_decks(user_id: int, db: Session = Depends(get_db)):
    decks = db.query(Deck).filter(Deck.user_id == user_id).all()
    return [{"id": deck.id, "name": deck.name} for deck in decks]