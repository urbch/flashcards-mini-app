from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
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

@dp.message(Command("start"))
async def start(message: Message):
    logger.info(f"Received /start command from user: {message.from_user.id}")
    # Динамически добавляем telegram_id в URL
    web_app_url = f"https://dd3e-194-58-154-209.ngrok-free.app?telegram_id={message.from_user.id}"
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
        "Нажмите, чтобы открыть приложение:",
        reply_markup=keyboard
    )

async def main():
    logger.info("Starting bot polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())