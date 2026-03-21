import pytest
import sys
import os
from unittest.mock import AsyncMock

# Добавляем путь к корню проекта
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def mock_bot():
    """Фикстура для мока бота"""
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    return bot


@pytest.fixture
def mock_dispatcher():
    """Фикстура для мока диспетчера"""
    dp = AsyncMock()
    dp.start_polling = AsyncMock()
    return dp