from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, WebAppInfo
import asyncio
from dotenv import load_dotenv
import os

# Загружаем переменные из .env
load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")  # Токен из .env
WEBAPP_URL = os.getenv("WEBAPP_URL")  # URL из .env

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: Message):
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(
                text="Открыть карточки",
                web_app=WebAppInfo(url=WEBAPP_URL)  # Используем переменную
            )]
        ],
        resize_keyboard=True
    )
    await message.answer(
        "Нажмите, чтобы открыть приложение:",
        reply_markup=keyboard
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
