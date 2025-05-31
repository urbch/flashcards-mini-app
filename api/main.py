from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import SessionLocal, Base, engine
from models import User, Deck, Card
from fastapi.responses import JSONResponse
import logging
import httpx
from dotenv import load_dotenv
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

class DeckCreate(BaseModel):
    telegram_id: int
    name: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_or_create_user(telegram_id: int, db: Session):
    logger.info(f"Looking for user with telegram_id: {telegram_id}")
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        logger.info(f"Creating new user with telegram_id: {telegram_id}")
        user = User(telegram_id=telegram_id)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

async def get_telegram_user_info(telegram_id: int):
    logger.info(f"Fetching Telegram user info for telegram_id: {telegram_id}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/getChat",
                params={"chat_id": telegram_id}
            )
            data = response.json()
            if not data.get("ok"):
                logger.error(f"Failed to get Telegram user info: {data}")
                raise HTTPException(status_code=400, detail="Failed to fetch user info from Telegram")
            user_info = data["result"]
            return {
                "id": user_info["id"],
                "first_name": user_info.get("first_name", "Unknown"),
                "last_name": user_info.get("last_name", ""),
                "username": user_info.get("username", "")
            }
    except Exception as e:
        logger.error(f"Error fetching Telegram user info: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching user info")

@app.get("/user/{telegram_id}/")
async def get_user_info(telegram_id: int):
    user_info = await get_telegram_user_info(telegram_id)
    return user_info

@app.post("/decks/")
async def create_deck(deck: DeckCreate, db: Session = Depends(get_db)):
    logger.info(f"Received deck creation request: {deck}")
    user = await get_or_create_user(deck.telegram_id, db)
    db_deck = Deck(user_id=user.id, name=deck.name)
    db.add(db_deck)
    db.commit()
    db.refresh(db_deck)
    logger.info(f"Created deck with id: {db_deck.id}, name: {db_deck.name}")
    return {"id": db_deck.id, "name": db_deck.name}

@app.get("/decks/{telegram_id}/", response_class=JSONResponse)
async def get_decks(telegram_id: int, db: Session = Depends(get_db)):
    logger.info(f"Received get decks request for telegram_id: {telegram_id}")
    try:
        telegram_id = int(telegram_id)
    except ValueError:
        logger.error(f"Invalid telegram_id format: {telegram_id}")
        raise HTTPException(status_code=400, detail="Invalid telegram_id")
    
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        logger.warning(f"User not found for telegram_id: {telegram_id}")
        raise HTTPException(status_code=404, detail="User not found")
    
    decks = db.query(Deck).filter(Deck.user_id == user.id).all()
    logger.info(f"Found decks for user {telegram_id}: {decks}")
    return [{"id": deck.id, "name": deck.name} for deck in decks]

@app.get("/hello")
async def home():
    return f"have a good day!\n"