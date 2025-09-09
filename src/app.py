import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, executor, types
from modules.avatar import AvatarModule
from modules.shop import ShopModule
from modules.rag import RAGModule

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

avatar = AvatarModule()
shop   = ShopModule()
rag    = RAGModule()

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🛍 Каталог", "📚 FAQ", "💬 Помощь")
    await message.answer("Выбери раздел:", reply_markup=kb)

@dp.message_handler(lambda m: m.text == "🛍 Каталог")
async def show_catalog(message: types.Message):
    text = shop.get_catalog()
    await message.answer(text)

@dp.message_handler(lambda m: m.text == "📚 FAQ")
async def faq(message: types.Message):
    await message.answer("Задай вопрос — я найду ответ с цитатой.")

@dp.message_handler(lambda m: m.text == "💬 Помощь")
async def help(message: types.Message):
    await message.answer("Опиши проблему — помогу.")

@dp.message_handler()
async def any_text(message: types.Message):
    # простой роутинг: если вопрос — RAG, иначе аватар
    if "?" in message.text:
        answer = rag.ask(message.text)
        await message.answer(answer)
    else:
        answer = avatar.chat(message.text)
        await message.answer(answer)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
