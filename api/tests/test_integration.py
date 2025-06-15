import pytest
import time
from fastapi.testclient import TestClient
from main import app, get_db
from models import User, Deck, Card
from sqlalchemy.orm import Session
from sqlalchemy import delete
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture
def client(db_session):
    # Переопределяем get_db, чтобы использовать ту же сессию
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    # Очищаем переопределение
    app.dependency_overrides.clear()

@pytest.fixture
def db_session():
    # Создаём сессию
    db = next(get_db())
    try:
        # Очищаем таблицы
        logger.info("Clearing database tables")
        db.execute(delete(Card))
        db.execute(delete(Deck))
        db.execute(delete(User))
        db.commit()
        yield db
        # Очищаем после теста
        db.execute(delete(Card))
        db.execute(delete(Deck))
        db.execute(delete(User))
        db.commit()
    finally:
        db.close()

def test_user_creates_deck_card_and_translates(client, db_session: Session):
    # Шаг 1: Создаём пользователя
    logger.info("Creating user with telegram_id=123456789")
    user = User(telegram_id=123456789)
    db_session.add(user)
    db_session.commit()
    db_user = db_session.query(User).filter(User.telegram_id == 123456789).first()
    assert db_user is not None, "User not found in database"
    logger.info(f"User created: id={db_user.id}, telegram_id={db_user.telegram_id}")

    # Шаг 2: Создаём колоду (POST /decks/)
    logger.info("Creating deck via POST /decks/")
    deck_response = client.post(
        "/decks/",
        json={
            "telegram_id": 123456789,
            "name": "Test Deck",
            "is_language_deck": False
        }
    )
    assert deck_response.status_code == 200, f"Failed to create deck: {deck_response.text}"
    deck_data = deck_response.json()
    logger.info(f"Deck response: {deck_data}")
    assert deck_data["name"] == "Test Deck", f"Unexpected deck name: {deck_data}"
    deck_id = deck_data.get("id")
    assert deck_id is not None, f"Deck ID is None in response: {deck_data}"
    logger.info(f"Deck created: id={deck_id}, name={deck_data['name']}")

    # Проверяем, что колода сохранена в базе
    db_deck = db_session.get(Deck, deck_id)
    assert db_deck is not None, f"Deck with id={deck_id} not found in database"
    assert db_deck.name == "Test Deck"
    logger.info(f"Deck verified in database: id={db_deck.id}, name={db_deck.name}")

    # Шаг 3: Добавляем карточку (POST /cards/)
    logger.info(f"Creating card for deck_id={deck_id}")
    card_response = client.post(
        "/cards/",
        json={"term": "Hello", "definition": "Greeting", "deck_id": deck_id}
    )
    assert card_response.status_code == 200, f"Failed to create card: {card_response.text}"
    card_data = card_response.json()
    assert card_data["term"] == "Hello"
    card_id = card_data["id"]
    logger.info(f"Card created: id={card_id}, term={card_data['term']}")

    # Проверяем, что карточка сохранена в базе
    db_card = db_session.get(Card, card_id)
    assert db_card is not None
    assert db_card.term == "Hello"
    assert db_card.deck_id == deck_id
    logger.info(f"Card verified in database: id={db_card.id}, term={db_card.term}")

    # Шаг 4: Переводим термин карточки (POST /translate)
    logger.info("Waiting for translate service to be ready")
    time.sleep(5)  # Даём время сервису translate
    logger.info("Translating term 'Hello' from en to ru")
    try:
        translate_response = client.post(
            "/translate",
            json={"q": "Hello", "source": "en", "target": "ru", "format": "text"}
        )
        assert translate_response.status_code == 200, f"Translation failed: {translate_response.text}"
        translate_data = translate_response.json()
        assert "translatedText" in translate_data
        logger.info(f"Translation successful: {translate_data['translatedText']}")
    except AssertionError as e:
        logger.error(f"Translation error: {str(e)}")
        raise
