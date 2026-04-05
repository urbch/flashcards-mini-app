import os
import sys
import pytest
from unittest.mock import AsyncMock
from sqlalchemy import delete
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from aiogram.types import ReplyKeyboardMarkup

# --- НАСТРОЙКА ПУТЕЙ ---
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
API_DIR = os.path.join(BASE_DIR, 'api')
BOT_DIR = os.path.join(BASE_DIR, 'bot')

sys.path.insert(0, BASE_DIR)
sys.path.insert(0, API_DIR)

import api.main as api_main
from bot.main import start as bot_start
from api.models import User, Deck, LangCard, Card

# --- ФИКСТУРЫ ---

@pytest.fixture
def db_session():
    """Создает чистую сессию БД для теста"""
    db = next(api_main.get_db())
    try:
        # Очистка таблиц перед тестом
        db.execute(delete(LangCard))
        db.execute(delete(Card))
        db.execute(delete(Deck))
        db.execute(delete(User))
        db.commit()
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session):
    """Создает тестовый клиент FastAPI"""

    def override_get_db():
        yield db_session

    api_main.app.dependency_overrides[api_main.get_db] = override_get_db
    with TestClient(api_main.app) as c:
        yield c
    api_main.app.dependency_overrides.clear()


# --- ТЕСТЫ ---

# 1. Интерфейсный контракт команды /start
@pytest.mark.asyncio
async def test_bot_start_ui_contract():
    """
    Проверяет: Бот -> Генерация кнопок -> Вшивание ID в WebApp URL.
    Результат: Корректное формирование WebAppInfo с telegram_id.
    """
    test_tg_id = 12345678
    message = AsyncMock()
    message.from_user.id = test_tg_id

    await bot_start(message)

    # Проверка вызова ответа
    assert message.answer.called
    args, kwargs = message.answer.call_args

    # Проверка структуры клавиатуры
    markup = kwargs.get("reply_markup")
    assert isinstance(markup, ReplyKeyboardMarkup)

    # Проверка URL (в него должен быть вшит telegram_id)
    button = markup.keyboard[0][0]
    assert button.text == "Открыть карточки"
    assert f"telegram_id={test_tg_id}" in button.web_app.url


# 2. Физическая регистрация пользователя в БД
@pytest.mark.asyncio
async def test_bot_db_user_registration_integration(db_session: Session):
    """
    Проверяет: Бот Логика -> SQLAlchemy -> PostgreSQL.
    Результат: Создание записи в таблице users при старте.
    """
    test_tg_id = 999111222

    # Имитируем логику, которую вызывает бот для регистрации
    api_main.get_or_create_user(test_tg_id, db_session)

    # Проверяем физическое наличие в БД
    user_in_db = db_session.query(User).filter(User.telegram_id == test_tg_id).first()
    assert user_in_db is not None
    assert user_in_db.telegram_id == test_tg_id
    assert isinstance(user_in_db.id, int)


# 3. Идентификация существующего пользователя
@pytest.mark.asyncio
async def test_bot_sees_user_decks_in_db(db_session: Session):
    """
    Проверяет: Database -> Identity Logic (get_or_create).
    Результат: Отсутствие дубликатов и сохранение связей с колодами.
    """
    test_tg_id = 555777

    # Создаем пользователя и колоду заранее
    user = User(telegram_id=test_tg_id)
    db_session.add(user)
    db_session.commit()

    deck = Deck(user_id=user.id, name="Existing Deck")
    db_session.add(deck)
    db_session.commit()

    # Повторный вызов логики (как при повторном /start)
    api_main.get_or_create_user(test_tg_id, db_session)

    # Проверяем, что дубликат не создан
    user_count = db_session.query(User).filter(User.telegram_id == test_tg_id).count()
    assert user_count == 1

    # Проверяем, что связь с колодой сохранена
    db_deck = db_session.query(Deck).filter(Deck.user_id == user.id).first()
    assert db_deck.name == "Existing Deck"


# 4. Интеграция с внешним Telegram API (Profile Parsing)
@pytest.mark.asyncio
async def test_api_telegram_integration_parsing(client, mocker):
    """
    Проверяет: FastAPI -> HTTPX -> Telegram API Servers.
    Результат: Корректный парсинг JSON от Telegram в модель пользователя.
    """
    test_tg_id = 12345
    mock_tg_json = {
        "ok": True,
        "result": {
            "id": test_tg_id,
            "first_name": "Ivan",
            "last_name": "Ivanov",
            "username": "ivan_test"
        }
    }

    # Мокаем внешний запрос к Telegram API
    mock_get = mocker.patch("httpx.AsyncClient.get", return_value=mocker.Mock(
        status_code=200,
        json=lambda: mock_tg_json
    ))

    # Вызываем API метод бэкенда
    response = client.get(f"/users/{test_tg_id}/info")

    assert response.status_code == 200
    data = response.json()

    # Проверяем парсинг данных
    assert data["name"] == "Ivan"
    assert data["last_name"] == "Ivanov"

    # Проверяем, что запрос ушел на правильный метод Telegram
    args, kwargs = mock_get.call_args
    assert "getChat" in args[0]
    assert kwargs["params"]["chat_id"] == test_tg_id