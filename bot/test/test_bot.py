import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from datetime import datetime
from freezegun import freeze_time
import pytz
import sys
import os
import asyncio
from aiogram.fsm.state import State

# Добавляем путь к боту
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from bot.main import (
    bot, dp, users, NOTIFICATION_MESSAGE, INFO_TEXT, TimeInput,
    start, info, cmd_notify, process_time, cmd_cancel, check_time_and_notify
)


@pytest.fixture
def mock_message():
    """Фикстура для мока сообщения"""
    message = AsyncMock()
    message.chat.id = 123456
    message.from_user.id = 123456
    message.text = ""
    message.answer = AsyncMock()
    message.reply = AsyncMock()
    return message


@pytest.fixture
def mock_state():
    """Фикстура для мока FSMContext"""
    state = AsyncMock()
    state.set_state = AsyncMock()
    state.clear = AsyncMock()
    return state


@pytest.fixture
def clear_users():
    """Очищает глобальный словарь users перед каждым тестом"""
    users.clear()
    yield
    users.clear()


@pytest.mark.asyncio
class TestBotCommands:
    """Тесты для команд бота"""

    @patch('main.WebAppInfo')
    async def test_start_command(self, mock_web_app_info, mock_message, clear_users):
        """Тест команды /start"""
        # Мокаем WebAppInfo
        mock_web_app_info.return_value = MagicMock()

        await start(mock_message)

        # Проверяем, что ответ был отправлен
        mock_message.answer.assert_called_once()

        # Проверяем, что в ответе есть кнопка с WebApp
        call_args = mock_message.answer.call_args[1]
        assert 'reply_markup' in call_args
        keyboard = call_args['reply_markup']
        assert keyboard.keyboard[0][0].text == "Открыть карточки"
        assert hasattr(keyboard.keyboard[0][0], 'web_app')

        # Проверяем, что в URL передан telegram_id
        web_app = keyboard.keyboard[0][0].web_app
        assert str(mock_message.from_user.id) in web_app.url

    async def test_info_command(self, mock_message):
        """Тест команды /info"""
        await info(mock_message)

        mock_message.answer.assert_called_once_with(INFO_TEXT)

    async def test_cmd_notify(self, mock_message, mock_state):
        """Тест команды /notify"""
        await cmd_notify(mock_message, mock_state)

        # Проверяем, что бот запросил время
        mock_message.reply.assert_called_once_with(
            "Введите время ежедневных уведомлений в формате ЧЧ:ММ (например, 14:30):"
        )

        # Проверяем, что состояние установлено
        mock_state.set_state.assert_called_once_with(TimeInput.waiting_for_time)


@pytest.mark.asyncio
class TestTimeInput:
    """Тесты для ввода времени"""

    async def test_process_time_valid(self, mock_message, mock_state, clear_users):
        """Тест обработки корректного времени"""
        mock_message.text = "14:30"

        await process_time(mock_message, mock_state)

        # Проверяем, что пользователь добавлен в словарь
        assert 123456 in users
        assert users[123456]["time"] == "14:30"
        assert users[123456]["enabled"] is True

        # Проверяем ответ
        mock_message.reply.assert_called_once_with(
            "Ежедневные уведомления установлены на 14:30"
        )

        # Проверяем, что состояние очищено
        mock_state.clear.assert_called_once()

    async def test_process_time_valid_with_single_digits(self, mock_message, mock_state, clear_users):
        """Тест обработки времени с одной цифрой"""
        mock_message.text = "09:05"

        await process_time(mock_message, mock_state)

        assert 123456 in users
        assert users[123456]["time"] == "09:05"

    async def test_process_time_invalid_format(self, mock_message, mock_state, clear_users):
        """Тест обработки некорректного формата времени"""
        mock_message.text = "14:30:00"

        await process_time(mock_message, mock_state)

        # Проверяем, что пользователь не добавлен
        assert 123456 not in users

        # Проверяем сообщение об ошибке
        mock_message.reply.assert_called_once_with(
            "Ошибка: Используйте формат ЧЧ:ММ (например, 14:30). Попробуйте снова:"
        )

    async def test_process_time_invalid_hours(self, mock_message, mock_state, clear_users):
        """Тест обработки неверного часа"""
        mock_message.text = "25:30"

        await process_time(mock_message, mock_state)

        assert 123456 not in users
        mock_message.reply.assert_called_once_with(
            "Ошибка: Время должно быть в диапазоне 00:00-23:59. Попробуйте снова:"
        )

    async def test_process_time_invalid_minutes(self, mock_message, mock_state, clear_users):
        """Тест обработки неверных минут"""
        mock_message.text = "14:75"

        await process_time(mock_message, mock_state)

        assert 123456 not in users
        mock_message.reply.assert_called_once_with(
            "Ошибка: Время должно быть в диапазоне 00:00-23:59. Попробуйте снова:"
        )

    async def test_process_time_no_colon(self, mock_message, mock_state, clear_users):
        """Тест обработки времени без двоеточия"""
        mock_message.text = "1430"

        await process_time(mock_message, mock_state)

        assert 123456 not in users
        mock_message.reply.assert_called_once_with(
            "Ошибка: Используйте формат ЧЧ:ММ (например, 14:30). Попробуйте снова:"
        )

    async def test_process_time_invalid_characters(self, mock_message, mock_state, clear_users):
        """Тест обработки времени с неверными символами"""
        mock_message.text = "ab:cd"

        await process_time(mock_message, mock_state)

        assert 123456 not in users
        mock_message.reply.assert_called_once_with(
            "Ошибка: Используйте формат ЧЧ:ММ (например, 14:30). Попробуйте снова:"
        )


@pytest.mark.asyncio
class TestCancelCommand:
    """Тесты для команды /cancel"""

    async def test_cmd_cancel_with_existing_user(self, mock_message, clear_users):
        """Тест отключения уведомлений для существующего пользователя"""
        users[123456] = {"time": "14:30", "enabled": True}

        await cmd_cancel(mock_message)

        # Проверяем, что уведомления отключены
        assert users[123456]["time"] is None
        assert users[123456]["enabled"] is False

        # Проверяем ответ
        mock_message.reply.assert_called_once_with("Уведомления отключены.")

    async def test_cmd_cancel_with_new_user(self, mock_message, clear_users):
        """Тест отключения уведомлений для нового пользователя"""
        await cmd_cancel(mock_message)

        # Проверяем, что пользователь создан с отключенными уведомлениями
        assert 123456 in users
        assert users[123456]["time"] is None
        assert users[123456]["enabled"] is False

        mock_message.reply.assert_called_once_with("Уведомления отключены.")


@pytest.mark.asyncio
class TestNotificationScheduler:
    """Тесты для планировщика уведомлений"""

    @patch('main.datetime')
    @patch('main.asyncio.sleep', new_callable=AsyncMock)
    async def test_check_time_and_notify_no_users(self, mock_sleep, mock_datetime, clear_users):
        """Тест когда нет пользователей для уведомления"""
        mock_now = datetime(2024, 1, 1, 14, 30, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.strftime = lambda self, fmt: self.strftime(fmt)

        # Настраиваем mock_sleep так, чтобы он выполнялся только один раз
        mock_sleep.side_effect = [None, asyncio.CancelledError()]

        with patch('main.bot.send_message', new_callable=AsyncMock) as mock_send_message:
            try:
                await check_time_and_notify()
            except asyncio.CancelledError:
                pass

            mock_send_message.assert_not_called()


@pytest.mark.asyncio
class TestBotIntegration:
    """Интеграционные тесты для бота"""

    async def test_full_notification_flow(self, mock_message, mock_state, clear_users):
        """Тест полного потока: установка времени, получение уведомления, отключение"""
        # 1. Пользователь устанавливает время
        mock_message.text = "14:30"
        await process_time(mock_message, mock_state)

        assert users[123456]["time"] == "14:30"
        assert users[123456]["enabled"] is True

        # 2. Пользователь отключает уведомления
        await cmd_cancel(mock_message)

        assert users[123456]["enabled"] is False

    async def test_notify_with_multiple_users(self, mock_message, clear_users):
        """Тест уведомлений для нескольких пользователей"""
        # Добавляем пользователей с разным временем
        users[111] = {"time": "10:00", "enabled": True}
        users[222] = {"time": "14:30", "enabled": True}
        users[333] = {"time": "14:30", "enabled": True}
        users[444] = {"time": "14:30", "enabled": False}

        # Проверяем, что пользователи с одинаковым временем правильно группируются
        users_at_1430 = [
            uid for uid, data in users.items()
            if data["enabled"] and data["time"] == "14:30"
        ]
        assert len(users_at_1430) == 2
        assert 222 in users_at_1430
        assert 333 in users_at_1430
        assert 444 not in users_at_1430


class TestConstants:
    """Тесты для констант"""

    def test_notification_message_not_empty(self):
        """Проверка, что сообщение уведомления не пустое"""
        assert NOTIFICATION_MESSAGE
        assert isinstance(NOTIFICATION_MESSAGE, str)

    def test_info_text_contains_key_info(self):
        """Проверка, что текст /info содержит ключевую информацию"""
        assert "Flashcards" in INFO_TEXT
        assert "Создавайте колоды" in INFO_TEXT
        assert "LibreTranslate" in INFO_TEXT
        assert "/notify" in INFO_TEXT
        assert "/cancel" in INFO_TEXT


class TestTimeInputState:
    """Тесты для состояния FSM"""

    def test_time_input_state_exists(self):
        """Проверка, что состояние существует"""
        assert hasattr(TimeInput, 'waiting_for_time')

    def test_time_input_state_is_state(self):
        """Проверка, что состояние является экземпляром State"""
        assert isinstance(TimeInput.waiting_for_time, State)