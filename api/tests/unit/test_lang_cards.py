import pytest

from models import Deck, LangCard


# =========================
# Helpers
# =========================

def make_language_deck(
        deck_id=1,
        user_id=1,
        source_lang="en",
        target_lang="es",
):
    return Deck(
        id=deck_id,
        user_id=user_id,
        is_language_deck=True,
        source_lang=source_lang,
        target_lang=target_lang,
    )


def make_regular_deck(deck_id=1, user_id=1):
    return Deck(
        id=deck_id,
        user_id=user_id,
        is_language_deck=False,
        source_lang=None,
        target_lang=None,
    )


def make_lang_card(card_id=1, deck_id=1, word="Hello", translation="Hola"):
    return LangCard(
        id=card_id,
        deck_id=deck_id,
        word=word,
        translation=translation,
    )


# =========================
# POST /lang_cards/
# =========================

@pytest.mark.asyncio
async def test_create_lang_card_returns_200_for_valid_payload(
        client, mock_db, db_refresh_sets_id, monkeypatch
):
    """Языковая карточка должна успешно создаваться для корректной языковой колоды."""
    # Arrange
    mock_deck = make_language_deck(deck_id=1, source_lang="en", target_lang="es")
    mock_db.query.return_value.filter.return_value.first.return_value = mock_deck
    mock_db.query.return_value.filter.return_value.count.return_value = 0
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.side_effect = db_refresh_sets_id

    async def mock_translate_word(word, source_lang, target_lang):
        return "Hola"

    monkeypatch.setattr("main.translate_word", mock_translate_word)

    payload = {
        "deck_id": 1,
        "word": "Hello",
        "source_lang": "en",
        "target_lang": "es",
    }

    # Act
    response = client.post("/lang_cards/", json=payload)

    # Assert
    assert response.status_code == 200
    body = response.json()

    assert body["id"] == 1
    assert body["deck_id"] == 1
    assert body["word"] == "Hello"
    assert body["translation"] == "Hola"

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

def test_create_lang_card_returns_400_when_deck_reaches_lang_card_limit(client, mock_db):
    """Если в языковой колоде достигнут лимит карточек, новая language card не должна создаваться."""
    # Arrange
    mock_deck = make_language_deck(deck_id=1, source_lang="en", target_lang="es")

    query_obj = mock_db.query.return_value
    filter_obj = query_obj.filter.return_value

    filter_obj.first.side_effect = [mock_deck]
    filter_obj.count.side_effect = [100]

    payload = {
        "deck_id": 1,
        "word": "Hello",
        "source_lang": "en",
        "target_lang": "es",
    }

    # Act
    response = client.post("/lang_cards/", json=payload)

    # Assert
    assert response.status_code == 400
    assert "лимит" in response.json()["detail"].lower()

    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()
    mock_db.refresh.assert_not_called()

def test_create_lang_card_returns_400_when_deck_not_found(client, mock_db):
    """Если колода не найдена, создание языковой карточки должно завершаться 400."""
    # Arrange
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_db.query.return_value.filter.return_value.count.return_value = 0

    payload = {
        "deck_id": 999,
        "word": "Hello",
        "source_lang": "en",
        "target_lang": "es",
    }

    # Act
    response = client.post("/lang_cards/", json=payload)

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid deck for language cards"

    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()
    mock_db.refresh.assert_not_called()


def test_create_lang_card_returns_400_when_deck_is_not_language_deck(client, mock_db):
    """Если колода существует, но не является языковой, создание должно завершаться 400."""
    # Arrange
    mock_db.query.return_value.filter.return_value.count.return_value = 0
    mock_db.query.return_value.filter.return_value.first.return_value = make_regular_deck(
        deck_id=1
    )

    payload = {
        "deck_id": 1,
        "word": "Hello",
        "source_lang": "en",
        "target_lang": "es",
    }

    # Act
    response = client.post("/lang_cards/", json=payload)

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid deck for language cards"


# =========================
# GET /lang_cards/{deck_id}
# =========================

def test_get_lang_cards_returns_200_and_cards_for_existing_language_deck(client, mock_db):
    """Для существующей языковой колоды должен возвращаться список language cards."""
    # Arrange
    mock_deck = make_language_deck(deck_id=1)
    mock_cards = [
        make_lang_card(card_id=1, deck_id=1, word="Hello", translation="Hola"),
        make_lang_card(card_id=2, deck_id=1, word="World", translation="Mundo"),
    ]

    mock_db.query.return_value.filter.return_value.first.return_value = mock_deck
    mock_db.query.return_value.filter.return_value.all.return_value = mock_cards

    # Act
    response = client.get("/lang_cards/1")

    # Assert
    assert response.status_code == 200
    body = response.json()

    assert len(body) == 2
    assert body[0]["word"] == "Hello"
    assert body[0]["translation"] == "Hola"
    assert body[1]["word"] == "World"
    assert body[1]["translation"] == "Mundo"


def test_get_lang_cards_returns_empty_list_for_existing_language_deck_without_cards(
        client, mock_db
):
    """Если языковая колода существует, но карточек нет, должен вернуться пустой список."""
    # Arrange
    mock_deck = make_language_deck(deck_id=1)

    mock_db.query.return_value.filter.return_value.first.return_value = mock_deck
    mock_db.query.return_value.filter.return_value.all.return_value = []

    # Act
    response = client.get("/lang_cards/1")

    # Assert
    assert response.status_code == 200
    assert response.json() == []


def test_get_lang_cards_returns_400_when_deck_is_invalid(client, mock_db):
    """Если колода не найдена или не является языковой, должен возвращаться 400."""
    # Arrange
    mock_db.query.return_value.filter.return_value.first.return_value = None

    # Act
    response = client.get("/lang_cards/1")

    # Assert
    assert response.status_code == 400


# =========================
# PUT /lang_cards/{card_id}
# =========================

def test_update_lang_card_returns_200_for_existing_card(client, mock_db):
    """Существующая языковая карточка должна успешно обновляться."""
    # Arrange
    mock_card = make_lang_card(card_id=1, deck_id=1, word="Old", translation="Viejo")
    mock_db.query.return_value.filter.return_value.first.return_value = mock_card
    mock_db.commit.return_value = None
    mock_db.refresh.side_effect = lambda obj: None

    payload = {
        "word": "New",
        "translation": "Nuevo",
    }

    # Act
    response = client.put("/lang_cards/1", json=payload)

    # Assert
    assert response.status_code == 200
    body = response.json()

    assert body["id"] == 1
    assert body["deck_id"] == 1
    assert body["word"] == "New"
    assert body["translation"] == "Nuevo"

    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()


def test_update_lang_card_returns_404_when_card_not_found(client, mock_db):
    """Если языковая карточка не найдена, обновление должно завершаться 404."""
    # Arrange
    mock_db.query.return_value.filter.return_value.first.return_value = None

    payload = {
        "word": "New",
        "translation": "Nuevo",
    }

    # Act
    response = client.put("/lang_cards/1", json=payload)

    # Assert
    assert response.status_code == 404


# =========================
# DELETE /lang_cards/{card_id}
# =========================

def test_delete_lang_card_returns_200_for_existing_card(client, mock_db):
    """Существующая языковая карточка должна успешно удаляться."""
    # Arrange
    mock_card = make_lang_card(card_id=1, deck_id=1, word="Hello", translation="Hola")
    mock_db.query.return_value.filter.return_value.first.return_value = mock_card
    mock_db.delete.return_value = None
    mock_db.commit.return_value = None

    # Act
    response = client.delete("/lang_cards/1")

    # Assert
    assert response.status_code == 200
    mock_db.delete.assert_called_once_with(mock_card)
    mock_db.commit.assert_called_once()


def test_delete_lang_card_returns_404_when_card_not_found(client, mock_db):
    """Если языковая карточка не найдена, удаление должно завершаться 404."""
    # Arrange
    mock_db.query.return_value.filter.return_value.first.return_value = None

    # Act
    response = client.delete("/lang_cards/1")

    # Assert
    assert response.status_code == 404