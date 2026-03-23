from models import Card, Deck


# =========================
# Helpers
# =========================

def make_deck(deck_id=1, user_id=1):
    return Deck(id=deck_id, user_id=user_id)


def make_card(card_id=1, deck_id=1, term="Capital", definition="Definition"):
    return Card(
        id=card_id,
        deck_id=deck_id,
        term=term,
        definition=definition,
    )


# =========================
# POST /cards/
# =========================

def test_create_card_returns_200_for_valid_payload(client, mock_db, db_refresh_sets_id):
    """Карточка должна успешно создаваться для существующей колоды."""
    # Arrange
    mock_deck = make_deck(deck_id=1, user_id=1)
    mock_db.query.return_value.filter.return_value.first.return_value = mock_deck
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.side_effect = db_refresh_sets_id

    payload = {
        "deck_id": 1,
        "term": "Capital",
        "definition": "A city that serves as the seat of government",
    }

    # Act
    response = client.post("/cards/", json=payload)

    # Assert
    assert response.status_code == 200
    body = response.json()

    assert body["id"] == 1
    assert body["deck_id"] == 1
    assert body["term"] == "Capital"
    assert body["definition"] == "A city that serves as the seat of government"

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()


def test_create_card_returns_404_when_deck_not_found(client, mock_db):
    """Если колода не найдена, создание карточки должно завершаться 404."""
    # Arrange
    mock_db.query.return_value.filter.return_value.first.return_value = None

    payload = {
        "deck_id": 999,
        "term": "Capital",
        "definition": "A city that serves as the seat of government",
    }

    # Act
    response = client.post("/cards/", json=payload)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Deck not found"

    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()
    mock_db.refresh.assert_not_called()


# =========================
# GET /cards/{deck_id}
# =========================

def test_get_cards_returns_200_and_cards_for_existing_deck(client, mock_db):
    """Для существующей колоды должен возвращаться список карточек."""
    # Arrange
    mock_deck = make_deck(deck_id=1)
    mock_card = make_card(card_id=1, deck_id=1, term="A", definition="B")

    mock_db.query.return_value.filter.return_value.first.return_value = mock_deck
    mock_db.query.return_value.filter.return_value.all.return_value = [mock_card]

    # Act
    response = client.get("/cards/1")

    # Assert
    assert response.status_code == 200
    body = response.json()

    assert len(body) == 1
    assert body[0]["id"] == 1
    assert body[0]["deck_id"] == 1
    assert body[0]["term"] == "A"
    assert body[0]["definition"] == "B"


def test_get_cards_returns_empty_list_for_existing_deck_without_cards(client, mock_db):
    """Если колода существует, но карточек нет, должен возвращаться пустой список."""
    # Arrange
    mock_deck = make_deck(deck_id=1)

    mock_db.query.return_value.filter.return_value.first.return_value = mock_deck
    mock_db.query.return_value.filter.return_value.all.return_value = []

    # Act
    response = client.get("/cards/1")

    # Assert
    assert response.status_code == 200
    assert response.json() == []


def test_get_cards_returns_404_when_deck_not_found(client, mock_db):
    """Если колода не найдена, получение карточек должно завершаться 404."""
    # Arrange
    mock_db.query.return_value.filter.return_value.first.return_value = None

    # Act
    response = client.get("/cards/1")

    # Assert
    assert response.status_code == 404


# =========================
# PUT /cards/{card_id}
# =========================

def test_update_card_returns_200_for_existing_card(client, mock_db):
    """Существующая карточка должна успешно обновляться."""
    # Arrange
    mock_card = make_card(card_id=1, deck_id=1, term="Old", definition="Old Def")
    mock_db.query.return_value.filter.return_value.first.return_value = mock_card
    mock_db.commit.return_value = None
    mock_db.refresh.side_effect = lambda obj: None

    payload = {
        "term": "New Capital",
        "definition": "Updated definition",
    }

    # Act
    response = client.put("/cards/1", json=payload)

    # Assert
    assert response.status_code == 200
    body = response.json()

    assert body["id"] == 1
    assert body["deck_id"] == 1
    assert body["term"] == "New Capital"
    assert body["definition"] == "Updated definition"

    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()


def test_update_card_returns_404_when_card_not_found(client, mock_db):
    """Если карточка не найдена, обновление должно завершаться 404."""
    # Arrange
    mock_db.query.return_value.filter.return_value.first.return_value = None

    payload = {
        "term": "x",
        "definition": "y",
    }

    # Act
    response = client.put("/cards/1", json=payload)

    # Assert
    assert response.status_code == 404


# =========================
# DELETE /cards/{card_id}
# =========================

def test_delete_card_returns_200_for_existing_card(client, mock_db):
    """Существующая карточка должна успешно удаляться."""
    # Arrange
    mock_card = make_card(card_id=1, deck_id=1, term="Capital", definition="Def")
    mock_db.query.return_value.filter.return_value.first.return_value = mock_card
    mock_db.delete.return_value = None
    mock_db.commit.return_value = None

    # Act
    response = client.delete("/cards/1")

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == "Card deleted successfully"

    mock_db.delete.assert_called_once_with(mock_card)
    mock_db.commit.assert_called_once()


def test_delete_card_returns_not_found_status_for_missing_card(client, mock_db):
    """При удалении несуществующей карточки должен возвращаться статус not found."""
    # Arrange
    mock_db.query.return_value.filter.return_value.first.return_value = None

    # Act
    response = client.delete("/cards/999")

    # Assert
    assert response.status_code in (404, 400)