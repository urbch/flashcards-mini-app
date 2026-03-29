import pytest

from models import Deck, User


# =========================
# Helpers
# =========================

def make_user(user_id=1, telegram_id=123456789):
    return User(id=user_id, telegram_id=telegram_id)


def make_deck(
        deck_id=1,
        user_id=1,
        name="Test Deck",
        is_language_deck=False,
        source_lang=None,
        target_lang=None,
):
    return Deck(
        id=deck_id,
        user_id=user_id,
        name=name,
        is_language_deck=is_language_deck,
        source_lang=source_lang,
        target_lang=target_lang,
    )


# =========================
# POST /decks/
# =========================

def test_create_deck_returns_200_for_valid_language_deck_payload(
        client, mock_db, db_refresh_sets_id
):
    """Должна успешно создаваться языковая колода с заполненными source_lang и target_lang."""
    # Arrange
    mock_user = make_user()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user
    mock_db.query.return_value.filter.return_value.count.return_value = 0
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.side_effect = db_refresh_sets_id

    payload = {
        "telegram_id": 123456789,
        "name": "Test Deck",
        "is_language_deck": True,
        "source_lang": "en",
        "target_lang": "es",
    }

    # Act
    response = client.post("/decks/", json=payload)

    # Assert
    assert response.status_code == 200
    body = response.json()

    assert body["id"] == 1
    assert body["name"] == "Test Deck"
    assert body["is_language_deck"] is True
    assert body["source_lang"] == "en"
    assert body["target_lang"] == "es"

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

def test_create_deck_returns_400_when_user_reaches_deck_limit(client, mock_db):
    """Если пользователь достиг лимита колод, новая колода не должна создаваться."""
    # Arrange
    mock_user = make_user()

    query_obj = mock_db.query.return_value
    filter_obj = query_obj.filter.return_value

    filter_obj.first.side_effect = [mock_user]
    filter_obj.count.side_effect = [20]

    payload = {
        "telegram_id": 123456789,
        "name": "One More Deck",
        "is_language_deck": False,
        "source_lang": None,
        "target_lang": None,
    }

    # Act
    response = client.post("/decks/", json=payload)

    # Assert
    assert response.status_code == 400
    assert "лимит" in response.json()["detail"].lower()

    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()
    mock_db.refresh.assert_not_called()


def test_create_deck_returns_400_when_language_deck_has_missing_languages(
        client, mock_db
):
    """Для языковой колоды source_lang и target_lang обязательны."""
    # Arrange
    mock_user = make_user()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user
    mock_db.query.return_value.filter.return_value.count.return_value = 0

    payload = {
        "telegram_id": 123456789,
        "name": "Test Deck",
        "is_language_deck": True,
    }

    # Act
    response = client.post("/decks/", json=payload)

    # Assert
    assert response.status_code == 400
    assert "Source and target languages are required" in response.json()["detail"]

    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()
    mock_db.refresh.assert_not_called()

def test_create_deck_returns_400_when_languages_are_same(client, mock_db):
    """Для языковой колоды source_lang и target_lang не должны совпадать."""
    mock_user = make_user()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user
    mock_db.query.return_value.filter.return_value.count.return_value = 0

    payload = {
        "telegram_id": 123456789,
        "name": "Test Deck",
        "is_language_deck": True,
        "source_lang": "en",
        "target_lang": "en",
    }

    response = client.post("/decks/", json=payload)

    assert response.status_code == 400
    assert "must be different" in response.json()["detail"].lower()

    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()
    mock_db.refresh.assert_not_called()


def test_create_deck_returns_200_for_valid_regular_deck_payload(
        client, mock_db, db_refresh_sets_id
):
    """Обычная колода должна успешно создаваться без языковых полей."""
    # Arrange
    mock_user = make_user()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user
    mock_db.query.return_value.filter.return_value.count.return_value = 0
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.side_effect = db_refresh_sets_id

    payload = {
        "telegram_id": 123456789,
        "name": "Regular Deck",
        "is_language_deck": False,
        "source_lang": None,
        "target_lang": None,
    }

    # Act
    response = client.post("/decks/", json=payload)

    # Assert
    assert response.status_code == 200
    body = response.json()

    assert body["id"] == 1
    assert body["name"] == "Regular Deck"
    assert body["is_language_deck"] is False
    assert body["source_lang"] is None
    assert body["target_lang"] is None


# =========================
# GET /decks/{telegram_id}/
# =========================

def test_get_decks_returns_200_and_user_decks_for_existing_user(client, mock_db):
    """Список колод должен возвращаться для существующего пользователя."""
    # Arrange
    mock_user = make_user(user_id=1, telegram_id=123)
    mock_decks = [
        make_deck(deck_id=1, user_id=1, name="Deck 1"),
        make_deck(deck_id=2, user_id=1, name="Deck 2"),
    ]

    mock_db.query.return_value.filter.return_value.first.return_value = mock_user
    mock_db.query.return_value.filter.return_value.all.return_value = mock_decks

    # Act
    response = client.get("/decks/123/")

    # Assert
    assert response.status_code == 200
    body = response.json()

    assert len(body) == 2
    assert body[0]["name"] == "Deck 1"
    assert body[1]["name"] == "Deck 2"


def test_get_decks_returns_empty_list_when_user_has_no_decks(client, mock_db):
    """Если у пользователя нет колод, endpoint должен вернуть пустой список."""
    # Arrange
    mock_user = make_user(user_id=1, telegram_id=123)

    mock_db.query.return_value.filter.return_value.first.return_value = mock_user
    mock_db.query.return_value.filter.return_value.all.return_value = []

    # Act
    response = client.get("/decks/123/")

    # Assert
    assert response.status_code == 200
    assert response.json() == []


# =========================
# DELETE /decks/{deck_id}
# =========================

def test_delete_deck_returns_200_for_existing_deck(client, mock_db):
    """Существующая колода должна успешно удаляться."""
    # Arrange
    mock_deck = make_deck(deck_id=1)
    mock_db.query.return_value.filter.return_value.first.return_value = mock_deck

    # Act
    response = client.delete("/decks/1")

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == "Deck deleted successfully"

    mock_db.delete.assert_called_once_with(mock_deck)
    mock_db.commit.assert_called_once()


def test_delete_deck_returns_not_found_status_for_missing_deck(client, mock_db):
    """При удалении несуществующей колоды должен возвращаться статус not found."""
    # Arrange
    mock_db.query.return_value.filter.return_value.first.return_value = None

    # Act
    response = client.delete("/decks/999")

    # Assert
    assert response.status_code in (404, 400)