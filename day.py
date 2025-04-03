import asyncio
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message
from aiogram.exceptions import TelegramAPIError
from datetime import datetime, time
from config import API_TOKEN
from color_data import MENUS

dp = Dispatcher()
bot = Bot(token=API_TOKEN)

COMBINED_DATA_FILE = "data.json"

# Настройки времени
MENU_TIME = time(8, 49)  # 08:31
WEIGHT_TIME = time(8, 52)  # 08:38

INSTRUCTIONS = "📋 Инструкции: Бот будет отправлять меню на следующий день утром и запрашивать вес вечером."
WEIGHT_QUESTION = "⚖️ Какой у вас вес? Напишите число в кг."

# Используем lock для синхронизации работы с JSON файлом
json_lock = asyncio.Lock()

async def load_data():
    async with json_lock:
        try:
            with open(COMBINED_DATA_FILE, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            return {}

async def save_data(data):
    async with json_lock:
        try:
            with open(COMBINED_DATA_FILE, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            pass

async def send_message(user_id, text):
    try:
        await bot.send_message(user_id, text)
    except TelegramAPIError as e:
        await bot.send_message(user_id, "❌ Произошла ошибка при отправке сообщения, попробуйте позже.")

async def start_handler(message: Message):
    user_id = str(message.chat.id)
    data = await load_data()

    if user_id not in data:
        data[user_id] = {"name": f"User {user_id}", "weights": {}, "day": 1, "finished": False}
        await save_data(data)
        await send_message(user_id, INSTRUCTIONS)
    elif data[user_id].get("finished"):
        await send_message(user_id, "✅ Ты уже завершил участие!")
        return

    await ask_weight(user_id)
    await send_menu(user_id, 1)

async def send_menu(user_id, day):
    if day in MENUS:
        await send_message(user_id, MENUS[day])

async def ask_weight(user_id):
    await send_message(user_id, WEIGHT_QUESTION)

async def weight_handler(message: Message):
    user_id = str(message.chat.id)
    weight = message.text
    today = datetime.now().strftime("%Y-%m-%d")

    data = await load_data()
    if user_id not in data or data[user_id].get("finished"):
        return

    if today in data[user_id]["weights"]:
        await send_message(user_id, "⚠️ Вес уже записан сегодня!")
        return

    data[user_id]["weights"][today] = weight
    await save_data(data)
    await send_message(user_id, f"✅ Вес {weight} кг сохранен на {today}!")

    if data[user_id]["day"] < 3:
        data[user_id]["day"] += 1
        await save_data(data)
    else:
        first_day_weight = float(list(data[user_id]["weights"].values())[0])
        last_day_weight = float(weight)
        weight_diff = last_day_weight - first_day_weight
        await send_message(user_id, f"📉 Разница в весе с первым днем: {weight_diff:.1f} кг. Спасибо за участие!")
        data[user_id]["finished"] = True
        await save_data(data)

async def scheduler():
    while True:
        now = datetime.now().time()
        data = await load_data()
        for user_id in list(data.keys()):
            if data[user_id].get("finished"):
                continue
            user_day = data[user_id].get("day", 1)
            last_weight_date = max(data[user_id]["weights"].keys(), default="")
            today = datetime.now().strftime("%Y-%m-%d")
            if last_weight_date != today and user_day > 1:
                await send_message(user_id, "⚠️ Напоминаем, что нужно ввести вес, прежде чем продолжать!")
                continue
            if now.hour == MENU_TIME.hour and now.minute == MENU_TIME.minute and user_day <= 3:
                await send_menu(user_id, user_day)
            if now.hour == WEIGHT_TIME.hour and now.minute == WEIGHT_TIME.minute:
                await ask_weight(user_id)
        await asyncio.sleep(30)

async def main():
    asyncio.create_task(scheduler())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
