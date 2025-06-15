import pytest
from fastapi.testclient import TestClient
from main import app, get_db
from database import SessionLocal
from unittest.mock import Mock
from models import Deck, Card

@pytest.fixture
def mock_db():
    db = Mock()
    return db

@pytest.fixture
def client(mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db
    return TestClient(app)

def test_create_card_valid(client, mock_db):
    # Мокаем вызовы к базе
    mock_deck = Deck(id=1, user_id=1)
    mock_db.query.return_value.filter.return_value.first.return_value = mock_deck
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.side_effect = lambda x: setattr(x, "id", 1)

    # Отправляем запрос
    response = client.post(
        "/cards/",
        json={
            "deck_id": 1,
            "term": "Capital",
            "definition": "A city that serves as the seat of government",
        },
    )
    # Проверяем ответ
    assert response.status_code == 200
    assert response.json()["deck_id"] == 1
    assert response.json()["term"] == "Capital"
    assert response.json()["definition"] == "A city that serves as the seat of government"

def test_create_card_invalid_deck(client, mock_db):
    # Мокаем отсутствие колоды
    mock_db.query.return_value.filter.return_value.first.return_value = None

    # Отправляем запрос
    response = client.post(
        "/cards/",
        json={
            "deck_id": 999,
            "term": "Capital",
            "definition": "A city that serves as the seat of government",
        },
    )
    # Проверяем ошибку
    assert response.status_code == 404
    assert response.json()["detail"] == "Deck not found"

def test_update_card_valid(client, mock_db):
    # Мокаем существующую карточку
    mock_card = Card(id=1, deck_id=1, term="Old", definition="Old Def")
    mock_db.query.return_value.filter.return_value.first.return_value = mock_card
    mock_db.commit.return_value = None
    mock_db.refresh.side_effect = lambda x: None

    # Отправляем запрос
    response = client.put(
        "/cards/1",
        json={
            "term": "New Capital",
            "definition": "Updated definition",
        },
    )
    # Проверяем ответ
    assert response.status_code == 200
    assert response.json()["term"] == "New Capital"
    assert response.json()["definition"] == "Updated definition"

def test_delete_card_valid(client, mock_db):
    # Мокаем существующую карточку
    mock_card = Card(id=1, deck_id=1, term="Capital", definition="Def")
    mock_db.query.return_value.filter.return_value.first.return_value = mock_card
    mock_db.delete.return_value = None
    mock_db.commit.return_value = None

    # Отправляем запрос
    response = client.delete("/cards/1")
    # Проверяем ответ
    assert response.status_code == 200
    assert response.json()["message"] == "Card deleted successfully"
