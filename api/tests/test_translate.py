import pytest
from fastapi.testclient import TestClient
from main import app, cached_translate
from unittest.mock import patch
import httpx

@pytest.fixture
def client():
    return TestClient(app)

@pytest.mark.asyncio
async def test_translate_success(client, monkeypatch):
    # Мокаем httpx.AsyncClient
    class MockResponse:
        def __init__(self):
            self.status_code = 200

        def json(self):  # Синхронный метод
            return {"translatedText": "Привет"}

        def raise_for_status(self):
            if self.status_code >= 400:
                raise httpx.HTTPStatusError(
                    f"Status {self.status_code}",
                    request=None,
                    response=self,
                )

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

    class MockAsyncClient:
        def __init__(self, timeout=None):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def post(self, url, **kwargs):
            return MockResponse()

    monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)

    # Очищаем lru_cache перед тестом
    cached_translate.cache_clear()

    # Отправляем запрос
    response = client.post(
        "/translate",
        json={
            "q": "Hello",
            "source": "en",
            "target": "ru",
            "format": "text",
        },
    )
    # Проверяем ответ
    assert response.status_code == 200
    assert response.json()["translatedText"] == "Привет"

@pytest.mark.asyncio
async def test_translate_service_unavailable(client, monkeypatch):
    # Мокаем httpx.AsyncClient с ошибкой
    class MockAsyncClient:
        def __init__(self, timeout=None):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def post(self, url, **kwargs):
            raise httpx.RequestError("Service unavailable")

    monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)

    # Очищаем lru_cache перед тестом
    cached_translate.cache_clear()

    # Отправляем запрос
    response = client.post(
        "/translate",
        json={
            "q": "Hello",
            "source": "en",
            "target": "ru",
            "format": "text",
        },
    )
    # Проверяем ошибку
    assert response.status_code == 503
    assert "Translation service unavailable" in response.json()["detail"]
