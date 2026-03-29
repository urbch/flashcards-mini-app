import os
import sys
import pytest
from unittest.mock import AsyncMock

# Настройка путей, чтобы тест видел модули внутри папки api
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE_DIR)

# Теперь импортируем из корня папки api
try:
    from main import app, get_db
    from models import User, Deck, Card, LangCard
except ImportError:
    # Запасной вариант для разных сред запуска
    from api.main import app, get_db
    from api.models import User, Deck, Card, LangCard

from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.orm import Session
import httpx
import asyncio
import logging


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
logger = logging.getLogger(__name__)

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


@pytest.mark.asyncio
async def test_card_updates_and_error_handling(client, db_session: Session):
    """
    Тест на проверку обновления данных и обработки граничных случаев:
    - Обновление обычной карточки
    - Обновление языковой карточки
    - Ошибка при создании языковой колоды без языков
    - Ошибка 404 при запросе несуществующей колоды
    """
    # 1. Подготовка: Создаем пользователя и колоду
    user = User(telegram_id=999)
    db_session.add(user)
    db_session.commit()

    deck_resp = client.post("/decks/", json={
        "telegram_id": 999,
        "name": "Original Name",
        "is_language_deck": False
    })
    deck_id = deck_resp.json()["id"]

    # --- ЧАСТЬ 1: ОБНОВЛЕНИЕ КАРТОЧЕК ---

    # Создаем обычную карточку
    card_resp = client.post("/cards/", json={
        "deck_id": deck_id,
        "term": "Old Term",
        "definition": "Old Definition"
    })
    card_id = card_resp.json()["id"]

    # Обновляем карточку (PUT /cards/{card_id})
    logger.info(f"Обновление карточки id={card_id}")
    update_resp = client.put(f"/cards/{card_id}", json={
        "term": "New Term",
        "definition": "New Definition"
    })
    assert update_resp.status_code == 200
    updated_data = update_resp.json()
    assert updated_data["term"] == "New Term"
    assert updated_data["definition"] == "New Definition"

    # Проверяем в БД
    db_card = db_session.get(Card, card_id)
    assert db_card.term == "New Term"
    logger.info("Карточка успешно обновлена в базе")

    # --- ЧАСТЬ 2: ВАЛИДАЦИЯ И ОШИБКИ БИЗНЕС-ЛОГИКИ ---

    # Попытка создать языковую колоду без указания языков (должна быть ошибка 400)
    logger.info("Тест: Создание языковой колоды без языков")
    bad_deck_resp = client.post("/decks/", json={
        "telegram_id": 999,
        "name": "Broken Deck",
        "is_language_deck": True,
        "source_lang": None  # Ошибка тут
    })
    assert bad_deck_resp.status_code == 400
    assert "Source and target languages are required" in bad_deck_resp.json()["detail"]
    logger.info("Сервер корректно отклонил запрос без языков")

    # Попытка получить карточки для несуществующей колоды
    logger.info("Тест: Запрос карточек несуществующей колоды")
    fake_deck_id = 99999
    none_cards_resp = client.get(f"/cards/{fake_deck_id}")
    assert none_cards_resp.status_code == 404
    logger.info("Сервер корректно вернул 404")

    # --- ЧАСТЬ 3: ЯЗЫКОВЫЕ КАРТОЧКИ (ОБНОВЛЕНИЕ) ---

    # Создаем языковую колоду
    lang_deck_resp = client.post("/decks/", json={
        "telegram_id": 999,
        "name": "Lang",
        "is_language_deck": True,
        "source_lang": "en",
        "target_lang": "ru"
    })
    l_deck_id = lang_deck_resp.json()["id"]

    # Создаем языковую карточку (с ручным переводом)
    l_card_resp = client.post("/lang_cards/", json={
        "deck_id": l_deck_id,
        "word": "Tree",
        "source_lang": "en",
        "target_lang": "ru",
        "translation": "Дерево"
    })
    l_card_id = l_card_resp.json()["id"]

    # Обновляем перевод (PUT /lang_cards/{card_id})
    logger.info(f"Обновление языковой карточки id={l_card_id}")
    l_update_resp = client.put(f"/lang_cards/{l_card_id}", json={
        "word": "Tree",
        "translation": "Древо (устар.)"
    })
    assert l_update_resp.status_code == 200
    assert l_update_resp.json()["translation"] == "Древо (устар.)"
    logger.info("Языковая карточка успешно обновлена")


@pytest.mark.asyncio
async def test_user_isolation_and_cascade_deletion(client, db_session: Session):
    """
    Тест на проверку безопасности и целостности данных:
    1. Проверка, что пользователи видят только свои колоды.
    2. Проверка, что при удалении колоды удаляются все её карточки.
    """

    # --- ШАГ 1: СОЗДАЕМ ДВУХ РАЗНЫХ ПОЛЬЗОВАТЕЛЕЙ ---
    user1_id = 111
    user2_id = 222

    # Создаем колоду для Пользователя 1
    client.post("/decks/", json={
        "telegram_id": user1_id,
        "name": "Колода Первого",
        "is_language_deck": False
    })

    # Создаем колоду для Пользователя 2
    client.post("/decks/", json={
        "telegram_id": user2_id,
        "name": "Колода Второго",
        "is_language_deck": False
    })

    # --- ШАГ 2: ПРОВЕРЯЕМ ИЗОЛЯЦИЮ (SECURITY CHECK) ---
    logger.info("Проверка изоляции: Пользователь 1 не должен видеть колоду Пользователя 2")

    resp_user1 = client.get(f"/decks/{user1_id}/")
    decks_user1 = resp_user1.json()
    assert len(decks_user1) == 1
    assert decks_user1[0]["name"] == "Колода Первого"

    resp_user2 = client.get(f"/decks/{user2_id}/")
    decks_user2 = resp_user2.json()
    assert len(decks_user2) == 1
    assert decks_user2[0]["name"] == "Колода Второго"
    logger.info("Изоляция подтверждена: каждый видит только своё")

    # --- ШАГ 3: ПОДГОТОВКА К КАСКАДНОМУ УДАЛЕНИЮ ---
    # Создаем языковую колоду для Пользователя 1
    lang_deck_resp = client.post("/decks/", json={
        "telegram_id": user1_id,
        "name": "Языковая для удаления",
        "is_language_deck": True,
        "source_lang": "en",
        "target_lang": "ru"
    })
    lang_deck_id = lang_deck_resp.json()["id"]

    # Добавляем карточку в эту колоду
    # ВНИМАНИЕ: Здесь добавлены source_lang и target_lang, чтобы пройти валидацию Pydantic
    card_resp = client.post("/lang_cards/", json={
        "deck_id": lang_deck_id,
        "word": "DeleteMe",
        "source_lang": "en",
        "target_lang": "ru",
        "translation": "УдалиМеня"
    })

    # Добавим проверку статуса, чтобы не получать KeyError, если API вернет ошибку
    assert card_resp.status_code == 200, f"Ошибка создания карточки: {card_resp.text}"

    card_data = card_resp.json()
    card_id = card_data["id"]

    # Проверяем, что карточка создалась в базе
    assert db_session.get(LangCard, card_id) is not None

    # --- ШАГ 4: УДАЛЯЕМ КОЛОДУ И ПРОВЕРЯЕМ КАСКАД ---
    logger.info(f"Удаление колоды id={lang_deck_id} и проверка удаления связанных карточек")

    delete_resp = client.delete(f"/decks/{lang_deck_id}")
    assert delete_resp.status_code == 200

    # Проверяем: колоды нет
    assert db_session.get(Deck, lang_deck_id) is None

    # Проверяем каскадное удаление
    db_card = db_session.get(LangCard, card_id)
    assert db_card is None, "ОШИБКА: Карточка осталась в базе после удаления колоды!"

    logger.info("Каскадное удаление работает корректно")


@pytest.mark.asyncio
async def test_auto_user_creation_and_translation_logic(client, db_session: Session):
    """
    Тест проверяет:
    1. Автоматическое создание записи пользователя при создании первой колоды.
    2. Приоритет ручного перевода над автоматическим в языковых карточках.
    3. Корректную работу автоперевода, если ручной перевод не указан.
    """
    new_telegram_id = 888777666

    # --- ШАГ 1: ПРОВЕРЯЕМ АВТО-СОЗДАНИЕ ПОЛЬЗОВАТЕЛЯ ---
    logger.info(f"Создаем колоду для нового пользователя {new_telegram_id}")

    # Сначала убедимся, что такого пользователя нет в базе
    user_in_db = db_session.query(User).filter(User.telegram_id == new_telegram_id).first()
    assert user_in_db is None

    # Создаем колоду. Бэкенд должен сам создать пользователя в этот момент.
    deck_resp = client.post("/decks/", json={
        "telegram_id": new_telegram_id,
        "name": "Авто-юзер колода",
        "is_language_deck": True,
        "source_lang": "en",
        "target_lang": "ru"
    })
    assert deck_resp.status_code == 200
    deck_id = deck_resp.json()["id"]

    # Теперь проверяем базу: пользователь должен был появиться
    user_in_db = db_session.query(User).filter(User.telegram_id == new_telegram_id).first()
    assert user_in_db is not None
    logger.info(f"Пользователь {new_telegram_id} был автоматически создан")

    # --- ШАГ 2: ПРОВЕРЯЕМ ПРИОРИТЕТ РУЧНОГО ПЕРЕВОДА ---
    logger.info("Тест: Ручной перевод не должен заменяться автоматическим")

    manual_word = "Apple"
    manual_trans = "Яблочко (мое любимое)"  # Специально не просто "Яблоко"

    resp_manual = client.post("/lang_cards/", json={
        "deck_id": deck_id,
        "word": manual_word,
        "source_lang": "en",
        "target_lang": "ru",
        "translation": manual_trans  # Передаем свой вариант
    })

    assert resp_manual.status_code == 200
    assert resp_manual.json()["translation"] == manual_trans
    logger.info("Ручной перевод успешно сохранен без вмешательства LibreTranslate")

    # --- ШАГ 3: ПРОВЕРЯЕМ АВТОМАТИЧЕСКИЙ ПЕРЕВОД (КОГДА ПУСТО) ---
    logger.info("Тест: Автоперевод должен сработать, если translation=None")

    # Ожидаем готовности сервиса
    assert await wait_for_translate_service()

    resp_auto = client.post("/lang_cards/", json={
        "deck_id": deck_id,
        "word": "Cat",
        "source_lang": "en",
        "target_lang": "ru",
        "translation": None  # Оставляем пустым для автоперевода
    })

    assert resp_auto.status_code == 200
    auto_data = resp_auto.json()
    assert auto_data["word"] == "Cat"
    assert auto_data["translation"].lower() == "кошка"
    logger.info(f"Автоперевод сработал корректно: Cat -> {auto_data['translation']}")

    # --- ШАГ 4: ПОВТОРНЫЙ ЗАПРОС ПРОВЕРКИ КЭША ---
    # В коде есть @lru_cache на функцию перевода. Проверим, что повторный перевод не ломает логику.
    resp_cached = client.post("/translate", json={
        "q": "Cat",
        "source": "en",
        "target": "ru"
    })
    assert resp_cached.status_code == 200
    assert resp_cached.json()["translatedText"].lower() == "кошка"
    logger.info("Повторный перевод (кэш) отработал успешно")


from unittest.mock import AsyncMock, patch
import pytest
from models import User
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)



import respx
import pytest
import respx
from httpx import Response
from main import app, get_db
from models import User, Deck, Card, LangCard
from fastapi.testclient import TestClient
import os

# Мокаем токен бота для тестов
os.environ["BOT_TOKEN"] = "12345:fake_token"


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


import pytest
import httpx
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_telegram_info_and_translation_failure(client, db_session, mocker):
    """
    Тест через mocker.patch: подменяем методы httpx напрямую.
    Никаких регулярных выражений, только логика.
    """
    telegram_id = 777

    # --- ШАГ 1: МОКАЕМ ТЕЛЕГРАМ ---
    # Мы подменяем метод 'get' у AsyncClient.
    # Теперь любой вызов client.get() внутри бэкенда вернет этот JSON.
    mock_tg_response = httpx.Response(200, json={
        "ok": True,
        "result": {
            "id": telegram_id,
            "first_name": "Ivan",
            "username": "ivan_test"
        }
    })

    # Патчим метод get в библиотеке httpx
    mocker.patch("httpx.AsyncClient.get", return_value=mock_tg_response)

    # Вызываем эндпоинт получения информации о пользователе
    response = client.get(f"/users/{telegram_id}/info")
    assert response.status_code == 200
    assert response.json()["name"] == "Ivan"

    # --- ШАГ 2: МОКАЕМ ОШИБКУ ТРАНСЛЕЙТА ---
    # Создаем колоду (это обычный запрос к БД, патч httpx на него не влияет)
    deck_resp = client.post("/decks/", json={
        "telegram_id": telegram_id,
        "name": "Error Deck",
        "is_language_deck": True,
        "source_lang": "en",
        "target_lang": "ru"
    })
    deck_id = deck_resp.json()["id"]

    # Теперь подменяем метод 'post' у AsyncClient, чтобы имитировать ошибку 500
    mock_err_response = httpx.Response(500, content="Internal Server Error")
    mocker.patch("httpx.AsyncClient.post", return_value=mock_err_response)

    # Пытаемся создать карточку (бэкенд внутри вызовет client.post к транслейту и получит 500)
    lang_card_resp = client.post("/lang_cards/", json={
        "deck_id": deck_id,
        "word": "Broken",
        "source_lang": "en",
        "target_lang": "ru",
        "translation": None
    })

    # Проверяем результат
    assert lang_card_resp.status_code in [400, 500, 503]
    # Проверяем наличие сообщения об ошибке
    assert "detail" in lang_card_resp.json()

@pytest.mark.asyncio
async def test_deck_type_integrity(client, db_session):
    """
    Тест проверяет бизнес-логику разделения типов колод:
    - Нельзя добавить LangCard в обычную колоду (API должен это пресекать).
    - Обычная карточка в языковой колоде (проверка консистентности).
    """
    telegram_id = 555

    # 1. Создаем ОБЫЧНУЮ колоду
    standard_deck = client.post("/decks/", json={
        "telegram_id": telegram_id,
        "name": "Simple Deck",
        "is_language_deck": False
    }).json()

    # 2. Пытаемся добавить в нее ЯЗЫКОВУЮ карточку через /lang_cards/
    # Это должно вызвать ошибку, так как колода не помечена как is_language_deck
    bad_card_resp = client.post("/lang_cards/", json={
        "deck_id": standard_deck["id"],
        "word": "Test",
        "source_lang": "en",
        "target_lang": "ru",
        "translation": "Тест"
    })

    assert bad_card_resp.status_code == 400
    assert "Invalid deck for language cards" in bad_card_resp.json()["detail"]


@pytest.mark.asyncio
async def test_complex_user_onboarding_and_translation_error(client, db_session, mocker):
    """
    СЦЕНАРИЙ: Успешный вход через Telegram -> Создание колоды -> Сбой перевода.
    Проверяет интеграцию: Telegram API + DB + Translation API.
    """
    tel_id = 999
    # 1. Мокаем успешный Telegram (Модуль интеграции со сторонним сервисом)
    mocker.patch("httpx.AsyncClient.get", return_value=httpx.Response(200, json={
        "ok": True, "result": {"id": tel_id, "first_name": "IntegrationTester"}
    }))

    # 2. Пользователь "входит" в приложение (создается в БД)
    client.get(f"/users/{tel_id}/info")

    # 3. Создаем колоду (Модуль взаимодействия с БД)
    deck_resp = client.post("/decks/", json={
        "telegram_id": tel_id, "name": "FailDeck", "is_language_deck": True,
        "source_lang": "en", "target_lang": "ru"
    })
    deck_id = deck_resp.json()["id"]

    # 4. Мокаем ПАДЕНИЕ транслятора (Модуль интеграции с внешним сервисом №2)
    mocker.patch("httpx.AsyncClient.post", return_value=httpx.Response(500))

    # 5. Пытаемся добавить карточку
    card_resp = client.post("/lang_cards/", json={
        "deck_id": deck_id, "word": "Error", "source_lang": "en",
        "target_lang": "ru", "translation": None
    })

    assert card_resp.status_code in [400, 500, 503]
    # Проверяем, что в БД пользователь и колода ОСТАЛИСЬ (целостность данных)
    assert db_session.query(User).filter(User.telegram_id == tel_id).first() is not None
    assert db_session.query(Deck).filter(Deck.id == deck_id).first() is not None


from unittest.mock import AsyncMock, patch
import pytest
from models import User
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


import pytest
import httpx
from models import User, Deck, LangCard
from sqlalchemy.orm import Session
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_language_study_session_preparation_flow(client, db_session: Session, mocker):
    """
    СЦЕНАРИЙ: Подготовка материалов для изучения.
    Проверяет интеграцию: API -> Логика перевода -> База данных -> Выдача для фронтенда.
    """
    test_id = 123000

    # --- ШАГ 1: Подготовка (Настройка правильного мока) ---
    # Создаем фиктивный запрос, чтобы .raise_for_status() не падал
    fake_request = httpx.Request("POST", "http://translate:5000/translate")

    mock_resp = httpx.Response(
        200,
        json={"translatedText": "Авто-перевод"},
        request=fake_request  # КРИТИЧЕСКИ ВАЖНО для httpx моков
    )

    # Патчим post запрос
    mock_post = mocker.patch("httpx.AsyncClient.post", return_value=mock_resp)

    # Создаем колоду (Модуль API + БД)
    deck_resp = client.post("/decks/", json={
        "telegram_id": test_id,
        "name": "Интеграционный Английский",
        "is_language_deck": True,
        "source_lang": "en",
        "target_lang": "ru"
    })
    assert deck_resp.status_code == 200
    deck_id = deck_resp.json()["id"]

    # --- ШАГ 2: Добавление карточек ---

    # 1. С автоматическим переводом (Интеграция API -> Translation Logic -> DB)
    resp_auto = client.post("/lang_cards/", json={
        "deck_id": deck_id,
        "word": "Automatic",
        "source_lang": "en",
        "target_lang": "ru",
        "translation": None
    })
    assert resp_auto.status_code == 200, f"Ошибка авто-карточки: {resp_auto.text}"

    # 2. С ручным переводом (Проверка приоритета логики)
    manual_translation = "Мой личный вариант"
    resp_manual = client.post("/lang_cards/", json={
        "deck_id": deck_id,
        "word": "Manual",
        "source_lang": "en",
        "target_lang": "ru",
        "translation": manual_translation
    })
    assert resp_manual.status_code == 200

    # --- ШАГ 3: Запрос данных для изучения (Имитация входа в Study Mode) ---
    study_resp = client.get(f"/lang_cards/{deck_id}")
    assert study_resp.status_code == 200
    cards = study_resp.json()

    # --- ШАГ 4: Проверка интеграционных связей ---

    # Теперь карточек точно 2
    assert len(cards) == 2, f"Получено карточек: {len(cards)}. Ответ: {cards}"

    auto_card = next(c for c in cards if c["word"] == "Automatic")
    manual_card = next(c for c in cards if c["word"] == "Manual")

    # Проверка работы интеграции с модулем перевода
    assert auto_card["translation"] == "Авто-перевод"
    # Проверка работы бизнес-логики (не затирать ручной ввод)
    assert manual_card["translation"] == manual_translation

    # ПРОВЕРКА: Был ли вызван транслятор только ОДИН раз?
    # (для Manual транслятор вызываться не должен)
    assert mock_post.call_count == 1

    # Проверка в реальной БД (Persistence Check)
    db_card = db_session.query(LangCard).filter(LangCard.word == "Automatic").first()
    assert db_card is not None
    assert db_card.translation == "Авто-перевод"


import pytest
import httpx
from models import User, Deck, LangCard
from sqlalchemy.orm import Session


@pytest.mark.asyncio
async def test_frontend_save_cards_workflow_simulation(client, db_session: Session, mocker):
    """
    СЦЕНАРИЙ: Симуляция работы фронтенда (React).
    Кейс: Пользователь открывает модалку, добавляет 2 новые карточки и редактирует 1 существующую.
    Проверяет интеграцию: Frontend Logic -> Multiple API Calls -> Database Consistency.
    """
    test_id = 555000

    # --- ШАГ 1: Предусловие (У нас уже есть колода и одна карточка) ---
    deck_resp = client.post("/decks/", json={
        "telegram_id": test_id, "name": "Frontend Test", "is_language_deck": True,
        "source_lang": "en", "target_lang": "ru"
    })
    deck_id = deck_resp.json()["id"]

    # Существующая карточка (которую будем "редактировать")
    old_card_resp = client.post("/lang_cards/", json={
        "deck_id": deck_id, "word": "Old Word", "source_lang": "en",
        "target_lang": "ru", "translation": "Старое слово"
    })
    old_card_id = old_card_resp.json()["id"]

    # --- ШАГ 2: Симуляция работы функции saveCards из App.jsx ---
    # В App.jsx функция запускает Promise.all([createPromises, updatePromises])

    # 1. Симулируем POST запросы для НОВЫХ карточек (как это делает React)
    new_cards_to_add = [
        {"deck_id": deck_id, "word": "Apple", "source_lang": "en", "target_lang": "ru", "translation": "Яблоко"},
        {"deck_id": deck_id, "word": "Orange", "source_lang": "en", "target_lang": "ru", "translation": "Апельсин"}
    ]

    for card_data in new_cards_to_add:
        resp = client.post("/lang_cards/", json=card_data)
        assert resp.status_code == 200

    # 2. Симулируем PUT запрос для ОБНОВЛЕНИЯ (пользователь изменил "Old Word" на "New Word")
    update_data = {"word": "Updated Word", "translation": "Обновленное слово"}
    update_resp = client.put(f"/lang_cards/{old_card_id}", json=update_data)
    assert update_resp.status_code == 200

    # --- ШАГ 3: Симуляция обновления интерфейса (fetchCards после сохранения) ---
    # Фронтенд запрашивает актуальный список, чтобы закрыть модалку и обновить грид
    final_get_resp = client.get(f"/lang_cards/{deck_id}")
    assert final_get_resp.status_code == 200
    cards_in_ui = final_get_resp.json()

    # --- ШАГ 4: Итоговая проверка консистентности (Интеграция завершена) ---

    # Всего должно быть 3 карточки (1 старая обновленная + 2 новых)
    assert len(cards_in_ui) == 3

    # Проверяем, что данные в БД соответствуют тому, что "видел" фронтенд
    words = [c["word"] for c in cards_in_ui]
    assert "Updated Word" in words
    assert "Apple" in words
    assert "Orange" in words
    assert "Old Word" not in words  # Старое слово должно исчезнуть (обновиться)

    # Проверка физического сохранения в БД через SQLAlchemy
    db_count = db_session.query(LangCard).filter(LangCard.deck_id == deck_id).count()
    assert db_count == 3



import pytest
from unittest.mock import AsyncMock
from sqlalchemy.orm import Session

try:
    from main import TimeInput
except ImportError:
    from aiogram.fsm.state import State, StatesGroup


    class TimeInput(StatesGroup):
        waiting_for_time = State()


@pytest.mark.asyncio
async def test_cross_module_user_sync_flow(client, db_session: Session, mocker):
    """
    СЦЕНАРИЙ: Полная синхронизация нового пользователя.
    Интеграция: Бот (логика регистрации) -> БД -> FastAPI (выдача данных).
    """
    new_tg_id = 11223344

    # --- ШАГ 1: ЛОГИКА БОТА (Модуль взаимодействия) ---
    # Имитируем функцию get_or_create_user, которую вызывает бот при старте
    from main import get_or_create_user

    logger.info(f"Бот: Пользователь {new_tg_id} нажал /start")
    bot_user = get_or_create_user(new_tg_id, db_session)
    assert bot_user.telegram_id == new_tg_id

    # --- ШАГ 2: БАЗА ДАННЫХ (Модуль данных) ---
    # Проверяем, что запись реально зафиксирована
    db_user = db_session.query(User).filter(User.telegram_id == new_tg_id).first()
    assert db_user is not None
    logger.info("БД: Запись пользователя подтверждена")

    # --- ШАГ 3: FASTAPI API (Модуль интеграции с фронтендом) ---
    # Теперь имитируем, что пользователь открыл WebApp.
    # Фронтенд делает запрос к API, чтобы получить колоды этого "новичка"
    api_response = client.get(f"/decks/{new_tg_id}/")

    assert api_response.status_code == 200
    # У нового пользователя должен быть пустой список колод, а не ошибка 404
    assert api_response.json() == []
    logger.info("API: Фронтенд успешно видит пользователя, созданного ботом")

    # --- ШАГ 4: ЗАВЕРШЕНИЕ ЦИКЛА ---
    # Создаем колоду через API и проверяем, что Бот (через БД) её увидит
    client.post("/decks/", json={
        "telegram_id": new_tg_id,
        "name": "Первая колода",
        "is_language_deck": False
    })

    user_decks_count = db_session.query(Deck).filter(Deck.user_id == db_user.id).count()
    assert user_decks_count == 1
    logger.info("Цикл завершен: Бот и API работают с одной областью данных")


import pytest
import httpx
from models import User, Deck, LangCard
from sqlalchemy.orm import Session


@pytest.mark.asyncio
async def test_multi_language_context_isolation(client, db_session: Session, mocker):
    """
    СЦЕНАРИЙ: Работа с омонимами в разных языковых парах.
    Проверяет интеграцию: API -> Логика контекстного перевода -> БД (уникальность связок).
    """
    test_id = 888111

    # --- ШАГ 1: Настройка мока для разных ответов переводчика ---
    # Мы имитируем, что переводчик умный и отвечает по-разному в зависимости от языка
    async def side_effect(url, json, **kwargs):
        # Если переводим с английского (en)
        if json.get("source") == "en" and json.get("q") == "Chat":
            return httpx.Response(200, json={"translatedText": "Чат (разговор)"},
                                  request=httpx.Request("POST", url))
        # Если переводим с французского (fr)
        if json.get("source") == "fr" and json.get("q") == "Chat":
            return httpx.Response(200, json={"translatedText": "Кот (животное)"},
                                  request=httpx.Request("POST", url))
        return httpx.Response(400, request=httpx.Request("POST", url))

    mocker.patch("httpx.AsyncClient.post", side_effect=side_effect)

    # --- ШАГ 2: Создание двух разных колод ---
    # 1. EN-RU
    deck_en_resp = client.post("/decks/", json={
        "telegram_id": test_id, "name": "English Deck", "is_language_deck": True,
        "source_lang": "en", "target_lang": "ru"
    })
    deck_en_id = deck_en_resp.json()["id"]

    # 2. FR-RU
    deck_fr_resp = client.post("/decks/", json={
        "telegram_id": test_id, "name": "French Deck", "is_language_deck": True,
        "source_lang": "fr", "target_lang": "ru"
    })
    deck_fr_id = deck_fr_resp.json()["id"]

    # --- ШАГ 3: Добавление одного и того же слова в обе колоды ---
    # Добавляем в английскую (ожидаем "Чат")
    client.post("/lang_cards/", json={
        "deck_id": deck_en_id, "word": "Chat", "source_lang": "en",
        "target_lang": "ru", "translation": None
    })

    # Добавляем во французскую (ожидаем "Кот")
    client.post("/lang_cards/", json={
        "deck_id": deck_fr_id, "word": "Chat", "source_lang": "fr",
        "target_lang": "ru", "translation": None
    })

    # --- ШАГ 4: Проверка изоляции данных в БД ---

    # Проверяем через API для английской колоды
    en_cards = client.get(f"/lang_cards/{deck_en_id}").json()
    assert en_cards[0]["translation"] == "Чат (разговор)"

    # Проверяем через API для французской колоды
    fr_cards = client.get(f"/lang_cards/{deck_fr_id}").json()
    assert fr_cards[0]["translation"] == "Кот (животное)"

    # --- ШАГ 5: Итоговая системная проверка ---
    # Убеждаемся, что в базе физически 2 разные записи
    total_cards = db_session.query(LangCard).count()
    assert total_cards == 2

    logger.info("Интеграция подтверждена: система различает контекст слова 'Chat' для разных колод.")

