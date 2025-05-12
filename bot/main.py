from aiogram import Bot, Dispatcher, types
from aiogram.types import WebAppInfo
from aiogram.utils import executor

bot = Bot(token="8016651500:AAHWvpf5S51rAOO68KMMAVZsWHBFBXU0H9M")
dp = Dispatcher(bot)

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    web_app = types.WebAppInfo(url="http://localhost:3000")  # URL фронтенда
    button = types.KeyboardButton("Открыть карточки", web_app=web_app)
    keyboard.add(button)
    await message.answer("Нажмите, чтобы открыть приложение:", reply_markup=keyboard)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)