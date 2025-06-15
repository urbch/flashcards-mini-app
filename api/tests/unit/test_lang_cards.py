import pytest
from fastapi.testclient import TestClient
from main import app, get_db, translate_word
from database import SessionLocal
from unittest.mock import Mock, AsyncMock
from models import Deck, LangCard
from unittest.mock import patch

@pytest.fixture
def mock_db():
    db = Mock()
    return db

@pytest.fixture
def client(mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db
    return TestClient(app)

@pytest.mark.asyncio
async def test_create_lang_card_valid(client, mock_db, monkeypatch):
    # Мокаем вызовы к базе
    mock_deck = Deck(id=1, is_language_deck=True, source_lang="en", target_lang="es")
    mock_db.query.return_value.filter.return_value.first.return_value = mock_deck
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.side_effect = lambda x: setattr(x, "id", 1)

    # Мокаем перевод
    async def mock_translate_word(word, source_lang, target_lang):
        return "Hola"
    monkeypatch.setattr("main.translate_word", mock_translate_word)

    # Отправляем запрос
    response = client.post(
        "/lang_cards/",
        json={
            "deck_id": 1,
            "word": "Hello",
            "source_lang": "en",
            "target_lang": "es",
        },
    )
    # Проверяем ответ
    assert response.status_code == 200
    assert response.json()["deck_id"] == 1
    assert response.json()["word"] == "Hello"
    assert response.json()["translation"] == "Hola"

def test_create_lang_card_invalid_deck(client, mock_db):
    # Мокаем отсутствие колоды
    mock_db.query.return_value.filter.return_value.first.return_value = None

    # Отправляем запрос
    response = client.post(
        "/lang_cards/",
        json={
            "deck_id": 999,
            "word": "Hello",
            "source_lang": "en",
            "target_lang": "es",
        },
    )
    # Проверяем ошибку
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid deck for language cards"
