from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.types import Message, WebAppInfo
import asyncio
from dotenv import load_dotenv
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Текст описания для команды /info
INFO_TEXT = """
Наше приложение Flashcards поможет вам быстро и эффективно запомнить учебный материал! 📚 Создавайте колоды с карточками, изучайте их и закрепляйте знания.

🌐 Хотите изучать иностранные языки? Создайте языковую колоду! Выберите исходный и целевой язык (например, английский → испанский), введите слово, а перевод добавится автоматически через LibreTranslate. Доступные языки: английский, русский, испанский, французский, немецкий, китайский и японский.

Как начать:
1️⃣ Нажмите «Открыть карточки», чтобы запустить приложение
2️⃣ Нажмите «Создать колоду» и выберите название.
3️⃣ Для языковой колоды отметьте 🌐 и выберите языки.
4️⃣ Добавляйте карточки и изучайте свайпами: вправо — знаю, влево — повторить.

Учитесь легко и с удовольствием! 🚀
"""

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

async def main():
    logger.info("Starting bot polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
