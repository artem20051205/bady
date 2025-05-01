import asyncio
import json
import logging
import os
from collections import defaultdict
from typing import Dict, Any, Optional
from datetime import datetime, time, timedelta

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
from utils import save_user_to_json  # Ensure this is imported

API_TOKEN: str = config.API_TOKEN
CHANNEL_ID: int = config.CHANNEL_ID
MENU_TIME = time(12, 00)
WEIGHT_TIME = time(18, 00)
REMINDER_OFFSET_HOURS = 2
REMINDER_TIME = time((WEIGHT_TIME.hour + REMINDER_OFFSET_HOURS) % 24, WEIGHT_TIME.minute)

TOTAL_WEIGHT_TRACKING_DAYS = 7

USER_DATA_DIR = "user_data"

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

SUPPORT_USERNAME = "@MRartemkaa"

bot: Bot = Bot(token=API_TOKEN)
dp: Dispatcher = Dispatcher()
router: Router = Router()

user_weight_data: Dict[int, Optional[Dict[str, Any]]] = defaultdict(lambda: None)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def save_user_to_json(user_id: int, data: dict):
    user_file = os.path.join(USER_DATA_DIR, f"{user_id}.json")
    try:
        with open(user_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"Дані користувача {user_id} збережено у файл {user_file}")
    except Exception as e:
        logging.error(f"Помилка збереження даних користувача {user_id} у файл {user_file}: {e}")

def load_user_from_json(user_id: int) -> Optional[dict]:
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

def load_all_users():
    logging.info("Завантаження даних усіх користувачів із файлів.")
    if not os.path.exists(USER_DATA_DIR):
        logging.warning(f"Директорія {USER_DATA_DIR} не існує.")
        return

    for filename in os.listdir(USER_DATA_DIR):
        if filename.endswith(".json"):
            try:
                user_id = int(filename.split(".")[0])
                user_data = load_user_from_json(user_id)
                user_weight_data[user_id] = user_data
                logging.info(f"Дані користувача {user_id} завантажено.")
            except ValueError:
                logging.error(f"Некоректне ім'я файлу: {filename}")
            except Exception as e:
                logging.error(f"Помилка завантаження даних з файлу {filename}: {e}")

async def send_safe_message(user_id: int, text: str, **kwargs):
    try:
        await bot.send_message(user_id, text, **kwargs)
        return True
    except TelegramAPIError as e:
        logging.error(f"Помилка надсилання повідомлення користувачу {user_id}: {e}")
        if "bot was blocked by the user" in str(e) or "user is deactivated" in str(e):
            logging.warning(f"Користувач {user_id} заблокував бота або деактивований. Видалення даних.")
            if user_id in user_weight_data:
                del user_weight_data[user_id]
            user_file = os.path.join(USER_DATA_DIR, f"{user_id}.json")
            if os.path.exists(user_file):
                try:
                    os.remove(user_file)
                    logging.info(f"Файл даних для {user_id} видалено.")
                except OSError as rm_err:
                    logging.error(f"Не вдалося видалити файл даних для {user_id}: {rm_err}")
        return False

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
                InlineKeyboardButton(text="📖 Меню та Вага", callback_data="start_weight"),
                InlineKeyboardButton(text="📝 Пройти тест", callback_data="start_test")
            ],
            [
                InlineKeyboardButton(text="🎧 Зв'язок з нами", callback_data="call_center")
            ]
        ]
    )

@router.callback_query(F.data == "call_center")
async def handle_call_center_callback(callback: types.CallbackQuery) -> None:
    await callback.message.answer(f"Для зв'язку з підтримкою напишіть: {SUPPORT_USERNAME}")
    await callback.answer()

@router.message(CommandStart())
async def send_welcome(message: types.Message) -> None:
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    logging.info(f"Користувач {user_id} ({full_name}) запустив бота.")

    user_data = load_user_from_json(user_id)
    user_data["full_name"] = full_name
    save_user_to_json(user_id, user_data)

    caption = f"👋 Привіт, {full_name}! Оберіть дію:"
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
        await message.answer(
            text,
            reply_markup=markup
        )

@router.callback_query(F.data == "check_subscription")
async def handle_check_subscription_callback(callback: types.CallbackQuery) -> None:
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    try:
        await callback.message.edit_text("⏳ Перевіряю підписку...")
    except TelegramBadRequest as e:
        logging.warning(f"Не вдалося редагувати повідомлення для перевірки підписки {user_id}: {e}")
        await callback.message.answer("⏳ Перевіряю підписку...")

    if await is_user_subscribed(user_id):
        await callback.message.answer("✅ Ви підписані! Можете користуватись ботом.", reply_markup=get_main_menu())
        try:
           await callback.message.delete()
        except TelegramAPIError: pass
    else:
        await callback.message.answer(
            "❌ Ви все ще не підписані.", reply_markup=get_subscribe_button())
    await callback.answer()

@router.callback_query(F.data == "start_weight")
async def handle_start_weight_callback(callback: types.CallbackQuery) -> None:
    user_id = callback.from_user.id
    user_data = load_user_from_json(user_id)

    if user_data.get("finished"):
        await callback.answer("✅ Ви вже завершили програму 'Меню та Вага'.", show_alert=True)
        await callback.message.answer("Оберіть іншу дію:", reply_markup=get_main_menu())
        return

    if "weights" not in user_data:
        user_data.update({
            "weights": {},
            "day": 1,
            "finished": False,
            "asked_today": False,
            "menu_sent_today": False,
            "last_entry_date": None
        })
        save_user_to_json(user_id, user_data)

    current_day = user_data.get("day", 1)
    today_str = datetime.now().strftime("%Y-%m-%d")

    if today_str not in user_data["weights"]:
        await ask_weight(user_id)
        user_data["asked_today"] = True
        save_user_to_json(user_id, user_data)

    await send_menu(user_id, current_day)
    user_data["menu_sent_today"] = True
    save_user_to_json(user_id, user_data)

    await callback.answer(f"Ви на Дні {current_day}. Меню надіслано.")

async def send_menu(user_id: int, day: int) -> bool:
    image_filename = f"m{day}.png"
    image_path = os.path.join("img", image_filename)

    caption = f"📅 Меню на День {day+1}"
    markup = None
    if day == 3:
        markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📝 Пройти тест", callback_data="start_test")]])

    photo_sent = False
    if os.path.exists(image_path):
        logging.info(f"Надсилання меню-фото {image_filename} (День {day}/{TOTAL_WEIGHT_TRACKING_DAYS}) користувачу {user_id}")
        try:
            photo_to_send = FSInputFile(image_path)
            await bot.send_photo(
                chat_id=user_id,
                photo=photo_to_send,
                caption=caption,
                reply_markup=markup
            )
            photo_sent = True
        except TelegramAPIError as e:
            logging.error(f"Помилка API при надсиланні фото-меню {image_path} користувачу {user_id}: {e}")
            if "bot was blocked by the user" in str(e) or "user is deactivated" in str(e):
                logging.warning(f"Користувач {user_id} заблокував бота або деактивований. Видалення даних.")
                if user_id in user_weight_data:
                    del user_weight_data[user_id]
                user_file = os.path.join(USER_DATA_DIR, f"{user_id}.json")
                if os.path.exists(user_file):
                    try:
                        os.remove(user_file)
                        logging.info(f"Файл даних для {user_id} видалено.")
                    except OSError as rm_err:
                        logging.error(f"Не вдалося видалити файл даних для {user_id}: {rm_err}")
                return False
        except Exception as e:
            logging.error(f"Несподівана помилка при надсиланні фото-меню {image_path} користувачу {user_id}: {e}")

    if not photo_sent:
        menu_text = MENUS.get(day)
        if menu_text:
            logging.info(f"Надсилання текстового меню (Fallback) Дня {day}/{TOTAL_WEIGHT_TRACKING_DAYS} користувачу {user_id}")
            fallback_note = ""
            if os.path.exists(image_path):
                fallback_note = "\n\n_(Не вдалося завантажити зображення меню)_"

            full_text = f"{caption}\n\n{menu_text}{fallback_note}"
            return await send_safe_message(user_id, full_text, reply_markup=markup, parse_mode="Markdown")
        else:
            logging.error(f"Ні зображення ({image_path}), ні тексту в MENUS для дня {day} не знайдено!")
            error_message = f"⚠️ Не можу знайти меню для дня {day}. Будь ласка, зв'яжіться з адміністратором ({SUPPORT_USERNAME})."
            await send_safe_message(user_id, error_message)
            return False

async def ask_weight(user_id: int) -> None:
    logging.info(f"Запит ваги у користувача {user_id}")
    await send_safe_message(user_id, WEIGHT_QUESTION)

@router.message(F.text.regexp(r'^\d+([.,]\d+)?$'))
async def handle_weight_input(message: types.Message):
    user_id = message.from_user.id
    user_data = load_user_from_json(user_id)

    if user_data.get("finished"):
        return

    try:
        weight = float(message.text.replace(',', '.'))
        if not (20 < weight < 300):
            raise ValueError("Нереальна вага")
    except ValueError:
        await message.reply("❌ Будь ласка, введіть вашу вагу коректним числом (наприклад, 75.5 або 75,5).")
        return

    today_str = datetime.now().strftime("%Y-%m-%d")
    if today_str in user_data["weights"]:
        await message.reply(f"⚠️ Вага на сьогодні ({today_str}) вже записана: {user_data['weights'][today_str]:.1f} кг.")
        return

    user_data["weights"][today_str] = weight
    user_data["last_entry_date"] = today_str
    user_data["asked_today"] = True
    save_user_to_json(user_id, user_data)

    await message.reply(f"✅ Вага {weight:.1f} кг збережена. Дякую!")

async def scheduler():
    logging.info("Планувальник запущено.")
    while True:
        now = datetime.now()
        current_time = now.time()
        today_str = now.strftime("%Y-%m-%d")

        active_user_ids = list(user_weight_data.keys())

        for user_id in active_user_ids:
            user_data = user_weight_data.get(user_id)

            if not user_data or user_data.get("finished"):
                continue

            current_day = user_data.get("day", 1)

            if current_time.hour == 0 and current_time.minute == 1:
                last_day_date = user_data.get("last_entry_date")
                yesterday_str = (now - timedelta(days=1)).strftime("%Y-%m-%d")

                if last_day_date != yesterday_str and current_day > 1:
                    logging.warning(f"Користувач {user_id} не ввів вагу за попередній день програми (День {current_day-1}).")

                next_day = current_day + 1
                logging.info(f"Північ для {user_id}. Перехід з Дня {current_day} на День {next_day}.")
                user_data['day'] = next_day
                user_data['menu_sent_today'] = False
                user_data['asked_today'] = False

                if next_day > TOTAL_WEIGHT_TRACKING_DAYS:
                    user_data["finished"] = True
                    logging.info(f"Користувач {user_id} завершив програму 'Меню та Вага' ({TOTAL_WEIGHT_TRACKING_DAYS} днів).")

                    all_weights_entries = sorted(user_data.get("weights", {}).items())
                    if len(all_weights_entries) >= 1:
                        first_day_weight = all_weights_entries[0][1]
                        last_day_weight = all_weights_entries[-1][1]
                        weight_diff = last_day_weight - first_day_weight
                        sign = "+" if weight_diff >= 0 else ""
                        num_days_participated = len(all_weights_entries)

                        success = await send_safe_message(
                            user_id,
                            f"🎉 Програму 'Меню та Вага' завершено!\n"
                            f"📉 Ваш результат за {num_days_participated} дн. (з {TOTAL_WEIGHT_TRACKING_DAYS}): {sign}{weight_diff:.1f} кг.\n"
                            f"(Перша вага: {first_day_weight:.1f} кг, Остання: {last_day_weight:.1f} кг)\n\n"
                            f"Дякуємо за участь!"
                        )
                        if success:
                            await send_safe_message(user_id, "Оберіть наступну дію:", reply_markup=get_main_menu())

                    else:
                        await send_safe_message(user_id, "🎉 Програму 'Меню та Вага' завершено! Дякуємо за участь!")

                save_user_to_json(user_id, user_data)
                if user_data.get("finished"):
                    continue

            if current_time.hour == MENU_TIME.hour and current_time.minute == MENU_TIME.minute:
                if not user_data.get('menu_sent_today'):
                    logging.info(f"Планувальник: надсилання меню Дня {current_day} користувачу {user_id}")
                    await send_menu(user_id, current_day)
                    user_data['menu_sent_today'] = True
                    save_user_to_json(user_id, user_data)

            if current_time.hour == WEIGHT_TIME.hour and current_time.minute == WEIGHT_TIME.minute:
                if today_str not in user_data.get("weights", {}):
                    if not user_data.get('asked_today'):
                        logging.info(f"Планувальник: запит ваги у користувача {user_id}")
                        await ask_weight(user_id)
                        user_data['asked_today'] = True
                        save_user_to_json(user_id, user_data)

            if current_time.hour == REMINDER_TIME.hour and current_time.minute == REMINDER_TIME.minute:
                if today_str not in user_data.get("weights", {}):
                    if user_data.get('asked_today'):
                        logging.info(f"Планувальник: надсилання нагадування про вагу користувачу {user_id}")
                        await send_safe_message(user_id, WEIGHT_REMINDER)

        await asyncio.sleep(60)

async def notify_users_on_startup():
    logging.info("Повідомлення всім активним користувачам про запуск бота.")
    active_user_ids = list(user_weight_data.keys())
    for user_id in active_user_ids:
        user_data = user_weight_data.get(user_id)
        if user_data and not user_data.get("finished"):
            try:
                await send_safe_message(user_id, "🤖 Бот перезапущено! Ви можете продовжити користуватися функціоналом.")
                logging.info(f"Повідомлення про запуск надіслано активному користувачу {user_id}.")
            except Exception as e:
                logging.error(f"Не вдалося надіслати повідомлення про запуск користувачу {user_id}: {e}")

async def main() -> None:
    load_all_users()

    dp.include_router(router)
    dp.include_router(test_router)
    scheduler_task = asyncio.create_task(scheduler())
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Запуск бота в режимі опитування (polling)...")

    await notify_users_on_startup()

    try:
        await dp.start_polling(bot)
    finally:
        logging.info("Зупинка бота...")
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            logging.info("Планувальник успішно зупинено.")
        logging.info("Збереження даних всіх користувачів перед виходом...")
        for user_id in user_weight_data:
            save_user_to_json(user_id, user_weight_data[user_id])
        logging.info("Дані збережено.")
        await bot.session.close()
        logging.info("Бот зупинено.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот зупинено вручну (Ctrl+C)")
    except Exception as e:
        logging.error(f"Критична помилка під час виконання: {e}", exc_info=True)