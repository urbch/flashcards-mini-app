import httpx
import pytest

from main import get_or_create_user, get_telegram_user_info
from models import User


# =========================
# Helpers
# =========================

def make_user(user_id=1, telegram_id=123456789):
    user = User()
    user.id = user_id
    user.telegram_id = telegram_id
    return user


class SuccessfulTelegramResponse:
    def json(self):
        return {
            "ok": True,
            "result": {
                "id": 1,
                "first_name": "Test",
            },
        }

    def raise_for_status(self):
        pass


class InvalidTelegramResponse:
    def json(self):
        return {"ok": False}

    def raise_for_status(self):
        pass


class MockAsyncClientSuccess:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def get(self, *args, **kwargs):
        return SuccessfulTelegramResponse()


class MockAsyncClientInvalidResponse:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def get(self, *args, **kwargs):
        return InvalidTelegramResponse()


class MockAsyncClientRequestError:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def get(self, *args, **kwargs):
        raise httpx.RequestError("fail")


# =========================
# get_or_create_user
# =========================

def test_get_or_create_user_returns_existing_user_without_creating_new_one(mock_db):
    """Если пользователь уже существует, функция должна вернуть его без создания новой записи."""
    # Arrange
    existing_user = make_user(user_id=1, telegram_id=123456789)
    mock_db.query.return_value.filter.return_value.first.return_value = existing_user

    # Act
    result = get_or_create_user(123456789, mock_db)

    # Assert
    assert result == existing_user
    mock_db.query.assert_called_once()
    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()
    mock_db.refresh.assert_not_called()


def test_get_or_create_user_creates_new_user_when_not_found(mock_db, db_refresh_sets_id):
    """Если пользователь не найден, функция должна создать и вернуть новую запись."""
    # Arrange
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.side_effect = db_refresh_sets_id

    # Act
    result = get_or_create_user(123456789, mock_db)

    # Assert
    assert result.id == 1
    assert result.telegram_id == 123456789
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()


# =========================
# get_telegram_user_info
# =========================

@pytest.mark.asyncio
async def test_get_telegram_user_info_returns_user_data_for_valid_response(monkeypatch):
    """Функция должна возвращать данные пользователя при корректном ответе Telegram API."""
    # Arrange
    monkeypatch.setattr("main.httpx.AsyncClient", MockAsyncClientSuccess)

    # Act
    result = await get_telegram_user_info("123")

    # Assert
    assert result is not None
    assert isinstance(result, dict)
    assert result["id"] == 1


@pytest.mark.asyncio
async def test_get_telegram_user_info_raises_exception_for_invalid_api_response(monkeypatch):
    """Если Telegram API вернул ok=False, функция должна выбросить исключение."""
    # Arrange
    monkeypatch.setattr("main.httpx.AsyncClient", MockAsyncClientInvalidResponse)

    # Act / Assert
    with pytest.raises(Exception) as exc_info:
        await get_telegram_user_info("123")

    assert "Failed to fetch user info" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_telegram_user_info_raises_exception_for_request_error(monkeypatch):
    """Если внешний HTTP-запрос завершился ошибкой, функция должна выбросить исключение."""
    # Arrange
    monkeypatch.setattr("main.httpx.AsyncClient", MockAsyncClientRequestError)

    # Act / Assert
    with pytest.raises(Exception):
        await get_telegram_user_info("123")


# =========================
# GET /users/{telegram_id}/info
# =========================

def test_get_user_info_endpoint_returns_200_and_name_for_valid_telegram_user(
        client, monkeypatch
):
    """Endpoint /users/{telegram_id}/info должен вернуть имя пользователя при корректном ответе Telegram API."""
    # Arrange
    monkeypatch.setattr("main.httpx.AsyncClient", MockAsyncClientSuccess)

    # Act
    response = client.get("/users/1/info")

    # Assert
    assert response.status_code == 200
    assert "name" in response.json()


# =========================
# GET /users/{telegram_id}
# =========================

def test_get_user_returns_404_when_user_not_found(client, mock_db):
    """Endpoint /users/{telegram_id} должен вернуть 404, если пользователь не найден."""
    # Arrange
    mock_db.query.return_value.filter.return_value.first.return_value = None

    # Act
    response = client.get("/users/999")

    # Assert
    assert response.status_code == 404


def test_get_user_returns_404_for_invalid_telegram_id_path_value(client):
    """Endpoint /users/{telegram_id} должен вернуть ошибку маршрута для невалидного path parameter."""
    # Act
    response = client.get("/users/invalid_id")

    # Assert
    assert response.status_code == 404