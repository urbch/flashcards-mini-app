from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.types import Message, WebAppInfo
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
import asyncio
from dotenv import load_dotenv
import os
import logging
import pytz
import re

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables")

bot = Bot(token=TOKEN)
dp = Dispatcher()

users = {}

NOTIFICATION_MESSAGE = "Привет! Время повторить твои карточки!"
# Текст описания для команды /info
INFO_TEXT = """
Наше приложение Flashcards поможет вам быстро и эффективно запомнить учебный материал! 📚 Создавайте колоды с карточками, изучайте их и закрепляйте знания.

🌐 Хотите изучать английский язык? Создайте языковую колоду! Выберите исходный и целевой язык (английский → русский или русский → английский), введите слово, а перевод добавится автоматически через LibreTranslate.

Как начать:
1️⃣ Нажмите «Открыть карточки», чтобы запустить приложение
2️⃣ Нажмите «Создать колоду» и выберите название.
3️⃣ Для языковой колоды отметьте ✅ "Языковая колода" и выберите языки.
4️⃣ Добавляйте карточки и изучайте свайпами: вправо — знаю, влево — повторить.

Хочтите поставить себе напоминание? 
/notify - задать или изменить время для напоминаний.
/cancel - отменить заданные напоминания.
Бот будет присылать Вам уведомление каждый день в заданное время!

Учитесь легко и с удовольствием! 🚀
"""

class TimeInput(StatesGroup):
    waiting_for_time = State()

@dp.message(Command("start"))
async def start(message: Message):
    logger.info(f"Received /start command from user: {message.from_user.id}")
    # Динамически добавляем telegram_id в URL
    web_app_url = f"https://flashcardsapp.ru?telegram_id={message.from_user.id}"
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(
                text="Открыть карточки",
                web_app=WebAppInfo(url=web_app_url)
            )]
        ],
        resize_keyboard=True
    )
    await message.answer(
        'Напишите /info, чтобы узнать о нашем приложении.\nНажмите «Открыть карточки», чтобы запустить приложение:',
        reply_markup=keyboard
    )

@dp.message(Command("info"))
async def info(message: Message):
    logger.info(f"Received /info command from user: {message.from_user.id}")
    await message.answer(INFO_TEXT)

@dp.message(Command("notify"))
async def cmd_notify(message: types.Message, state: FSMContext):
    await message.reply("Введите время ежедневных уведомлений в формате ЧЧ:ММ (например, 14:30):")
    await state.set_state(TimeInput.waiting_for_time)

@dp.message(TimeInput.waiting_for_time)
async def process_time(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    time_str = message.text

    if re.match(r'^\d{2}:\d{2}$', time_str):
        try:
            hours, minutes = map(int, time_str.split(':'))
            if 0 <= hours <= 23 and 0 <= minutes <= 59:
                users[chat_id] = {
                    "time": time_str,
                    "enabled": True
                }
                await message.reply(f"Ежедневные уведомления установлены на {time_str}")
                await state.clear()
            else:
                await message.reply("Ошибка: Время должно быть в диапазоне 00:00-23:59. Попробуйте снова:")
        except ValueError:
            await message.reply("Ошибка: Некорректный формат времени. Используйте ЧЧ:ММ (например, 14:30):")
    else:
        await message.reply("Ошибка: Используйте формат ЧЧ:ММ (например, 14:30). Попробуйте снова:")

@dp.message(Command("cancel"))
async def cmd_cancel(message: types.Message):
    chat_id = message.chat.id
    users[chat_id] = {"time": None, "enabled": False}
    await message.reply("Уведомления отключены.")

async def check_time_and_notify():
    while True:
        now = datetime.now(pytz.timezone('Europe/Moscow'))
        current_time = now.strftime("%H:%M")

        users_to_notify = [
            chat_id for chat_id, user_data in users.items()
            if user_data["enabled"] and user_data["time"] == current_time
        ]

        if users_to_notify:
            for chat_id in users_to_notify:
                try:
                    await bot.send_message(chat_id=chat_id, text=NOTIFICATION_MESSAGE)
                    logger.info(f"Уведомление отправлено для {chat_id} в {current_time}")
                except Exception as e:
                    logger.info(f"Ошибка при отправке уведомления для {chat_id}: {e}")
            await asyncio.sleep(60)
        else:
            await asyncio.sleep(10)

async def main():
    asyncio.create_task(check_time_and_notify())
    logger.info("Starting bot polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())