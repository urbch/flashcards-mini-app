import pytest
from unittest.mock import Mock
from main import get_or_create_user
from models import User

@pytest.fixture
def mock_db():
    return Mock()

def test_get_or_create_user_existing(mock_db):
    # Мокаем существующего пользователя
    mock_user = User(id=1, telegram_id=123456789)
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user

    # Вызываем функцию
    user = get_or_create_user(123456789, mock_db)
    assert user == mock_user
    mock_db.query.assert_called_once()
    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()
    mock_db.refresh.assert_not_called()

def test_get_or_create_user_new(mock_db):
    # Мокаем отсутствие пользователя
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.side_effect = lambda x: setattr(x, "id", 1)

    # Вызываем функцию
    user = get_or_create_user(123456789, mock_db)
    assert user.id == 1
    assert user.telegram_id == 123456789
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()
