import asyncio
import json
import logging
import os
from collections import defaultdict
from typing import Dict, Any, Optional
from datetime import datetime, time

import aiofiles
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.enums import ChatMemberStatus
from aiogram.filters import CommandStart, Command
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import config
from color_data import (
    color_dict, evaluation_criteria, color_to_system, evaluation_icons, MENUS
)
from test_handlers import router as test_router

API_TOKEN: str = config.API_TOKEN
CHANNEL_ID: int = config.CHANNEL_ID
MENU_TIME = time(8, 0)
WEIGHT_TIME = time(20, 0)
TOTAL_WEIGHT_TRACKING_DAYS = 7

USER_DATA_DIR = "user_data"

# Ensure the directory for user data exists
os.makedirs(USER_DATA_DIR, exist_ok=True)

WEIGHT_TRACKING_INSTRUCTIONS = (
    "📋 Програму 'Меню та Вага' запущено!\n\n"
    f"Я надсилатиму вам меню на день щоранку о {MENU_TIME.strftime('%H:%M')} "
    f"та запитуватиму вашу вагу щовечора о {WEIGHT_TIME.strftime('%H:%M')} "
    f"протягом {TOTAL_WEIGHT_TRACKING_DAYS} днів."
)
WEIGHT_QUESTION = "⚖️ Яка у вас сьогодні вага? Напишіть число в кг (наприклад, 75.5 або 75,5)."
WEIGHT_REMINDER = "⏰ Нагадую, будь ласка, введіть вашу сьогоднішню вагу."

WELCOME_IMAGE_PATH = "img/1.png"
RESULTS_IMAGE_PATH = "img/1.png"

SUPPORT_USERNAME = "@MRartemkaa"  # Replace with the actual username for support

bot: Bot = Bot(token=API_TOKEN)
dp: Dispatcher = Dispatcher()
router: Router = Router()

user_weight_data: Dict[int, Dict[str, Any]] = defaultdict(dict)
user_last_question_msg_id: Dict[int, int] = defaultdict(int)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

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

async def save_user_data(user_id: int, key: str, value: Any) -> None:
    """Save specific user data to their JSON file."""
    user_data = load_user_from_json(user_id)
    user_data[key] = value
    save_user_to_json(user_id, user_data)

async def load_user_data(user_id: int, key: str) -> Any:
    """Load specific user data from their JSON file."""
    user_data = load_user_from_json(user_id)
    return user_data.get(key)

async def send_safe_message(user_id: int, text: str, **kwargs):
    try:
        await bot.send_message(user_id, text, **kwargs)
    except TelegramAPIError as e:
        logging.error(f"Помилка надсилання повідомлення користувачу {user_id}: {e}")

async def is_user_subscribed(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in {ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR}
    except TelegramAPIError as e:
        logging.error(f"Помилка перевірки підписки користувача {user_id} в каналі {CHANNEL_ID}: {e}")
        return False
    except Exception as e:
        logging.error(f"Непередбачена помилка перевірки підписки {user_id}: {e}")
        return False


def create_buttons(buttons: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=text, callback_data=callback)] for text, callback in buttons]
    )

def get_subscribe_button() -> InlineKeyboardMarkup:
    channel_link = getattr(config, 'CHANNEL_LINK', "https://t.me/tteessttooss")
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔔 Підписатися", url=channel_link)],
            [InlineKeyboardButton(text="✅ Перевірити підписку", callback_data="check_subscription")]
        ]
    )

def get_main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📖 Меню", callback_data="start_weight"),
                InlineKeyboardButton(text="📝 Пройти тест", callback_data="start_test")
            ],
            [
                InlineKeyboardButton(text="🎧 Зв'язок з нами", callback_data="call_center")
            ]
        ]
    )

@router.callback_query(F.data == "call_center")
async def handle_call_center_callback(callback: types.CallbackQuery) -> None:
    """Handle the 'Contact Us' button."""
    await callback.message.answer(f"Для зв'язку з підтримкою напишіть: {SUPPORT_USERNAME}")
    await callback.answer()

@router.message(CommandStart())
async def send_welcome(message: types.Message) -> None:
    user_id = message.from_user.id
    logging.info(f"Користувач {user_id} ({message.from_user.full_name}) запустив бота.")
    # Скидаємо ID повідомлення з питанням, якщо користувач починає з /start
    user_last_question_msg_id[user_id] = 0
    caption = f"👋 Привіт, {message.from_user.full_name}! Оберіть дію:"
    try:
        photo = FSInputFile(WELCOME_IMAGE_PATH)
        await message.answer_photo(
            photo=photo,
            caption=caption,
            reply_markup=get_main_menu()
        )
    except Exception as e:
        logging.error(f"Не вдалося надіслати вітальне фото ({WELCOME_IMAGE_PATH}): {e}. Надсилання тексту.")
        await message.answer(
            caption,
            reply_markup=get_main_menu()
        )

@router.message(Command("mainmenu"))
async def handle_mainmenu_command(message: types.Message) -> None:
    user_id = message.from_user.id
    logging.info(f"Користувач {user_id} викликав команду /mainmenu.")
    
    text = "👋 Оберіть дію:"
    markup = get_main_menu()

    try:
        photo = FSInputFile(WELCOME_IMAGE_PATH)
        await message.answer_photo(
            photo=photo,
            caption=text,
            reply_markup=markup
        )
    except Exception as e:
        logging.error(f"Не вдалося надіслати вітальне фото ({WELCOME_IMAGE_PATH}): {e}. Надсилання тексту.")
        # If sending the photo fails, send only text with the markup
        await message.answer(
            text,
            reply_markup=markup
        )

@router.callback_query(F.data == "check_subscription")
async def handle_check_subscription_callback(callback: types.CallbackQuery) -> None:
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    await callback.message.edit_text("⏳ Перевіряю підписку...")
    if await is_user_subscribed(user_id):
        await callback.message.edit_text("✅ Ви підписані! Надсилаю результати...")
        await send_results(user_id, chat_id)
    else:
        await callback.message.edit_text(
            "❌ Ви все ще не підписані.", reply_markup=get_subscribe_button())
    await callback.answer()

async def send_results(user_id: int, chat_id: int) -> None:
    await send_safe_message(chat_id, "Оберіть дію:", reply_markup=get_main_menu())

@router.callback_query(F.data == "start_weight")
async def handle_start_weight_callback(callback: types.CallbackQuery) -> None:
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    global user_weight_data

    user_data = user_weight_data.get(user_id)

    if user_data:
        if user_data.get("finished"):
            await callback.answer("✅ Ви вже завершили програму 'Меню та Вага'.", show_alert=True)
            return
        else:
            current_day = user_data.get("day", 1)
            logging.info(f"Користувач {user_id} (активний учасник, день {current_day}) запросив меню.")
            await send_menu(user_id, current_day)
            await callback.answer(f"Надсилаю меню на День {current_day}.")
            return

    logging.info(f"Користувач {user_id} запускає програму 'Меню та Вага' ({TOTAL_WEIGHT_TRACKING_DAYS} днів).")
    user_weight_data[user_id] = {"weights": {}, "day": 1, "finished": False, "asked_today": False, "menu_sent_today": False}
    await save_user_data(user_id, "weight_data", user_weight_data[user_id])

    try:
        if callback.message.photo:
             await callback.message.edit_caption(caption=WEIGHT_TRACKING_INSTRUCTIONS, reply_markup=None)
        else:
             await callback.message.edit_text(WEIGHT_TRACKING_INSTRUCTIONS, reply_markup=None)
    except TelegramAPIError as e:
        logging.warning(f"Не вдалося відредагувати повідомлення при старті 'Меню та Вага' для {user_id}: {e}")
        await callback.message.answer(WEIGHT_TRACKING_INSTRUCTIONS)
        try: await callback.message.delete()
        except TelegramAPIError: pass

    await send_menu(user_id, 1)
    user_weight_data[user_id]['menu_sent_today'] = True
    await ask_weight(user_id)
    user_weight_data[user_id]['asked_today'] = True
    await save_user_data(user_id, "weight_data", user_weight_data[user_id])
    await callback.answer()

async def send_menu(user_id: int, day: int) -> None:
    menu_text = MENUS.get(day)
    if menu_text:
        logging.info(f"Надсилання меню Дня {day}/{TOTAL_WEIGHT_TRACKING_DAYS} користувачу {user_id}")
        if day == 3:
            markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=" Пройти тест", callback_data="start_test")]])
            full_text = f"️ *Меню на День {day}*\n\n{menu_text}"
            await send_safe_message(user_id, full_text, reply_markup=markup, parse_mode="Markdown")
        else:
            full_text = f"️ *Меню на День {day}*\n\n{menu_text}"
            await send_safe_message(user_id, full_text, parse_mode="Markdown")
    else:
        logging.warning(f"Меню для дня {day} не знайдено в color_data.MENUS!")
        await send_safe_message(user_id, f"⚠️ Не можу знайти меню для дня {day}. Будь ласка, зв'яжіться з адміністратором.")
async def ask_weight(user_id: int) -> None:

    logging.info(f"Запит ваги у користувача {user_id}")
    await send_safe_message(user_id, WEIGHT_QUESTION)


@router.message(F.text.regexp(r'^\d+([.,]\d+)?$'))
async def handle_weight_input(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    global user_weight_data

    if user_id not in user_weight_data or not user_weight_data[user_id] or user_weight_data[user_id].get("finished"):
        return

    try:
        weight_str = message.text.replace(',', '.')
        weight = float(weight_str)
        if not (20 < weight < 300):
            raise ValueError("Нереальна вага")
    except ValueError:
        await message.reply("❌ Будь ласка, введіть вашу вагу коректним числом (наприклад, 75.5 або 75,5).")
        return

    today_str = datetime.now().strftime("%Y-%m-%d")
    user_data = user_weight_data[user_id]

    if today_str in user_data.get("weights", {}):
        await message.reply(f"⚠️ Вага на сьогодні ({today_str}) вже записана: {user_data['weights'][today_str]:.1f} кг.")
        return

    # Save the weight for today
    user_data.setdefault("weights", {})[today_str] = weight
    user_data["asked_today"] = True  # Mark as asked for today
    current_day = user_data.get("day", 1)

    logging.info(f"Користувач {user_id} ввів вагу {weight:.1f} кг за {today_str} (День {current_day}/{TOTAL_WEIGHT_TRACKING_DAYS})")
    await message.reply(f"✅ Вага {weight:.1f} кг збережена (День {current_day}/{TOTAL_WEIGHT_TRACKING_DAYS}). Дякую!")

    # Check if the program is finished
    if current_day >= TOTAL_WEIGHT_TRACKING_DAYS:
        user_data["finished"] = True
        logging.info(f"Користувач {user_id} завершив програму 'Меню та Вага' ({TOTAL_WEIGHT_TRACKING_DAYS} днів).")
        all_weights = list(user_data["weights"].values())
        if len(all_weights) >= 1:
            first_day_weight = all_weights[0]
            last_day_weight = weight
            weight_diff = last_day_weight - first_day_weight
            sign = "+" if weight_diff >= 0 else ""
            num_days_participated = len(all_weights)
            await send_safe_message(chat_id, f"🎉 Програму 'Меню та Вага' завершено!\n📉 Ваш результат за {num_days_participated} дн.: {sign}{weight_diff:.1f} кг.\nДякуємо за участь!")
            await send_safe_message(chat_id, "Оберіть наступну дію:", reply_markup=get_main_menu())
        else:
            await send_safe_message(chat_id, "🎉 Програму 'Меню та Вага' завершено! Дякуємо за участь!")

    # Save updated user data
    await save_user_data(user_id, "weight_data", user_data)

async def scheduler():
    logging.info("Планувальник запущено.")
    while True:
        now = datetime.now(); current_time = now.time(); today_str = now.strftime("%Y-%m-%d")
        active_user_ids = list(user_weight_data.keys())
        for user_id in active_user_ids:

            user_data = user_weight_data.get(user_id)
            if not user_data or user_data.get("finished"): continue

            user_day = user_data.get("day", 1)

            if current_time.hour == 0 and current_time.minute == 1:
                if user_data.get('menu_sent_today') or user_data.get('asked_today'):
                     logging.debug(f"Скидання щоденних прапорців для {user_id}")
                     user_data['menu_sent_today'] = False; user_data['asked_today'] = False
                     await save_user_data(user_id, "weight_data", user_data)

            if current_time.hour == MENU_TIME.hour and current_time.minute == MENU_TIME.minute:
                if not user_data.get('menu_sent_today'):
                    if user_day <= TOTAL_WEIGHT_TRACKING_DAYS:
                        await send_menu(user_id, user_day)
                        user_data['menu_sent_today'] = True

                        if user_day < TOTAL_WEIGHT_TRACKING_DAYS:
                             user_data['day'] += 1
                             logging.info(f"Користувач {user_id} переведений на День {user_data['day']}")
                        await save_user_data(user_id, "weight_data", user_data)

            if current_time.hour == WEIGHT_TIME.hour and current_time.minute == WEIGHT_TIME.minute:

                if today_str not in user_data.get("weights", {}):
                     if not user_data.get('asked_today'):
                        await ask_weight(user_id)
                        user_data['asked_today'] = True
                        await save_user_data(user_id, "weight_data", user_data)

        await asyncio.sleep(60)

async def main() -> None:
    dp.include_router(router)
    dp.include_router(test_router)  # Include the test router
    asyncio.create_task(scheduler())
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Запуск бота в режимі опитування (polling)...")
    await dp.start_polling(bot)
    logging.info("Бот зупинено.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот зупинено вручну (Ctrl+C)")