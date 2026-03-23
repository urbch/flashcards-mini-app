import os
import sys
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient

# Добавляем путь к корню проекта
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from main import app, get_db


# =========================
# Core API fixtures
# =========================

@pytest.fixture
def mock_db():
    """Мок сессии БД для unit/API-unit тестов."""
    return Mock()


@pytest.fixture
def override_get_db(mock_db):
    """Подмена зависимости get_db на mock_db."""
    def _override():
        return mock_db

    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client(mock_db, override_get_db):
    """Тестовый клиент FastAPI с замоканной БД."""
    with TestClient(app) as test_client:
        yield test_client


# =========================
# Shared helper fixtures
# =========================

@pytest.fixture
def db_refresh_sets_id():
    """
    Хелпер для mock_db.refresh:
    при refresh(obj) выставляет obj.id = 1, если id ещё нет.
    """
    def _apply(obj, obj_id=1):
        if getattr(obj, "id", None) is None:
            setattr(obj, "id", obj_id)

    return _apply


@pytest.fixture
def mock_async_http_response():
    """
    Фабрика простого HTTP-ответа для моков внешних сервисов.
    Используется в users/translate/languages тестах.
    """
    class MockResponse:
        def __init__(self, json_data=None, status_code=200):
            self._json_data = json_data or {}
            self.status_code = status_code

        def json(self):
            return self._json_data

        def raise_for_status(self):
            if self.status_code >= 400:
                raise Exception(f"HTTP {self.status_code}")

    return MockResponse


@pytest.fixture
def async_client_factory():
    """
    Фабрика async context manager для monkeypatch httpx.AsyncClient.
    Пример:
        monkeypatch.setattr("main.httpx.AsyncClient", async_client_factory(get=...))
    """
    def _factory(get=None, post=None):
        class MockAsyncClient:
            def __init__(self, *args, **kwargs):
                self.args = args
                self.kwargs = kwargs

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                pass

            async def get(self, *args, **kwargs):
                if get is None:
                    raise NotImplementedError("Mock GET handler is not configured")
                if callable(get):
                    return await get(*args, **kwargs) if hasattr(get, "__await__") else get(*args, **kwargs)
                return get

            async def post(self, *args, **kwargs):
                if post is None:
                    raise NotImplementedError("Mock POST handler is not configured")
                if callable(post):
                    return await post(*args, **kwargs) if hasattr(post, "__await__") else post(*args, **kwargs)
                return post

        return MockAsyncClient

    return _factory


# =========================
# Optional async mocks
# =========================

@pytest.fixture
def mock_async_function():
    """Универсальный AsyncMock для подмены async-функций."""
    return AsyncMock()