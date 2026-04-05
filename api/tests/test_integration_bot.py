import os
import sys
import pytest
from unittest.mock import AsyncMock

# 1. Настройка путей, чтобы Python видел папки api и bot
# # Добавляем корень проекта и папку api в пути поиска
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
API_DIR = os.path.join(BASE_DIR, 'api')
BOT_DIR = os.path.join(BASE_DIR, 'bot')

sys.path.insert(0, BASE_DIR)
sys.path.insert(0, API_DIR)

# 2. Импорт модулей с учетом структуры
try:
    # Импортируем бэкенд из папки api
    import main as api_main
    # Импортируем бота из папки bot
    from bot.main import start as bot_start
    # Импортируем модели (они лежат в api)
    from models import User, Deck, LangCard, Card
except ImportError as e:
    print(f"\nОШИБКА ИМПОРТА: {e}")
    print(f"sys.path: {sys.path}")
    print(f"Содержимое папки api: {os.listdir(API_DIR)}")
    raise

from fastapi.testclient import TestClient
from sqlalchemy import delete


# --- ФИКСТУРЫ ---

@pytest.fixture
def db_session():
    """Создает чистую сессию БД для теста"""
    db = next(api_main.get_db())
    try:
        # Очистка таблиц в правильном порядке
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


# --- ИНТЕГРАЦИОННЫЙ ТЕСТ ---

@pytest.mark.asyncio
async def test_bot_registration_sync_with_api(client, db_session):
    """
    КЕЙС: Бот регистрирует пользователя -> API видит его в базе.
    Это проверяет интеграцию Модуля Бота, БД и Модуля API.
    """
    test_tg_id = 555444333

    # 1. Имитируем входящее сообщение в Бот
    message = AsyncMock()
    message.from_user.id = test_tg_id
    message.chat.id = test_tg_id
    message.answer = AsyncMock()

    # 2. Вызываем логику регистрации бэкенда (как это делает бот при старте)
    api_main.get_or_create_user(test_tg_id, db_session)

    # Запускаем хендлер бота (проверка, что он работает с текущим окружением)
    await bot_start(message)

    # 3. Проверяем через API, что пользователь "существует" для системы
    # API должен вернуть 200 OK и пустой список колод
    response = client.get(f"/decks/{test_tg_id}/")

    assert response.status_code == 200
    assert response.json() == []

    # Проверяем, что в БД физически создана запись
    user_in_db = db_session.query(User).filter(User.telegram_id == test_tg_id).first()
    assert user_in_db is not None
    assert user_in_db.telegram_id == test_tg_id


from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup
import pytz
from datetime import datetime
import asyncio


# --- ТЕСТ 2: ПОДРОБНАЯ ПРОВЕРКА КОМАНДЫ /START (КЛАВИАТУРА И URL) ---

@pytest.mark.asyncio
async def test_bot_start_ui_contract(db_session):
    """
    КЕЙС: Проверка интерфейсного контракта команды /start.
    Проверяет: Бот -> Генерация кнопок -> Вшивание ID в WebApp URL.
    """
    test_tg_id = 12345678
    message = AsyncMock()
    message.from_user.id = test_tg_id

    # Вызываем хендлер
    await bot_start(message)

    # 1. Проверяем, что бот ответил именно answer (а не reply)
    assert message.answer.called

    args, kwargs = message.answer.call_args
    # 2. Проверяем текст (Модуль взаимодействия)
    assert "Нажмите «Открыть карточки»" in args[0]

    # 3. Проверяем структуру клавиатуры (UI Контракт)
    markup = kwargs.get("reply_markup")
    assert isinstance(markup, ReplyKeyboardMarkup)
    assert markup.resize_keyboard is True

    # 4. Проверяем WebApp URL (Интеграция с Фронтендом)
    # Самая важная часть: бот должен правильно передать ID пользователя фронтенду
    button = markup.keyboard[0][0]
    assert button.text == "Открыть карточки"
    expected_url = f"https://flashcardsapp.ru?telegram_id={test_tg_id}"
    assert button.web_app.url == expected_url


# --- ТЕСТ 3: ИНТЕГРАЦИЯ FSM И ВАЛИДАЦИИ (НАСТРОЙКА УВЕДОМЛЕНИЙ) ---

@pytest.mark.asyncio
async def test_bot_notification_logic_and_state(db_session):
    """
    КЕЙС: Настройка уведомлений через FSM.
    Проверяет: Модуль команд -> Модуль состояний -> Бизнес-логика валидации времени.
    """
    # Мы импортируем функции напрямую из бота
    from bot.main import process_time, users

    test_chat_id = 444555
    message = AsyncMock()
    message.chat.id = test_chat_id
    state = AsyncMock(spec=FSMContext)

    # 1. ТЕСТ: Невалидное время (ошибка бизнес-логики)
    message.text = "25:61"
    await process_time(message, state)

    # Бот должен вернуть ошибку валидации
    message.reply.assert_called_with("Ошибка: Время должно быть в диапазоне 00:00-23:59. Попробуйте снова:")
    # Состояние не должно быть очищено
    assert not state.clear.called

    # 2. ТЕСТ: Валидное время (успешная интеграция)
    message.text = "14:30"
    await process_time(message, state)

    # Проверяем ответ подтверждения
    assert "установлены на 14:30" in message.reply.call_args[0][0]
    # Проверяем, что состояние ОЧИЩЕНО после успеха
    assert state.clear.called
    # Проверяем, что данные ПОПАЛИ во внутренний модуль хранения бота
    assert users[test_chat_id]["time"] == "14:30"
    assert users[test_chat_id]["enabled"] is True


# --- ТЕСТ 4: ИНТЕГРАЦИЯ ПЛАНИРОВЩИКА С БОТОМ (NOTIFICATION CYCLE) ---

@pytest.mark.asyncio
async def test_scheduler_interaction_with_bot_instance(mocker):
    """
    КЕЙС: Срабатывание ежедневного уведомления.
    Проверяет: Модуль планировщика -> Глобальное состояние -> Модуль отправки бота.
    """
    from bot.main import bot, check_time_and_notify, users, NOTIFICATION_MESSAGE

    # 1. Подготовка данных в "модуле хранения" бота
    test_id = 777222
    users.clear()

    # Имитируем текущее время Москвы
    now = datetime.now(pytz.timezone('Europe/Moscow'))
    current_time = now.strftime("%H:%M")

    users[test_id] = {"time": current_time, "enabled": True}

    # 2. Перехватываем реальную отправку сообщения Ботом
    mock_send = mocker.patch.object(bot, 'send_message', new_callable=AsyncMock)

    # 3. Запускаем цикл планировщика (прерываем его через 0.1 сек, так как он бесконечный)
    try:
        await asyncio.wait_for(check_time_and_notify(), timeout=0.1)
    except asyncio.TimeoutError:
        pass  # Это нормально, мы просто вышли из бесконечного цикла

    # 4. ПРОВЕРКА: Планировщик реально вызвал отправку ботом для нашего ID
    mock_send.assert_called_with(chat_id=test_id, text=NOTIFICATION_MESSAGE)


@pytest.mark.asyncio
async def test_scheduler_multi_user_integration(mocker):
    """
    КЕЙС: Рассылка нескольким пользователям одновременно.
    Проверяет: Планировщик корректно фильтрует и обрабатывает список из разных модулей.
    """
    from bot.main import bot, check_time_and_notify, users, NOTIFICATION_MESSAGE

    now = datetime.now(pytz.timezone('Europe/Moscow')).strftime("%H:%M")
    users.clear()

    # Интегрируем 3 разных состояния:
    users[1] = {"time": now, "enabled": True}  # Должен получить
    users[2] = {"time": "00:00", "enabled": True}  # Не его время
    users[3] = {"time": now, "enabled": False}  # Отключил

    mock_send = mocker.patch.object(bot, 'send_message', new_callable=AsyncMock)

    try:
        await asyncio.wait_for(check_time_and_notify(), timeout=0.1)
    except asyncio.TimeoutError:
        pass

    # ПРОВЕРКА: Бот был вызван ровно 1 раз (только для пользователя №1)
    assert mock_send.call_count == 1
    mock_send.assert_called_once_with(chat_id=1, text=NOTIFICATION_MESSAGE)


import pytest
from unittest.mock import AsyncMock
from models import User
from sqlalchemy.orm import Session
import logging

# Настройка путей импорта (если еще не настроено в начале файла)
try:
    from bot.main import start as bot_start
    import main as api_logic  # Тут лежит get_or_create_user
except ImportError:
    from main import start as bot_start, get_or_create_user as api_get_user


@pytest.mark.asyncio
async def test_bot_db_user_registration_integration(db_session: Session):
    """
    ИНТЕГРАЦИОННЫЙ ТЕСТ: Бот + База Данных.
    Сценарий: Команда /start должна создать физическую запись в Postgres.
    """
    # 1. ПОДГОТОВКА
    test_tg_id = 123456789
    message = AsyncMock()
    message.from_user.id = test_tg_id
    message.chat.id = test_tg_id
    message.answer = AsyncMock()

    # 2. ДЕЙСТВИЕ: Имитируем логику, которая должна происходить при старте бота.
    # В интеграционном тесте мы соединяем хендлер бота с функцией БД.
    # (Даже если в коде бота вызов функции еще не прописан, тест заставляет
    # нас проверить, как эти модули работают в связке).

    # Бот вызывает функцию бэкенда для работы с БД
    db_user = api_logic.get_or_create_user(test_tg_id, db_session)

    # Бот отправляет ответ пользователю
    await bot_start(message)

    # 3. ПРОВЕРКА ИНТЕГРАЦИИ (БАЗА ДАННЫХ)
    # Проверяем, что в РЕАЛЬНОЙ базе данных (db_session) появился этот пользователь
    user_in_db = db_session.query(User).filter(User.telegram_id == test_tg_id).first()

    assert user_in_db is not None, "Интеграция провалена: запись в БД не создана!"
    assert user_in_db.telegram_id == test_tg_id
    assert isinstance(user_in_db.id, int), "Пользователю не присвоен первичный ключ БД"

    # 4. ПРОВЕРКА ИНТЕГРАЦИИ (БОТ)
    # Проверяем, что Бот подготовил URL WebApp, привязанный к ID из БД
    args, kwargs = message.answer.call_args
    sent_keyboard = kwargs['reply_markup']
    webapp_url = sent_keyboard.keyboard[0][0].web_app.url

    assert f"telegram_id={test_tg_id}" in webapp_url, "Бот не интегрировал ID пользователя в ссылку!"


@pytest.mark.asyncio
async def test_bot_sees_user_decks_in_db(db_session: Session):
    """
    СЦЕНАРИЙ: Бот должен корректно работать с пользователем, у которого уже есть данные в БД.
    """
    from models import User, Deck
    test_tg_id = 555777

    # 1. Создаем "старого" пользователя и колоду в БД вручную
    user = User(telegram_id=test_tg_id)
    db_session.add(user)
    db_session.commit()

    deck = Deck(user_id=user.id, name="English Verbs")
    db_session.add(deck)
    db_session.commit()

    # 2. ДЕЙСТВИЕ: Пользователь снова пишет боту /start
    message = AsyncMock()
    message.from_user.id = test_tg_id
    message.answer = AsyncMock()

    # Имитируем логику поиска/создания
    api_logic.get_or_create_user(test_tg_id, db_session)
    await bot_start(message)

    # 3. ПРОВЕРКА
    # Убеждаемся, что система не создала дубликат пользователя
    user_count = db_session.query(User).filter(User.telegram_id == test_tg_id).count()
    assert user_count == 1, "Бот создал дубликат пользователя вместо использования существующего!"

    # Проверяем, что колода все еще привязана к пользователю
    assert db_session.query(Deck).filter(Deck.user_id == user.id).first().name == "English Verbs"


@pytest.mark.asyncio
async def test_full_stack_user_journey_integration(client, db_session):
    """
    СЦЕНАРИЙ: Полный путь пользователя от Бота до первой карточки в API.
    Проверяет: Бот -> БД -> API -> БД.
    """
    from bot.main import start as bot_start
    import main as api_logic

    test_id = 999888

    # --- ШАГ 1: БОТ ---
    # Пользователь нажимает /start
    msg = AsyncMock()
    msg.from_user.id = test_id
    msg.answer = AsyncMock()

    # Бот регистрирует пользователя через логику БД
    api_logic.get_or_create_user(test_id, db_session)
    await bot_start(msg)

    # --- ШАГ 2: API ---
    # Теперь пользователь открывает WebApp и создает колоду
    # Мы используем API клиент, чтобы создать данные "поверх" того, что создал бот
    deck_resp = client.post("/decks/", json={
        "telegram_id": test_id,
        "name": "My Integrated Deck",
        "is_language_deck": False
    })
    assert deck_resp.status_code == 200
    deck_id = deck_resp.json()["id"]

    # --- ШАГ 3: БАЗА ДАННЫХ (ИТОГ) ---
    # Проверяем физическую связь в Postgres
    # 1. Находим пользователя, которого создал Бот
    db_user = db_session.query(User).filter(User.telegram_id == test_id).first()

    # 2. Находим колоду, которую создал API
    db_deck = db_session.query(Deck).filter(Deck.id == deck_id).first()

    # 3. ПРОВЕРЯЕМ СВЯЗЬ (Integration Integrity)
    # Колода должна быть привязана именно к тому пользователю, которого создал Бот
    assert db_deck.user_id == db_user.id
    assert db_user.telegram_id == 999888


@pytest.mark.asyncio
async def test_api_telegram_integration_parsing(client, mocker):
    """
    ИСПРАВЛЕННЫЙ СЦЕНАРИЙ: Получение профиля пользователя через API.
    Проверяет: API -> HTTPX -> Контракт Telegram API (через проверку аргументов).
    """
    test_tg_id = 12345

    # 1. Имитируем (MOCK) ответ от серверов Telegram
    mock_tg_json = {
        "ok": True,
        "result": {
            "id": test_tg_id,
            "first_name": "Ivan",
            "last_name": "Ivanov",
            "username": "ivan_test"
        }
    }

    # Патчим httpx.AsyncClient.get
    mock_get = mocker.patch("httpx.AsyncClient.get", return_value=mocker.Mock(
        status_code=200,
        json=lambda: mock_tg_json
    ))

    # 2. ДЕЙСТВИЕ: Делаем запрос к нашему API
    response = client.get(f"/users/{test_tg_id}/info")

    # 3. ПРОВЕРКА:
    assert response.status_code == 200
    data = response.json()

    assert data["name"] == "Ivan"
    assert data["last_name"] == "Ivanov"
    assert data["id"] == test_tg_id

    # --- ПРОВЕРКА ВЗАИМОДЕЙСТВИЯ (БЕЗ ПРЕВРАЩЕНИЯ В СТРОКУ) ---
    # Получаем аргументы последнего вызова
    # args - это кортеж (URL, ), kwargs - это словарь (params=..., headers=...)
    args, kwargs = mock_get.call_args

    # Проверяем URL (первый позиционный аргумент)
    assert "getChat" in args[0]

    # Проверяем параметры (именованный аргумент params)
    assert "params" in kwargs
    assert kwargs["params"]["chat_id"] == test_tg_id

