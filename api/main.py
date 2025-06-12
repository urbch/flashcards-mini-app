from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import httpx
import logging
import os
from dotenv import load_dotenv
from functools import lru_cache

from database import SessionLocal, Base, engine
from models import User, Deck, Card, LangCard

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
    is_language_deck: bool = False
    source_lang: Optional[str] = None
    target_lang: Optional[str] = None

class CardCreate(BaseModel):
    deck_id: int
    term: str
    definition: str

class CardUpdate(BaseModel):
    term: str
    definition: str

class LangCardCreate(BaseModel):
    deck_id: int
    word: str
    source_lang: str
    target_lang: str
    translation: Optional[str] = None

class LangCardUpdate(BaseModel):
    word: str
    translation: str

class TranslateRequest(BaseModel):
    q: str
    source: str
    target: str
    format: str = "text"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_or_create_user(telegram_id: int, db: Session) -> User:
    logger.info(f"Fetching user with telegram_id: {telegram_id}")
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        logger.info(f"Creating new user with telegram_id: {telegram_id}")
        user = User(telegram_id=telegram_id)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

async def get_telegram_user_info(telegram_id: int) -> dict:
    logger.info(f"Requesting Telegram user info for telegram_id: {telegram_id}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/getChat",
                params={"chat_id": telegram_id}
            )
            data = response.json()
            if not data.get("ok"):
                logger.error(f"Failed to fetch Telegram user info: {data}")
                raise HTTPException(
                    status_code=400,
                    detail="Failed to fetch user info from Telegram"
                )
            user_info = data["result"]
            return {
                "id": user_info["id"],
                "name": user_info.get("first_name", "Unknown"),
                "last_name": user_info.get("last_name", ""),
                "username": user_info.get("username", "")
            }
    except httpx.RequestError as e:
        logger.error(f"Error fetching Telegram user info: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch Telegram user info: {str(e)}"
        )

async def translate_word(word: str, source_lang: str, target_lang: str) -> str:
    url = "http://translate:5000/translate"
    payload = {
        "q": word,
        "source": source_lang,
        "target": target_lang,
        "format": "text"
    }
    headers = {"Content-Type": "application/json"}
    logger.info(f"Translating word: {word} from {source_lang} to {target_lang}")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            if "translatedText" not in result:
                logger.error(f"Invalid translation response: {result}")
                raise HTTPException(
                    status_code=400,
                    detail="Invalid response from translation service"
                )
            logger.info(f"Translation successful: {result['translatedText']}")
            return result["translatedText"]
    except httpx.HTTPStatusError as e:
        logger.error(f"Translation HTTP error: {e.response.status_code}, {e.response.text}")
        raise HTTPException(
            status_code=400,
            detail=f"Translation failed: {e.response.status_code} {e.response.text}"
        )
    except httpx.RequestError as e:
        logger.error(f"Translation request failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Translation service unavailable: {str(e)}"
        )

@app.get("/users/{telegram_id}/info")
async def get_user_info(telegram_id: int):
    return await get_telegram_user_info(telegram_id)

@app.post("/decks/")
async def create_deck(deck: DeckCreate, db: Session = Depends(get_db)):
    logger.info(f"Creating deck: telegram_id={deck.telegram_id}, name={deck.name}")
    if deck.is_language_deck and (not deck.source_lang or not deck.target_lang):
        logger.error("Missing source or target language for language deck")
        raise HTTPException(
            status_code=400,
            detail="Source and target languages are required for language deck"
        )
    user = await get_or_create_user(deck.telegram_id, db)
    db_deck = Deck(
        user_id=user.id,
        name=deck.name,
        is_language_deck=deck.is_language_deck,
        source_lang=deck.source_lang if deck.is_language_deck else None,
        target_lang=deck.target_lang if deck.is_language_deck else None
    )
    db.add(db_deck)
    db.commit()
    db.refresh(db_deck)
    logger.info(f"Deck created: id={db_deck.id}, name={db_deck.name}")
    return {
        "id": db_deck.id,
        "name": db_deck.name,
        "is_language_deck": db_deck.is_language_deck,
        "source_lang": db_deck.source_lang,
        "target_lang": db_deck.target_lang
    }

@app.get("/decks/{telegram_id}/")
async def get_decks(telegram_id: int, db: Session = Depends(get_db)):
    logger.info(f"Fetching decks for telegram_id: {telegram_id}")
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            logger.warning(f"User not found for telegram_id: {telegram_id}")
            raise HTTPException(status_code=404, detail="User not found")
        decks = db.query(Deck).filter(Deck.user_id == user.id).all()
        logger.info(f"Found {len(decks)} decks for user {telegram_id}")
        return [
            {
                "id": deck.id,
                "name": deck.name,
                "is_language_deck": deck.is_language_deck,
                "source_lang": deck.source_lang,
                "target_lang": deck.target_lang
            }
            for deck in decks
        ]
    except ValueError:
        logger.error(f"Invalid telegram_id format: {telegram_id}")
        raise HTTPException(status_code=400, detail="Invalid telegram_id format")

@app.delete("/decks/{deck_id}")
async def delete_deck(deck_id: int, db: Session = Depends(get_db)):
    logger.info(f"Deleting deck: id={deck_id}")
    db_deck = db.query(Deck).filter(Deck.id == deck_id).first()
    if not db_deck:
        logger.error(f"Deck not found: id={deck_id}")
        raise HTTPException(status_code=404, detail="Deck not found")
    db.delete(db_deck)
    db.commit()
    logger.info(f"Deck deleted: id={deck_id}")
    return {"message": "Deck deleted successfully"}

@app.post("/cards/")
async def create_card(card: CardCreate, db: Session = Depends(get_db)):
    logger.info(f"Creating card for deck_id: {card.deck_id}")
    deck = db.query(Deck).filter(Deck.id == card.deck_id).first()
    if not deck:
        logger.error(f"Deck not found: id={card.deck_id}")
        raise HTTPException(status_code=404, detail="Deck not found")
    db_card = Card(
        deck_id=card.deck_id,
        term=card.term,
        definition=card.definition
    )
    db.add(db_card)
    db.commit()
    db.refresh(db_card)
    logger.info(f"Card created: id={db_card.id}, deck_id={db_card.deck_id}")
    return {
        "id": db_card.id,
        "deck_id": db_card.deck_id,
        "term": db_card.term,
        "definition": db_card.definition
    }

@app.get("/cards/{deck_id}")
async def get_cards(deck_id: int, db: Session = Depends(get_db)):
    logger.info(f"Fetching cards for deck_id: {deck_id}")
    deck = db.query(Deck).filter(Deck.id == deck_id).first()
    if not deck:
        logger.error(f"Deck not found: id={deck_id}")
        raise HTTPException(status_code=404, detail="Deck not found")
    cards = db.query(Card).filter(Card.deck_id == deck_id).all()
    logger.info(f"Found {len(cards)} cards for deck_id: {deck_id}")
    return [
        {
            "id": card.id,
            "deck_id": card.deck_id,
            "term": card.term,
            "definition": card.definition
        }
        for card in cards
    ]

@app.put("/cards/{card_id}")
async def update_card(card_id: int, card: CardUpdate, db: Session = Depends(get_db)):
    logger.info(f"Updating card: id={card_id}")
    db_card = db.query(Card).filter(Card.id == card_id).first()
    if not db_card:
        logger.error(f"Card not found: id={card_id}")
        raise HTTPException(status_code=404, detail="Card not found")
    db_card.term = card.term
    db_card.definition = card.definition
    db.commit()
    db.refresh(db_card)
    logger.info(f"Card updated: id={db_card.id}")
    return {
        "id": db_card.id,
        "deck_id": db_card.deck_id,
        "term": db_card.term,
        "definition": db_card.definition
    }

@app.delete("/cards/{card_id}")
async def delete_card(card_id: int, db: Session = Depends(get_db)):
    logger.info(f"Deleting card: id={card_id}")
    db_card = db.query(Card).filter(Card.id == card_id).first()
    if not db_card:
        logger.error(f"Card not found: id={card_id}")
        raise HTTPException(status_code=404, detail="Card not found")
    db.delete(db_card)
    db.commit()
    logger.info(f"Card deleted: id={card_id}")
    return {"message": "Card deleted successfully"}

@app.post("/lang_cards/")
async def create_lang_card(card: LangCardCreate, db: Session = Depends(get_db)):
    logger.info(f"Creating language card for deck_id: {card.deck_id}, word: {card.word}")
    deck = db.query(Deck).filter(Deck.id == card.deck_id).first()
    if not deck or not deck.is_language_deck:
        logger.error(f"Invalid deck for language cards: id={card.deck_id}")
        raise HTTPException(status_code=400, detail="Invalid deck for language cards")

    # Если translation не предоставлен, используем автоперевод
    translation = card.translation
    if translation is None:
        try:
            translation = await translate_word(card.word, card.source_lang, card.target_lang)
        except HTTPException as e:
            logger.error(f"Translation error: {e.detail}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during translation: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error during translation")

    db_card = LangCard(
        deck_id=card.deck_id,
        word=card.word,
        translation=translation
    )
    db.add(db_card)
    db.commit()
    db.refresh(db_card)
    logger.info(f"Language card created: id={db_card.id}, deck_id={db_card.deck_id}")
    return {
        "id": db_card.id,
        "deck_id": db_card.deck_id,
        "word": db_card.word,
        "translation": db_card.translation
    }

@lru_cache(maxsize=1000)
async def cached_translate(word: str, source_lang: str, target_lang: str) -> str:
    logger.info(f"Translating word: {word} from {source_lang} to {target_lang}")
    url = "http://translate:5000/translate"
    payload = {
        "q": word,
        "source": source_lang,
        "target": target_lang,
        "format": "text"
    }
    headers = {"Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            if "translatedText" not in result:
                logger.error(f"Invalid translation response: {result}")
                raise HTTPException(
                    status_code=400,
                    detail="Invalid response from translation service"
                )
            logger.info(f"Translation successful: {result['translatedText']}")
            return result["translatedText"]
    except httpx.HTTPStatusError as e:
        logger.error(f"Translation HTTP error: {e.response.status_code}, {e.response.text}")
        raise HTTPException(
            status_code=400,
            detail=f"Translation failed: {e.response.status_code} {e.response.text}"
        )
    except httpx.RequestError as e:
        logger.error(f"Translation request failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Translation service unavailable: {str(e)}"
        )

@app.post("/translate")
async def translate(req: TranslateRequest):
    logger.info(f"Translate request: {req.model_dump()}")
    try:
        translated_text = await cached_translate(req.q, req.source, req.target)
        logger.info(f"Translate response: {translated_text}")
        return {"translatedText": translated_text}
    except HTTPException as e:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during translation: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during translation")

@app.get("/lang_cards/{deck_id}")
async def get_lang_cards(deck_id: int, db: Session = Depends(get_db)):
    logger.info(f"Fetching language cards for deck_id: {deck_id}")
    deck = db.query(Deck).filter(Deck.id == deck_id).first()
    if not deck or not deck.is_language_deck:
        logger.error(f"Invalid deck for language cards: id={deck_id}")
        raise HTTPException(status_code=400, detail="Invalid deck for language cards")
    cards = db.query(LangCard).filter(LangCard.deck_id == deck_id).all()
    logger.info(f"Found {len(cards)} language cards for deck_id: {deck_id}")
    return [
        {
            "id": card.id,
            "deck_id": card.deck_id,
            "word": card.word,
            "translation": card.translation
        }
        for card in cards
    ]

@app.put("/lang_cards/{card_id}")
async def update_lang_card(card_id: int, card: LangCardUpdate, db: Session = Depends(get_db)):
    logger.info(f"Updating language card: id={card_id}")
    db_card = db.query(LangCard).filter(LangCard.id == card_id).first()
    if not db_card:
        logger.error(f"Language card not found: id={card_id}")
        raise HTTPException(status_code=404, detail="Language card not found")
    db_card.word = card.word
    db_card.translation = card.translation
    db.commit()
    db.refresh(db_card)
    logger.info(f"Language card updated: id={db_card.id}")
    return {
        "id": db_card.id,
        "deck_id": db_card.deck_id,
        "word": db_card.word,
        "translation": db_card.translation
    }

@app.delete("/lang_cards/{card_id}")
async def delete_lang_card(card_id: int, db: Session = Depends(get_db)):
    logger.info(f"Deleting language card: id={card_id}")
    db_card = db.query(LangCard).filter(LangCard.id == card_id).first()
    if not db_card:
        logger.error(f"Language card not found: id={card_id}")
        raise HTTPException(status_code=404, detail="Language card not found")
    db.delete(db_card)
    db.commit()
    logger.info(f"Language card deleted: id={card_id}")
    return {"message": "Language card deleted successfully"}

@app.get("/languages/")
async def get_languages():
    logger.info("Fetching available languages from LibreTranslate")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("http://translate:5000/languages")
            response.raise_for_status()
            logger.info("Languages fetched successfully")
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Failed to fetch languages: {e.response.status_code}, {e.response.text}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch languages: {e.response.status_code}"
        )
    except httpx.RequestError as e:
        logger.error(f"Language request failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Language service unavailable: {str(e)}"
        )

@app.get("/hello")
async def home():
    return {"message": "Have a good day!"}
