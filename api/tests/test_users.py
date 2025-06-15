import pytest
from main import get_or_create_user
from database import SessionLocal
from unittest.mock import Mock
from models import User

@pytest.fixture
def mock_db():
    db = Mock()
    return db

@pytest.mark.asyncio
async def test_get_or_create_user_existing(mock_db):
    # Мокаем существующего пользователя
    mock_user = User(id=1, telegram_id=123456789)
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user

    # Вызываем функцию
    user = await get_or_create_user(123456789, mock_db)

    # Проверяем результат
    assert user.id == 1
    assert user.telegram_id == 123456789
    assert mock_db.add.not_called()
    assert mock_db.commit.not_called()

@pytest.mark.asyncio
async def test_get_or_create_user_new(mock_db):
    # Мокаем отсутствие пользователя
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.side_effect = lambda x: setattr(x, "id", 1)

    # Вызываем функцию
    user = await get_or_create_user(123456789, mock_db)

    # Проверяем результат
    assert user.telegram_id == 123456789
    assert mock_db.add.called
    assert mock_db.commit.called
    assert mock_db.refresh.called
