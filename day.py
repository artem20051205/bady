import asyncio
import logging
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message
from datetime import datetime, time, timedelta
from config import API_TOKEN

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

COMBINED_DATA_FILE = "data.json"

MENU_TEXT = "🍽️ Меню на день:\n1. Завтрак: Овсянка с фруктами\n2. Обед: Курица с рисом\n3. Ужин: Салат с тунцом"
WEIGHT_QUESTION = "⚖️ Какой у вас был вес сегодня вечером? Напиши число в кг."

# Функции для работы с данными
def load_data():
    try:
        with open(COMBINED_DATA_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_data(data):
    try:
        with open(COMBINED_DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        logging.error(f"Ошибка сохранения данных: {e}")

@dp.message(F.text == "/start")
async def start_handler(message: Message):
    data = load_data()
    user_id = str(message.chat.id)

    if user_id not in data:
        data[user_id] = {"name": f"User {user_id}", "weights": {}}
        save_data(data)
        await message.answer("🤖 Бот запущен! Теперь ты будешь получать ежедневное меню и вечерний запрос веса.")
    else:
        await message.answer("Ты уже зарегистрирован!")

@dp.message(F.text == "/weight")
async def weight_history_handler(message: Message):
    user_id = str(message.chat.id)
    data = load_data()

    if user_id in data and data[user_id]["weights"]:
        history = "\n".join([f"{date}: {weight} кг" for date, weight in data[user_id]["weights"].items()])
        await message.answer(f"📊 История твоего веса:\n{history}")
    else:
        await message.answer("❌ История веса пуста!")

async def send_menu():
    data = load_data()
    for user_id in data:
        try:
            await bot.send_message(user_id, MENU_TEXT)
        except Exception as e:
            logging.warning(f"Не удалось отправить сообщение пользователю {user_id}: {e}")

async def ask_weight():
    data = load_data()
    for user_id in data:
        try:
            await bot.send_message(user_id, WEIGHT_QUESTION)
        except Exception as e:
            logging.warning(f"Не удалось отправить сообщение пользователю {user_id}: {e}")

@dp.message(F.text.regexp(r"^\d+(\.\d+)?$"))
async def weight_handler(message: Message):
    user_id = str(message.chat.id)
    weight = message.text
    today = datetime.now().strftime("%Y-%m-%d")

    data = load_data()
    if user_id not in data:
        data[user_id] = {"name": f"User {user_id}", "weights": {}}
    
    data[user_id]["weights"][today] = weight
    save_data(data)

    await message.answer(f"✅ Вес {weight} кг сохранен на {today}!")

async def scheduler():
    while True:
        now = datetime.now()
        next_run = None
        
        if now.time() < time(8, 0):
            next_run = now.replace(hour=8, minute=0, second=0, microsecond=0)
        elif now.time() < time(20, 0):
            next_run = now.replace(hour=20, minute=0, second=0, microsecond=0)
        else:
            next_run = (now + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)

        delay = (next_run - now).total_seconds()
        logging.info(f"Следующее событие запланировано на {next_run} через {delay} секунд.")
        await asyncio.sleep(delay)

        if next_run.hour == 8:
            await send_menu()
        elif next_run.hour == 20:
            await ask_weight()

async def main():
    asyncio.create_task(scheduler())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
