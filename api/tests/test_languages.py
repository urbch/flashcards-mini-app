import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch
import httpx

@pytest.fixture
def client():
    return TestClient(app)

@pytest.mark.asyncio
async def test_get_languages_success(client, monkeypatch):
    # Мокаем httpx.AsyncClient
    class MockResponse:
        def __init__(self):
            self.status_code = 200

        def json(self):  # Синхронный метод
            return [{"code": "en", "name": "English"}]

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

        async def get(self, url, **kwargs):
            return MockResponse()

    monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)

    # Отправляем запрос
    response = client.get("/languages/")
    # Проверяем ответ
    assert response.status_code == 200
    assert response.json() == [{"code": "en", "name": "English"}]
