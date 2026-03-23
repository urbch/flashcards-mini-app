import httpx
import pytest

from main import cached_translate, translate_word


# =========================
# Helpers
# =========================

class SuccessfulTranslateResponse:
    def __init__(self, translated_text="Привет"):
        self.status_code = 200
        self._translated_text = translated_text

    def json(self):
        return {"translatedText": self._translated_text}

    def raise_for_status(self):
        pass


class InvalidTranslateResponse:
    def __init__(self):
        self.status_code = 200

    def json(self):
        return {}

    def raise_for_status(self):
        pass


class HttpErrorTranslateResponse:
    def __init__(self, status_code=500, text="error"):
        self.status_code = status_code
        self.text = text

    def json(self):
        return {"detail": self.text}

    def raise_for_status(self):
        raise httpx.HTTPStatusError(
            f"Status {self.status_code}",
            request=None,
            response=self,
        )


class MockAsyncClientPostSuccess:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def post(self, *args, **kwargs):
        return SuccessfulTranslateResponse()


class MockAsyncClientPostInvalidResponse:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def post(self, *args, **kwargs):
        return InvalidTranslateResponse()


class MockAsyncClientPostHttpError:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def post(self, *args, **kwargs):
        return HttpErrorTranslateResponse()


class MockAsyncClientPostRequestError:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def post(self, *args, **kwargs):
        raise httpx.RequestError("Service unavailable")


# =========================
# POST /translate
# =========================

def test_translate_endpoint_returns_200_for_valid_translation_response(client, monkeypatch):
    """Endpoint /translate должен вернуть translatedText при корректном ответе сервиса перевода."""
    # Arrange
    monkeypatch.setattr("main.httpx.AsyncClient", MockAsyncClientPostSuccess)
    cached_translate.cache_clear()

    payload = {
        "q": "Hello",
        "source": "en",
        "target": "ru",
        "format": "text",
    }

    # Act
    response = client.post("/translate", json=payload)

    # Assert
    assert response.status_code == 200
    assert response.json()["translatedText"] == "Привет"


def test_translate_endpoint_returns_503_when_translation_service_is_unavailable(
        client, monkeypatch
):
    """Endpoint /translate должен вернуть 503, если сервис перевода недоступен."""
    # Arrange
    monkeypatch.setattr("main.httpx.AsyncClient", MockAsyncClientPostRequestError)
    cached_translate.cache_clear()

    payload = {
        "q": "Hello",
        "source": "en",
        "target": "ru",
        "format": "text",
    }

    # Act
    response = client.post("/translate", json=payload)

    # Assert
    assert response.status_code == 503
    assert "Translation service unavailable" in response.json()["detail"]


# =========================
# translate_word
# =========================

@pytest.mark.asyncio
async def test_translate_word_returns_translated_text_for_valid_response(monkeypatch):
    """Функция translate_word должна возвращать переведённый текст при корректном ответе."""
    # Arrange
    monkeypatch.setattr("main.httpx.AsyncClient", MockAsyncClientPostSuccess)

    # Act
    result = await translate_word("Hello", "en", "es")

    # Assert
    assert result == "Привет"


@pytest.mark.asyncio
async def test_translate_word_raises_exception_for_invalid_response(monkeypatch):
    """Если сервис не вернул translatedText, translate_word должна выбросить исключение."""
    # Arrange
    monkeypatch.setattr("main.httpx.AsyncClient", MockAsyncClientPostInvalidResponse)

    # Act / Assert
    with pytest.raises(Exception) as exc_info:
        await translate_word("Hello", "en", "es")

    assert "Invalid response" in str(exc_info.value)


@pytest.mark.asyncio
async def test_translate_word_raises_exception_for_http_error(monkeypatch):
    """Если сервис вернул HTTP-ошибку, translate_word должна выбросить исключение."""
    # Arrange
    monkeypatch.setattr("main.httpx.AsyncClient", MockAsyncClientPostHttpError)

    # Act / Assert
    with pytest.raises(Exception):
        await translate_word("Hello", "en", "es")


@pytest.mark.asyncio
async def test_translate_word_raises_exception_for_request_error(monkeypatch):
    """Если возникла сетевая ошибка, translate_word должна выбросить исключение."""
    # Arrange
    monkeypatch.setattr("main.httpx.AsyncClient", MockAsyncClientPostRequestError)

    # Act / Assert
    with pytest.raises(Exception):
        await translate_word("Hello", "en", "es")


# =========================
# cached_translate
# =========================

@pytest.mark.asyncio
async def test_cached_translate_returns_translated_text_for_valid_response(monkeypatch):
    """Функция cached_translate должна возвращать переведённый текст при корректном ответе."""
    # Arrange
    monkeypatch.setattr("main.httpx.AsyncClient", MockAsyncClientPostSuccess)
    cached_translate.cache_clear()

    # Act
    result = await cached_translate("Hello", "en", "ru")

    # Assert
    assert result == "Привет"


@pytest.mark.asyncio
async def test_cached_translate_raises_exception_for_invalid_response(monkeypatch):
    """Если сервис не вернул translatedText, cached_translate должна выбросить исключение."""
    # Arrange
    monkeypatch.setattr("main.httpx.AsyncClient", MockAsyncClientPostInvalidResponse)
    cached_translate.cache_clear()

    # Act / Assert
    with pytest.raises(Exception):
        await cached_translate("Hello", "en", "ru")


@pytest.mark.asyncio
async def test_cached_translate_raises_exception_for_http_error(monkeypatch):
    """Если сервис вернул HTTP-ошибку, cached_translate должна выбросить исключение."""
    # Arrange
    monkeypatch.setattr("main.httpx.AsyncClient", MockAsyncClientPostHttpError)
    cached_translate.cache_clear()

    # Act / Assert
    with pytest.raises(Exception):
        await cached_translate("Hello", "en", "ru")


@pytest.mark.asyncio
async def test_cached_translate_raises_exception_for_request_error(monkeypatch):
    """Если возникла сетевая ошибка, cached_translate должна выбросить исключение."""
    # Arrange
    monkeypatch.setattr("main.httpx.AsyncClient", MockAsyncClientPostRequestError)
    cached_translate.cache_clear()

    # Act / Assert
    with pytest.raises(Exception):
        await cached_translate("Hello", "en", "ru")