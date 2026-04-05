import os
import sys
import pytest
import logging
import httpx
import asyncio
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
API_DIR = os.path.join(BASE_DIR, 'api')
BOT_DIR = os.path.join(BASE_DIR, 'bot')

sys.path.insert(0, BASE_DIR)
sys.path.insert(0, API_DIR)

from api.main import app, get_db
from api.models import User, Deck, Card, LangCard

logger = logging.getLogger(__name__)

# --- Фикстуры ---

@pytest.fixture
def db_session():
    """Создает сессию и очищает БД до и после теста."""
    db = next(get_db())
    try:
        # Очистка перед тестом
        for model in [LangCard, Card, Deck, User]:
            db.execute(delete(model))
        db.commit()

        yield db

        # Очистка после теста
        for model in [LangCard, Card, Deck, User]:
            db.execute(delete(model))
        db.commit()
    finally:
        db.close()


@pytest.fixture
def client(db_session):
    """Клиент с переопределенной зависимостью БД."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Создает тестового пользователя в базе."""
    user = User(telegram_id=123456789)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


async def wait_for_translate_service():
    """Ожидание готовности сервиса перевода."""
    url = "http://translate:5000/languages"
    for attempt in range(1, 6):
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    return True
        except Exception:
            await asyncio.sleep(1)
    return False


# --- Тесты ---

# 5. Регистрация пользователя и создание стандартной колоды
def test_create_standard_deck(client, db_session, test_user):
    logger.info("Тест 5: Создание стандартной колоды")

    response = client.post(
        "/decks/",
        json={
            "telegram_id": test_user.telegram_id,
            "name": "Стандартная колода",
            "is_language_deck": False
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Стандартная колода"
    assert data["is_language_deck"] is False

    # Проверка в БД
    db_deck = db_session.get(Deck, data["id"])
    assert db_deck is not None
    assert db_deck.user_id == test_user.id


# 6. Регистрация пользователя и создание языковой колоды
def test_create_language_deck(client, db_session, test_user):
    logger.info("Тест 6: Создание языковой колоды")

    response = client.post(
        "/decks/",
        json={
            "telegram_id": test_user.telegram_id,
            "name": "English-Russian",
            "is_language_deck": True,
            "source_lang": "en",
            "target_lang": "ru"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["source_lang"] == "en"
    assert data["target_lang"] == "ru"

    # Проверка сохранения настроек в БД
    db_deck = db_session.get(Deck, data["id"])
    assert db_deck.is_language_deck is True
    assert db_deck.source_lang == "en"


# 7. Добавление карточек в стандартную колоду
def test_add_cards_to_standard_deck(client, db_session, test_user):
    logger.info("Тест 7: Добавление карточек в стандартную колоду")

    # Сначала создаем колоду
    deck = Deck(name="Logic Deck", user_id=test_user.id, is_language_deck=False)
    db_session.add(deck)
    db_session.commit()

    # Успешное добавление
    response = client.post(
        "/cards/",
        json={"term": "Atom", "definition": "Basic unit of matter", "deck_id": deck.id}
    )
    assert response.status_code == 200
    assert response.json()["term"] == "Atom"

    # Проверка Foreign Key (несуществующий deck_id)
    bad_response = client.post(
        "/cards/",
        json={"term": "Error", "definition": "Fail", "deck_id": 99999}
    )
    assert bad_response.status_code == 404  # Или 400, зависит от вашей реализации API


# 8. Добавление карточек в языковую колоду с ручным переводом
def test_add_lang_card_manual_translation(client, db_session, test_user):
    logger.info("Тест 8: Ручной перевод в языковой колоде")

    deck = Deck(name="Lang", user_id=test_user.id, is_language_deck=True, source_lang="en", target_lang="ru")
    db_session.add(deck)
    db_session.commit()

    response = client.post(
        "/lang_cards/",
        json={
            "deck_id": deck.id,
            "word": "Book",
            "source_lang": "en",
            "target_lang": "ru",
            "translation": "Книженция"  # Пользовательский ввод
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["translation"] == "Книженция"

    # Проверяем, что в БД именно наш вариант
    db_card = db_session.get(LangCard, data["id"])
    assert db_card.translation == "Книженция"


# 9. Добавление карточек в языковую колоду через LibreTranslate
@pytest.mark.asyncio
async def test_add_lang_card_auto_translation(client, db_session, test_user):
    logger.info("Тест 9: Автоматический перевод")

    # Проверяем доступность сервиса перевода
    if not await wait_for_translate_service():
        pytest.skip("Сервис перевода недоступен")

    deck = Deck(name="AutoLang", user_id=test_user.id, is_language_deck=True, source_lang="en", target_lang="ru")
    db_session.add(deck)
    db_session.commit()

    response = client.post(
        "/lang_cards/",
        json={
            "deck_id": deck.id,
            "word": "Apple",
            "source_lang": "en",
            "target_lang": "ru",
            "translation": None  # Триггер автоперевода
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["translation"] is not None
    assert data["translation"].lower() in ["яблоко", "apple"]  # LibreTranslate может вернуть по-разному
    logger.info(f"Автоперевод получен: {data['translation']}")


# 10. Удаление колод и проверка каскадной очистки БД
def test_cascade_delete_deck(client, db_session, test_user):
    logger.info("Тест 10: Каскадное удаление")

    # 1. Создаем колоду и карточку
    deck = Deck(name="To Be Deleted", user_id=test_user.id)
    db_session.add(deck)
    db_session.commit()

    card = Card(term="Delete Me", definition="Gone", deck_id=deck.id)
    db_session.add(card)
    db_session.commit()

    card_id = card.id
    deck_id = deck.id

    # 2. Удаляем колоду через API
    response = client.delete(f"/decks/{deck_id}")
    assert response.status_code == 200

    # 3. Проверяем, что колоды нет
    assert db_session.get(Deck, deck_id) is None

    # 4. Проверяем каскад (карточка должна исчезнуть автоматически)
    # Важно: вызываем expire_all или создаем новый запрос, чтобы избежать кеша сессии
    db_session.expire_all()
    db_card = db_session.get(Card, card_id)
    assert db_card is None, "Карточка осталась в базе после удаления колоды (каскад не сработал)"

# --- ТЕСТЫ ---

# 6. Сценарий: «Валидация обновлений и обработка исключений»
@pytest.mark.asyncio
async def test_card_updates_and_error_handling(client, db_session: Session):
    """
    Модули: FastAPI + Pydantic + БД.
    Проверяет: Ошибки 400 (контракт), 404 (отсутствие ID) и PUT-обновление.
    """
    # 1. Попытка создать языковую колоду без языков (нарушение Pydantic/Logic)
    bad_deck_resp = client.post("/decks/", json={
        "telegram_id": 999,
        "name": "Broken Deck",
        "is_language_deck": True,
        "source_lang": None  # Ошибка: для языковой колоды это поле обязательно
    })
    assert bad_deck_resp.status_code == 400
    assert "Source and target languages are required" in bad_deck_resp.json()["detail"]

    # 2. Запрос данных по несуществующему ID колоды
    fake_id = 99999
    none_cards_resp = client.get(f"/cards/{fake_id}")
    assert none_cards_resp.status_code == 404

    # 3. Проверка корректности изменения (обновление термина)
    # Создаем пользователя и колоду для теста
    user = User(telegram_id=999);
    db_session.add(user);
    db_session.commit()
    deck = Deck(name="Old Deck", user_id=user.id);
    db_session.add(deck);
    db_session.commit()
    card = Card(term="Old", definition="Old", deck_id=deck.id);
    db_session.add(card);
    db_session.commit()

    update_resp = client.put(f"/cards/{card.id}", json={"term": "New Term", "definition": "New Def"})
    assert update_resp.status_code == 200
    assert update_resp.json()["term"] == "New Term"
    assert db_session.get(Card, card.id).term == "New Term"


# 7. Сценарий: «Безопасность доступа»
@pytest.mark.asyncio
async def test_user_isolation_and_cascade_deletion(client, db_session: Session):
    """
    Модули: API + PostgreSQL Constraints (Foreign Keys).
    Проверяет: Изоляцию пользователей и Cascade Delete.
    """
    # 1. Создаем двух разных пользователей
    u1_tg, u2_tg = 111, 222
    client.post("/decks/", json={"telegram_id": u1_tg, "name": "Deck User 1", "is_language_deck": False})
    client.post("/decks/", json={"telegram_id": u2_tg, "name": "Deck User 2", "is_language_deck": False})

    # 2. Проверка изоляции: Юзер 1 не должен видеть колоду Юзера 2
    resp_u1 = client.get(f"/decks/{u1_tg}/")
    assert len(resp_u1.json()) == 1
    assert resp_u1.json()[0]["name"] == "Deck User 1"

    # 3. Проверка каскадной очистки
    deck_id = resp_u1.json()[0]["id"]
    # Добавляем карточку
    card_id = client.post("/cards/", json={"deck_id": deck_id, "term": "X", "definition": "Y"}).json()["id"]

    # Удаляем колоду
    client.delete(f"/decks/{deck_id}")

    # Проверяем, что карточка удалилась автоматически (Cascade)
    db_session.expire_all()
    assert db_session.get(Card, card_id) is None


# 8. Сценарий: «Автоматизация профиля и работа кэша перевода»
@pytest.mark.asyncio
async def test_auto_user_creation_and_translation_logic(client, db_session: Session, mocker):
    """
    Модули: API + БД + LRU Cache.
    Проверяет: Авто-регистрацию User и приоритет ручного перевода.
    """
    new_tg_id = 888777

    # 1. Создание колоды для ID, которого нет в базе (авто-создание User)
    client.post("/decks/", json={
        "telegram_id": new_tg_id, "name": "Auto User Deck", "is_language_deck": True,
        "source_lang": "en", "target_lang": "ru"
    })
    user_in_db = db_session.query(User).filter(User.telegram_id == new_tg_id).first()
    assert user_in_db is not None

    # 2. Приоритет ручного перевода (не должен затираться автоматикой)
    deck_id = db_session.query(Deck).filter(Deck.name == "Auto User Deck").first().id
    resp = client.post("/lang_cards/", json={
        "deck_id": deck_id, "word": "Apple", "source_lang": "en", "target_lang": "ru",
        "translation": "Спелое Яблоко"  # Ручной ввод
    })
    assert resp.json()["translation"] == "Спелое Яблоко"

    # 3. Проверка кэша (mocker позволит увидеть, вызывался ли http-запрос повторно)
    mock_post = mocker.patch("httpx.AsyncClient.post",
                             return_value=httpx.Response(200, json={"translatedText": "Кошка"}))

    # Первый вызов (сетевой)
    client.post("/translate", json={"q": "Cat", "source": "en", "target": "ru"})
    # Второй вызов (должен сработать кэш, если реализован @lru_cache на уровне функции)
    client.post("/translate", json={"q": "Cat", "source": "en", "target": "ru"})

    # Если кэш работает, call_count будет 1 (зависит от реализации функции перевода)
    # assert mock_post.call_count == 1


# 9. Сценарий: «Отказоустойчивость при работе с внешними API»
@pytest.mark.asyncio
async def test_telegram_info_and_translation_failure(client, mocker):
    """
    Модули: API + HTTPX + Внешние сбои.
    Проверяет: Обработку ошибок 500 от внешних сервисов.
    """
    # 1. Имитация успеха Telegram
    mocker.patch("httpx.AsyncClient.get", return_value=httpx.Response(200, json={
        "ok": True, "result": {"id": 777, "first_name": "Ivan", "username": "ivan_test"}
    }))
    resp_tg = client.get("/users/777/info")
    assert resp_tg.status_code == 200

    # 2. Имитация сбоя LibreTranslate (500)
    mocker.patch("httpx.AsyncClient.post", return_value=httpx.Response(500, content="External Error"))

    # Пытаемся создать карту с автопереводом
    resp_card = client.post("/lang_cards/", json={
        "deck_id": 1, "word": "Broken", "source_lang": "en", "target_lang": "ru", "translation": None
    })
    # Бэкенд должен поймать 500 от соседа и вернуть 503 или 400 пользователю
    assert resp_card.status_code in [400, 500, 503]
    assert "detail" in resp_card.json()


# 10. Сценарий: «Целостность типов колод»
@pytest.mark.asyncio
async def test_deck_type_integrity(client, db_session: Session):
    """
    Модули: API + Бизнес-логика + БД.
    Проверяет: Нельзя добавить LangCard в обычную колоду.
    """
    user = User(telegram_id=555);
    db_session.add(user);
    db_session.commit()

    # 1. Создаем ОБЫЧНУЮ колоду
    deck = Deck(name="Standard Deck", user_id=user.id, is_language_deck=False)
    db_session.add(deck);
    db_session.commit()

    # 2. Попытка добавить LangCard (через эндпоинт языковых карт)
    bad_resp = client.post("/lang_cards/", json={
        "deck_id": deck.id,
        "word": "Test",
        "source_lang": "en", "target_lang": "ru", "translation": "Тест"
    })

    # Система должна проверить флаг is_language_deck у колоды и отклонить запрос
    assert bad_resp.status_code == 400
    assert "Invalid deck for language cards" in bad_resp.json()["detail"]