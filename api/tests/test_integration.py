import pytest
import httpx
import asyncio
from fastapi.testclient import TestClient
from main import app, get_db
from models import User, Deck, Card, LangCard
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
    # Создаем сессию
    db = next(get_db())
    try:
        # Очищаем таблицы
        logger.info("Очистка таблиц базы данных")
        db.execute(delete(LangCard))
        db.execute(delete(Card))
        db.execute(delete(Deck))
        db.execute(delete(User))
        db.commit()
        yield db
        # Очищаем после теста
        db.execute(delete(LangCard))
        db.execute(delete(Card))
        db.execute(delete(Deck))
        db.execute(delete(User))
        db.commit()
    finally:
        db.close()

async def wait_for_translate_service():
    """Ожидание готовности сервиса перевода с использованием healthcheck"""
    logger.info("Ожидание готовности сервиса перевода")
    url = "http://translate:5000/languages"
    max_attempts = 10
    attempt = 1
    async with httpx.AsyncClient(timeout=5.0) as client:
        while attempt <= max_attempts:
            try:
                response = await client.get(url)
                response.raise_for_status()
                logger.info("Сервис перевода готов")
                return True
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                logger.warning(f"Попытка {attempt}/{max_attempts}: Сервис перевода недоступен: {str(e)}")
                attempt += 1
                await asyncio.sleep(2)  # Задержка 2 секунды между попытками
        logger.error("Сервис перевода не стал доступен после максимального количества попыток")
        return False

@pytest.mark.asyncio
async def test_user_full_journey(client, db_session: Session):
    """
    Интеграционный тест, покрывающий пользовательскую историю:
    - Создание пользователя
    - Создание обычной и языковой колоды
    - Добавление карточек (обычных и языковых с автопереводом)
    - Получение карточек для симуляции режима изучения
    - Удаление карточек и колоды
    - Проверка корректности данных
    """
    # Шаг 1: Создаем пользователя
    logger.info("Создание пользователя с telegram_id=123456789")
    user = User(telegram_id=123456789)
    db_session.add(user)
    db_session.commit()
    db_user = db_session.query(User).filter(User.telegram_id == 123456789).first()
    assert db_user is not None, "Пользователь не найден в базе данных"
    logger.info(f"Пользователь создан: id={db_user.id}, telegram_id={db_user.telegram_id}")

    # Шаг 2: Создаем обычную колоду (POST /decks/)
    logger.info("Создание обычной колоды через POST /decks/")
    deck_response = client.post(
        "/decks/",
        json={
            "telegram_id": 123456789,
            "name": "Тестовая колода",
            "is_language_deck": False
        }
    )
    assert deck_response.status_code == 200, f"Не удалось создать колоду: {deck_response.text}"
    deck_data = deck_response.json()
    logger.info(f"Ответ по колоде: {deck_data}")
    assert deck_data["name"] == "Тестовая колода", f"Неправильное имя колоды: {deck_data}"
    assert deck_data["is_language_deck"] is False, "Колода не должна быть языковой"
    deck_id = deck_data.get("id")
    assert deck_id is not None, f"ID колоды отсутствует в ответе: {deck_data}"
    logger.info(f"Колода создана: id={deck_id}, name={deck_data['name']}")

    # Проверяем, что колода сохранена в базе
    db_deck = db_session.get(Deck, deck_id)
    assert db_deck is not None, f"Колода с id={deck_id} не найдена в базе данных"
    assert db_deck.name == "Тестовая колода"
    assert db_deck.user_id == db_user.id
    logger.info(f"Колода подтверждена в базе: id={db_deck.id}, name={db_deck.name}")

    # Шаг 3: Добавляем обычную карточку (POST /cards/)
    logger.info(f"Создание обычной карточки для deck_id={deck_id}")
    card_response = client.post(
        "/cards/",
        json={"term": "Привет", "definition": "Приветствие", "deck_id": deck_id}
    )
    assert card_response.status_code == 200, f"Не удалось создать карточку: {card_response.text}"
    card_data = card_response.json()
    assert card_data["term"] == "Привет", f"Неправильный термин: {card_data['term']}"
    assert card_data["definition"] == "Приветствие", f"Неправильное определение: {card_data['definition']}"
    card_id = card_data["id"]
    logger.info(f"Карточка создана: id={card_id}, term={card_data['term']}")

    # Проверяем, что карточка сохранена в базе
    db_card = db_session.get(Card, card_id)
    assert db_card is not None, f"Карточка с id={card_id} не найдена в базе"
    assert db_card.term == "Привет"
    assert db_card.definition == "Приветствие"
    assert db_card.deck_id == deck_id
    logger.info(f"Карточка подтверждена в базе: id={db_card.id}, term={db_card.term}")

    # Шаг 4: Создаем языковую колоду (POST /decks/)
    logger.info("Создание языковой колоды через POST /decks/")
    lang_deck_response = client.post(
        "/decks/",
        json={
            "telegram_id": 123456789,
            "name": "Английский-Русский",
            "is_language_deck": True,
            "source_lang": "en",
            "target_lang": "ru"
        }
    )
    assert lang_deck_response.status_code == 200, f"Не удалось создать языковую колоду: {lang_deck_response.text}"
    lang_deck_data = lang_deck_response.json()
    logger.info(f"Ответ по языковой колоде: {lang_deck_data}")
    assert lang_deck_data["name"] == "Английский-Русский"
    assert lang_deck_data["is_language_deck"] is True
    assert lang_deck_data["source_lang"] == "en"
    assert lang_deck_data["target_lang"] == "ru"
    lang_deck_id = lang_deck_data.get("id")
    assert lang_deck_id is not None, f"ID языковой колоды отсутствует: {lang_deck_data}"
    logger.info(f"Языковая колода создана: id={lang_deck_id}, name={lang_deck_data['name']}")

    # Проверяем, что языковая колода сохранена в базе
    db_lang_deck = db_session.get(Deck, lang_deck_id)
    assert db_lang_deck is not None, f"Языковая колода с id={lang_deck_id} не найдена"
    assert db_lang_deck.is_language_deck is True
    assert db_lang_deck.source_lang == "en"
    assert db_lang_deck.target_lang == "ru"
    logger.info(f"Языковая колода подтверждена в базе: id={db_lang_deck.id}, name={db_lang_deck.name}")

    # Шаг 5: Ожидаем готовности сервиса перевода
    logger.info("Ожидание готовности сервиса перевода")
    assert await wait_for_translate_service(), "Сервис перевода не стал доступен"

    # Шаг 6: Добавляем языковую карточку с автопереводом (POST /lang_cards/)
    logger.info(f"Создание языковой карточки для deck_id={lang_deck_id}")
    lang_card_response = client.post(
        "/lang_cards/",
        json={
            "deck_id": lang_deck_id,
            "word": "Hello",
            "source_lang": "en",
            "target_lang": "ru",
            "translation": None  # Ожидаем автоперевод
        }
    )
    assert lang_card_response.status_code == 200, f"Не удалось создать языковую карточку: {lang_card_response.text}"
    lang_card_data = lang_card_response.json()
    assert lang_card_data["word"] == "Hello"
    assert lang_card_data["translation"] is not None, "Перевод не был выполнен"
    assert lang_card_data["translation"].lower() in ["привет", "здравствуйте"], f"Неправильный перевод: {lang_card_data['translation']}"
    lang_card_id = lang_card_data["id"]
    logger.info(f"Языковая карточка создана: id={lang_card_id}, word={lang_card_data['word']}, translation={lang_card_data['translation']}")

    # Проверяем, что языковая карточка сохранена в базе
    db_lang_card = db_session.get(LangCard, lang_card_id)
    assert db_lang_card is not None, f"Языковая карточка с id={lang_card_id} не найдена"
    assert db_lang_card.word == "Hello"
    assert db_lang_card.deck_id == lang_deck_id
    logger.info(f"Языковая карточка подтверждена в базе: id={db_lang_card.id}, word={db_lang_card.word}")

    # Шаг 7: Проверяем перевод слова отдельно (POST /translate)
    logger.info("Перевод слова 'Hello' с en на ru")
    translate_response = client.post(
        "/translate",
        json={"q": "Hello", "source": "en", "target": "ru", "format": "text"}
    )
    assert translate_response.status_code == 200, f"Не удалось выполнить перевод: {translate_response.text}"
    translate_data = translate_response.json()
    assert "translatedText" in translate_data, "Поле translatedText отсутствует в ответе"
    assert translate_data["translatedText"].lower() in ["привет", "здравствуйте"], f"Неправильный перевод: {translate_data['translatedText']}"
    logger.info(f"Перевод успешен: {translate_data['translatedText']}")

    # Шаг 8: Симулируем режим изучения — получение карточек обычной колоды (GET /cards/{deck_id})
    logger.info(f"Получение карточек для deck_id={deck_id} (режим изучения)")
    cards_response = client.get(f"/cards/{deck_id}")
    assert cards_response.status_code == 200, f"Не удалось получить карточки: {cards_response.text}"
    cards_data = cards_response.json()
    assert len(cards_data) == 1, f"Ожидалась 1 карточка, получено {len(cards_data)}"
    assert cards_data[0]["term"] == "Привет"
    assert cards_data[0]["definition"] == "Приветствие"
    assert cards_data[0]["deck_id"] == deck_id
    logger.info(f"Карточки для обычной колоды получены: {cards_data}")

    # Шаг 9: Симулируем режим изучения — получение языковых карточек (GET /lang_cards/{deck_id})
    logger.info(f"Получение языковых карточек для deck_id={lang_deck_id} (режим изучения)")
    lang_cards_response = client.get(f"/lang_cards/{lang_deck_id}")
    assert lang_cards_response.status_code == 200, f"Не удалось получить языковые карточки: {lang_cards_response.text}"
    lang_cards_data = lang_cards_response.json()
    assert len(lang_cards_data) == 1, f"Ожидалась 1 языковая карточка, получено {len(lang_cards_data)}"
    assert lang_cards_data[0]["word"] == "Hello"
    assert lang_cards_data[0]["translation"].lower() in ["привет", "здравствуйте"]
    assert lang_cards_data[0]["deck_id"] == lang_deck_id
    logger.info(f"Языковые карточки получены: {lang_cards_data}")

    # Шаг 10: Проверяем удаление карточек (DELETE /cards/{card_id}, DELETE /lang_cards/{card_id})
    logger.info(f"Удаление обычной карточки с id={card_id}")
    delete_card_response = client.delete(f"/cards/{card_id}")
    assert delete_card_response.status_code == 200, f"Не удалось удалить карточку: {delete_card_response.text}"
    assert delete_card_response.json() == {"message": "Card deleted successfully"}
    db_card = db_session.get(Card, card_id)
    assert db_card is None, f"Карточка с id={card_id} не была удалена из базы"
    logger.info(f"Обычная карточка удалена: id={card_id}")

    logger.info(f"Удаление языковой карточки с id={lang_card_id}")
    delete_lang_card_response = client.delete(f"/lang_cards/{lang_card_id}")
    assert delete_lang_card_response.status_code == 200, f"Не удалось удалить языковую карточку: {delete_lang_card_response.text}"
    assert delete_lang_card_response.json() == {"message": "Language card deleted successfully"}
    db_lang_card = db_session.get(LangCard, lang_card_id)
    assert db_lang_card is None, f"Языковая карточка с id={lang_card_id} не была удалена из базы"
    logger.info(f"Языковая карточка удалена: id={lang_card_id}")

    # Шаг 11: Проверяем удаление колоды (DELETE /decks/{deck_id})
    logger.info(f"Удаление обычной колоды с id={deck_id}")
    delete_deck_response = client.delete(f"/decks/{deck_id}")
    assert delete_deck_response.status_code == 200, f"Не удалось удалить колоду: {delete_deck_response.text}"
    assert delete_deck_response.json() == {"message": "Deck deleted successfully"}
    db_deck = db_session.get(Deck, deck_id)
    assert db_deck is None, f"Колода с id={deck_id} не была удалена из базы"
    logger.info(f"Обычная колода удалена: id={deck_id}")

    logger.info(f"Удаление языковой колоды с id={lang_deck_id}")
    delete_lang_deck_response = client.delete(f"/decks/{lang_deck_id}")
    assert delete_lang_deck_response.status_code == 200, f"Не удалось удалить языковую колоду: {delete_lang_deck_response.text}"
    assert delete_lang_deck_response.json() == {"message": "Deck deleted successfully"}
    db_lang_deck = db_session.get(Deck, lang_deck_id)
    assert db_lang_deck is None, f"Языковая колода с id={lang_deck_id} не была удалена из базы"
    logger.info(f"Языковая колода удалена: id={lang_deck_id}")

    # Шаг 12: Проверяем, что можно получить список языков (GET /languages/)
    logger.info("Получение списка доступных языков")
    languages_response = client.get("/languages/")
    assert languages_response.status_code == 200, f"Не удалось получить языки: {languages_response.text}"
    languages_data = languages_response.json()
    assert len(languages_data) > 0, "Список языков пуст"
    assert any(lang["code"] == "en" for lang in languages_data), "Английский язык отсутствует"
    assert any(lang["code"] == "ru" for lang in languages_data), "Русский язык отсутствует"
    logger.info(f"Список языков получен, найдено {len(languages_data)} языков")
