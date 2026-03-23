import httpx
import pytest

from main import cached_translate


# =========================
# Helpers
# =========================

def make_languages_response():
    return [
        {"code": "en", "name": "English"},
        {"code": "es", "name": "Spanish"},
    ]


class SuccessfulLanguagesResponse:
    def __init__(self, json_data=None):
        self.status_code = 200
        self._json_data = json_data or make_languages_response()

    def json(self):
        return self._json_data

    def raise_for_status(self):
        pass


class HttpErrorLanguagesResponse:
    status_code = 500
    text = "error"

    def json(self):
        return {"detail": "error"}

    def raise_for_status(self):
        raise httpx.HTTPStatusError("error", request=None, response=self)


class SuccessfulTranslateResponse:
    def __init__(self, translated_text="Привет"):
        self._translated_text = translated_text

    def json(self):
        return {"translatedText": self._translated_text}

    def raise_for_status(self):
        pass


class MockAsyncClientForGetSuccess:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def get(self, *args, **kwargs):
        return SuccessfulLanguagesResponse()


class MockAsyncClientForGetHttpError:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def get(self, *args, **kwargs):
        return HttpErrorLanguagesResponse()


class MockAsyncClientForGetRequestError:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def get(self, *args, **kwargs):
        raise httpx.RequestError("fail")


class MockAsyncClientForPostSuccess:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def post(self, *args, **kwargs):
        return SuccessfulTranslateResponse()


# =========================
# GET /languages/
# =========================

def test_get_languages_returns_200_and_language_list_for_valid_external_response(
        client, monkeypatch
):
    """Endpoint /languages/ должен вернуть список языков при корректном ответе внешнего сервиса."""
    # Arrange
    monkeypatch.setattr("main.httpx.AsyncClient", MockAsyncClientForGetSuccess)

    # Act
    response = client.get("/languages/")

    # Assert
    assert response.status_code == 200
    assert response.json() == make_languages_response()


def test_get_languages_returns_500_when_external_service_returns_http_error(
        client, monkeypatch
):
    """Endpoint /languages/ должен вернуть 500, если внешний сервис вернул HTTP-ошибку."""
    # Arrange
    monkeypatch.setattr("main.httpx.AsyncClient", MockAsyncClientForGetHttpError)

    # Act
    response = client.get("/languages/")

    # Assert
    assert response.status_code == 500


def test_get_languages_returns_503_when_external_service_request_fails(
        client, monkeypatch
):
    """Endpoint /languages/ должен вернуть 503, если произошла сетевая ошибка запроса."""
    # Arrange
    monkeypatch.setattr("main.httpx.AsyncClient", MockAsyncClientForGetRequestError)

    # Act
    response = client.get("/languages/")

    # Assert
    assert response.status_code == 503


# =========================
# cached_translate
# =========================

@pytest.mark.asyncio
async def test_cached_translate_returns_translated_text_for_valid_response(monkeypatch):
    """Функция cached_translate должна возвращать translatedText при корректном ответе сервиса."""
    # Arrange
    monkeypatch.setattr("main.httpx.AsyncClient", MockAsyncClientForPostSuccess)
    cached_translate.cache_clear()

    # Act
    result = await cached_translate("Hello", "en", "ru")

    # Assert
    assert result == "Привет"