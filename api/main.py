from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import SessionLocal, Base, engine
from models import User, Deck, Card
from sqlalchemy import text

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  # Разрешить все методы (GET, POST, OPTIONS, и т.д.)
    allow_headers=["*"],  # Разрешить все заголовки
)

# Создание таблиц
Base.metadata.create_all(bind=engine)

# Модель для создания колоды
class DeckCreate(BaseModel):
    telegram_id: int  # Изменено на telegram_id
    name: str

# Получение сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_or_create_user(telegram_id: int, db: Session):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

@app.post("/decks/")
async def create_deck(deck: DeckCreate, db: Session = Depends(get_db)):
    user = await get_or_create_user(deck.telegram_id, db)
    db_deck = Deck(user_id=user.id, name=deck.name)
    db.add(db_deck)
    db.commit()
    db.refresh(db_deck)
    return {"id": db_deck.id, "name": db_deck.name}

@app.get("/decks/{telegram_id}")
async def get_decks(telegram_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    decks = db.query(Deck).filter(Deck.user_id == user.id).all()
    return [{"id": deck.id, "name": deck.name} for deck in decks]

@app.get("/hello")
async def home():
    return f"have a good day!\n"


@app.get("/db-test")
def db_test():
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT 1"))
        return {"status": "OK", "result": result.scalar()}
    except Exception as e:
        return {"status": "Error", "detail": str(e)}
    finally:
        db.close()
