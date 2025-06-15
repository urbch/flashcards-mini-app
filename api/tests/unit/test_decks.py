import pytest
from fastapi.testclient import TestClient
from main import app, get_db
from database import SessionLocal
from unittest.mock import Mock
from models import Deck, User

# Мокаем зависимость базы данных
@pytest.fixture
def mock_db():
    db = Mock()
    return db

# Настраиваем тестовый клиент с моком
@pytest.fixture
def client(mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db
    return TestClient(app)

def test_create_deck_valid(client, mock_db):
    # Мокаем вызовы к базе
    mock_user = User(id=1, telegram_id=123456789)
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.side_effect = lambda x: setattr(x, "id", 1)

    # Отправляем запрос
    response = client.post(
        "/decks/",
        json={
            "telegram_id": 123456789,
            "name": "Test Deck",
            "is_language_deck": True,
            "source_lang": "en",
            "target_lang": "es",
        },
    )
    # Проверяем ответ
    assert response.status_code == 200
    assert response.json()["name"] == "Test Deck"
    assert response.json()["is_language_deck"] is True
    assert response.json()["source_lang"] == "en"
    assert response.json()["target_lang"] == "es"

def test_create_deck_missing_fields(client, mock_db):
    # Мокаем вызовы к базе
    mock_user = User(id=1, telegram_id=123456789)
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user

    # Отправляем запрос с пропущенными полями
    response = client.post(
        "/decks/",
        json={
            "telegram_id": 123456789,
            "name": "Test Deck",
            "is_language_deck": True,
            # Пропущены source_lang и target_lang
        },
    )
    # Проверяем ошибку валидации
    assert response.status_code == 400
    assert "Source and target languages are required" in response.json()["detail"]
