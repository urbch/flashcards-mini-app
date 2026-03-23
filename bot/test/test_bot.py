import asyncio
import os
import sys
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.fsm.state import State

# Добавляем путь к корню проекта
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from main import (
    INFO_TEXT,
    NOTIFICATION_MESSAGE,
    TimeInput,
    check_time_and_notify,
    cmd_cancel,
    cmd_notify,
    info,
    process_time,
    start,
    users,
)


# =========================
# Fixtures
# =========================

@pytest.fixture
def mock_message():
    """Мок aiogram Message."""
    message = AsyncMock()
    message.chat.id = 123456
    message.from_user.id = 123456
    message.text = ""
    message.answer = AsyncMock()
    message.reply = AsyncMock()
    return message


@pytest.fixture
def mock_state():
    """Мок FSMContext."""
    state = AsyncMock()
    state.set_state = AsyncMock()
    state.clear = AsyncMock()
    return state


@pytest.fixture
def clear_users():
    """Очищает глобальный словарь пользователей до и после теста."""
    users.clear()
    yield
    users.clear()


# =========================
# Helpers
# =========================

def assert_invalid_time_response(mock_message):
    mock_message.reply.assert_called_once_with(
        "Ошибка: Используйте формат ЧЧ:ММ (например, 14:30). Попробуйте снова:"
    )


def assert_out_of_range_time_response(mock_message):
    mock_message.reply.assert_called_once_with(
        "Ошибка: Время должно быть в диапазоне 00:00-23:59. Попробуйте снова:"
    )


# =========================
# Command handlers
# =========================

@pytest.mark.asyncio
class TestBotCommands:
    """Юнит-тесты обработчиков команд."""

    async def test_start_returns_webapp_button_with_telegram_id(self, mock_message, clear_users):
        """Команда /start отправляет клавиатуру с кнопкой WebApp и telegram_id в URL."""
        await start(mock_message)

        mock_message.answer.assert_called_once()

        call_kwargs = mock_message.answer.call_args.kwargs
        assert "reply_markup" in call_kwargs

        keyboard = call_kwargs["reply_markup"]
        button = keyboard.keyboard[0][0]

        assert button.text == "Открыть карточки"
        assert hasattr(button, "web_app")
        assert str(mock_message.from_user.id) in button.web_app.url

    async def test_info_returns_info_text(self, mock_message):
        """Команда /info возвращает информационный текст."""
        await info(mock_message)

        mock_message.answer.assert_called_once_with(INFO_TEXT)

    async def test_cmd_notify_requests_time_and_sets_state(self, mock_message, mock_state):
        """Команда /notify должна запросить время и установить FSM-состояние."""
        await cmd_notify(mock_message, mock_state)

        mock_message.reply.assert_called_once_with(
            "Введите время ежедневных уведомлений в формате ЧЧ:ММ (например, 14:30):"
        )
        mock_state.set_state.assert_called_once_with(TimeInput.waiting_for_time)


# =========================
# Time input processing
# =========================

@pytest.mark.asyncio
class TestTimeInput:
    """Юнит-тесты обработки ввода времени."""

    async def test_process_time_accepts_valid_time(self, mock_message, mock_state, clear_users):
        """Корректное время должно сохраняться для пользователя."""
        mock_message.text = "14:30"

        await process_time(mock_message, mock_state)

        assert 123456 in users
        assert users[123456]["time"] == "14:30"
        assert users[123456]["enabled"] is True

        mock_message.reply.assert_called_once_with(
            "Ежедневные уведомления установлены на 14:30"
        )
        mock_state.clear.assert_called_once()

    async def test_process_time_accepts_valid_time_with_leading_zeroes(
            self, mock_message, mock_state, clear_users
    ):
        """Корректное время с ведущими нулями также должно сохраняться."""
        mock_message.text = "09:05"

        await process_time(mock_message, mock_state)

        assert 123456 in users
        assert users[123456]["time"] == "09:05"
        assert users[123456]["enabled"] is True

    async def test_process_time_handles_value_error_after_regex_match(
            self, mock_message, mock_state, clear_users
    ):
        """Если после успешной regex-проверки возникает ValueError, должен вернуться корректный ответ."""
        mock_message.text = "14:30abc"

        with patch("main.re.match", return_value=MagicMock()):
            with patch("builtins.map", side_effect=ValueError):
                await process_time(mock_message, mock_state)

        assert 123456 not in users
        mock_message.reply.assert_called_once_with(
            "Ошибка: Некорректный формат времени. Используйте ЧЧ:ММ (например, 14:30):"
        )
        mock_state.clear.assert_not_called()

    async def test_process_time_rejects_invalid_format_with_seconds(
            self, mock_message, mock_state, clear_users
    ):
        """Формат HH:MM:SS должен отклоняться."""
        mock_message.text = "14:30:00"

        await process_time(mock_message, mock_state)

        assert 123456 not in users
        assert_invalid_time_response(mock_message)
        mock_state.clear.assert_not_called()

    async def test_process_time_rejects_invalid_hours(self, mock_message, mock_state, clear_users):
        """Часы вне диапазона 00-23 должны отклоняться."""
        mock_message.text = "25:30"

        await process_time(mock_message, mock_state)

        assert 123456 not in users
        assert_out_of_range_time_response(mock_message)
        mock_state.clear.assert_not_called()

    async def test_process_time_rejects_invalid_minutes(self, mock_message, mock_state, clear_users):
        """Минуты вне диапазона 00-59 должны отклоняться."""
        mock_message.text = "14:75"

        await process_time(mock_message, mock_state)

        assert 123456 not in users
        assert_out_of_range_time_response(mock_message)
        mock_state.clear.assert_not_called()

    async def test_process_time_rejects_input_without_colon(
            self, mock_message, mock_state, clear_users
    ):
        """Строка без двоеточия должна отклоняться."""
        mock_message.text = "1430"

        await process_time(mock_message, mock_state)

        assert 123456 not in users
        assert_invalid_time_response(mock_message)
        mock_state.clear.assert_not_called()

    async def test_process_time_rejects_non_numeric_input(
            self, mock_message, mock_state, clear_users
    ):
        """Небуквенно-числовой мусор должен отклоняться."""
        mock_message.text = "ab:cd"

        await process_time(mock_message, mock_state)

        assert 123456 not in users
        assert_invalid_time_response(mock_message)
        mock_state.clear.assert_not_called()


# =========================
# Cancel command
# =========================

@pytest.mark.asyncio
class TestCancelCommand:
    """Юнит-тесты команды /cancel."""

    async def test_cmd_cancel_disables_notifications_for_existing_user(
            self, mock_message, clear_users
    ):
        """Для существующего пользователя уведомления должны отключаться."""
        users[123456] = {"time": "14:30", "enabled": True}

        await cmd_cancel(mock_message)

        assert users[123456]["time"] is None
        assert users[123456]["enabled"] is False
        mock_message.reply.assert_called_once_with("Уведомления отключены.")

    async def test_cmd_cancel_creates_disabled_user_for_new_user(
            self, mock_message, clear_users
    ):
        """Для нового пользователя должна создаваться запись с отключенными уведомлениями."""
        await cmd_cancel(mock_message)

        assert 123456 in users
        assert users[123456]["time"] is None
        assert users[123456]["enabled"] is False
        mock_message.reply.assert_called_once_with("Уведомления отключены.")


# =========================
# Notification scheduler
# =========================

@pytest.mark.asyncio
class TestNotificationScheduler:
    """Юнит-тесты логики планировщика уведомлений."""

    @patch("main.asyncio.sleep", new_callable=AsyncMock)
    @patch("main.datetime")
    async def test_check_time_and_notify_skips_when_no_users(
            self, mock_datetime, mock_sleep, clear_users
    ):
        """Если пользователей нет, уведомления не отправляются."""
        mock_now = datetime(2024, 1, 1, 14, 30, 0)
        mock_datetime.now.return_value = mock_now
        mock_sleep.side_effect = [None, asyncio.CancelledError()]

        with patch("main.bot.send_message", new_callable=AsyncMock) as mock_send_message:
            with pytest.raises(asyncio.CancelledError):
                await check_time_and_notify()

        mock_send_message.assert_not_called()

    @patch("main.asyncio.sleep", new_callable=AsyncMock)
    @patch("main.datetime")
    async def test_check_time_and_notify_sends_only_to_matching_enabled_users(
            self, mock_datetime, mock_sleep, clear_users
    ):
        """Уведомления отправляются только пользователям с подходящим временем и enabled=True."""
        mock_now = MagicMock()
        mock_now.strftime.return_value = "14:30"
        mock_datetime.now.return_value = mock_now
        mock_sleep.return_value = None

        users[111] = {"time": "10:00", "enabled": True}
        users[222] = {"time": "14:30", "enabled": True}
        users[333] = {"time": "14:30", "enabled": True}
        users[444] = {"time": "14:30", "enabled": False}

        sent_ids = []

        async def stop_after_two_sends(*args, **kwargs):
            if args:
                sent_ids.append(args[0])
            elif "chat_id" in kwargs:
                sent_ids.append(kwargs["chat_id"])

            if len(sent_ids) >= 2:
                raise asyncio.CancelledError()

        with patch("main.bot.send_message", new_callable=AsyncMock) as mock_send_message:
            mock_send_message.side_effect = stop_after_two_sends

            with pytest.raises(asyncio.CancelledError):
                await check_time_and_notify()

        assert mock_send_message.await_count == 2
        assert sent_ids == [222, 333]

    @patch("main.asyncio.sleep", new_callable=AsyncMock)
    @patch("main.datetime")
    async def test_check_time_and_notify_logs_successful_send(
            self, mock_datetime, mock_sleep, clear_users
    ):
        """Успешная отправка уведомления должна логироваться."""
        mock_now = MagicMock()
        mock_now.strftime.return_value = "14:30"
        mock_datetime.now.return_value = mock_now
        mock_sleep.side_effect = [None, asyncio.CancelledError()]

        users[123456] = {"time": "14:30", "enabled": True}

        with patch("main.bot.send_message", new_callable=AsyncMock):
            with patch("main.logger") as mock_logger:
                with pytest.raises(asyncio.CancelledError):
                    await check_time_and_notify()

        mock_logger.info.assert_any_call(
            "Уведомление отправлено для 123456 в 14:30"
        )


# =========================
# State and constants
# =========================

class TestConstants:
    """Юнит-тесты констант."""

    def test_notification_message_is_not_empty_string(self):
        """Текст уведомления должен быть непустой строкой."""
        assert NOTIFICATION_MESSAGE
        assert isinstance(NOTIFICATION_MESSAGE, str)

    def test_info_text_contains_key_commands_and_features(self):
        """Текст /info должен содержать ключевые сведения о боте."""
        assert "Flashcards" in INFO_TEXT
        assert "Создавайте колоды" in INFO_TEXT
        assert "LibreTranslate" in INFO_TEXT
        assert "/notify" in INFO_TEXT
        assert "/cancel" in INFO_TEXT


class TestTimeInputState:
    """Юнит-тесты FSM-состояния."""

    def test_time_input_state_exists(self):
        """Состояние waiting_for_time должно существовать."""
        assert hasattr(TimeInput, "waiting_for_time")

    def test_time_input_state_is_aiogram_state(self):
        """waiting_for_time должен быть экземпляром aiogram State."""
        assert isinstance(TimeInput.waiting_for_time, State)


# =========================
# Pure state logic checks
# =========================

class TestUsersStateLogic:
    """Юнит-тесты вспомогательной логики состояния users."""

    def test_users_can_be_filtered_by_time_and_enabled_flag(self, clear_users):
        """Локальная логика отбора пользователей по времени должна работать предсказуемо."""
        users[111] = {"time": "10:00", "enabled": True}
        users[222] = {"time": "14:30", "enabled": True}
        users[333] = {"time": "14:30", "enabled": True}
        users[444] = {"time": "14:30", "enabled": False}

        users_at_1430 = [
            user_id
            for user_id, data in users.items()
            if data["enabled"] and data["time"] == "14:30"
        ]

        assert len(users_at_1430) == 2
        assert 222 in users_at_1430
        assert 333 in users_at_1430
        assert 444 not in users_at_1430

    @pytest.mark.asyncio
    async def test_full_user_state_flow_via_handlers(self, mock_message, mock_state, clear_users):
        """Последовательный unit-сценарий: установка времени и последующее отключение уведомлений."""
        mock_message.text = "14:30"

        await process_time(mock_message, mock_state)

        assert users[123456]["time"] == "14:30"
        assert users[123456]["enabled"] is True

        await cmd_cancel(mock_message)

        assert users[123456]["time"] is None
        assert users[123456]["enabled"] is False