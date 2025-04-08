import os
import json
import logging
from aiogram.exceptions import TelegramAPIError
from aiogram import Bot

USER_DATA_DIR = "user_data"

# Ensure the directory for user data exists
os.makedirs(USER_DATA_DIR, exist_ok=True)

def save_user_to_json(user_id: int, data: dict):
    """Save user data to a JSON file."""
    user_file = os.path.join(USER_DATA_DIR, f"{user_id}.json")
    try:
        with open(user_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"Дані користувача {user_id} збережено у файл {user_file}")
    except Exception as e:
        logging.error(f"Помилка збереження даних користувача {user_id} у файл {user_file}: {e}")

def load_user_from_json(user_id: int) -> dict:
    """Load user data from a JSON file."""
    user_file = os.path.join(USER_DATA_DIR, f"{user_id}.json")
    if os.path.exists(user_file):
        try:
            with open(user_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            logging.info(f"Дані користувача {user_id} завантажено з файлу {user_file}")
            return data
        except Exception as e:
            logging.error(f"Помилка завантаження даних користувача {user_id} з файлу {user_file}: {e}")
    return {}

async def save_user_data(user_id: int, key: str, value: any) -> None:
    """Save specific user data to their JSON file."""
    user_data = load_user_from_json(user_id)
    user_data[key] = value
    save_user_to_json(user_id, user_data)

async def send_safe_message(bot: Bot, user_id: int, text: str, **kwargs):
    """Send a message to a user safely, handling errors."""
    try:
        await bot.send_message(user_id, text, **kwargs)
    except TelegramAPIError as e:
        logging.error(f"Помилка надсилання повідомлення користувачу {user_id}: {e}")