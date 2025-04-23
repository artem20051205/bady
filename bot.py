import asyncio
import json
import logging
import os
from collections import defaultdict
from typing import Dict, Any, Optional
# <<< ДОДАНО: timedelta для розрахунку часу нагадування
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

API_TOKEN: str = config.API_TOKEN
CHANNEL_ID: int = config.CHANNEL_ID
MENU_TIME = time(12, 00) # Час надсилання меню
WEIGHT_TIME = time(18, 00) # Час запиту ваги
# <<< ДОДАНО: Час для надсилання нагадування (наприклад, через 2 години після запиту)
REMINDER_OFFSET_HOURS = 2
# Розраховуємо фактичний час нагадування
# Обережно з переходом через північ, але для вечірніх часів це працює:
REMINDER_TIME = time((WEIGHT_TIME.hour + REMINDER_OFFSET_HOURS) % 24, WEIGHT_TIME.minute)

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
RESULTS_IMAGE_PATH = "img/1.png" # Можливо, не використовується, але залишмо

SUPPORT_USERNAME = "@MRartemkaa"  # Replace with the actual username for support

bot: Bot = Bot(token=API_TOKEN)
dp: Dispatcher = Dispatcher()
router: Router = Router()

# <<< ЗМІНА: Використовуємо defaultdict(lambda: None) щоб легше перевіряти існування даних
user_weight_data: Dict[int, Optional[Dict[str, Any]]] = defaultdict(lambda: None)
# user_last_question_msg_id не використовується в поточному коді, можна прибрати або залишити для майбутнього
# user_last_question_msg_id: Dict[int, int] = defaultdict(int)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# --- Функції збереження/завантаження даних ---
def save_user_to_json(user_id: int, data: dict):
    """Save user data to a JSON file."""
    user_file = os.path.join(USER_DATA_DIR, f"{user_id}.json")
    try:
        with open(user_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"Дані користувача {user_id} збережено у файл {user_file}")
    except Exception as e:
        logging.error(f"Помилка збереження даних користувача {user_id} у файл {user_file}: {e}")

def load_user_from_json(user_id: int) -> Optional[dict]:
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
    return None # <<< ЗМІНА: Повертаємо None, якщо файлу немає або помилка

def load_all_users():
    """Load all user data from JSON files into memory."""
    logging.info("Завантаження даних усіх користувачів із файлів.")
    if not os.path.exists(USER_DATA_DIR):
        logging.warning(f"Директорія {USER_DATA_DIR} не існує.")
        return

    for filename in os.listdir(USER_DATA_DIR):
        if filename.endswith(".json"):
            try:
                user_id = int(filename.split(".")[0])
                user_data = load_user_from_json(user_id)
                if user_data: # <<< ЗМІНА: Перевіряємо, чи дані завантажились
                    # Переконуємося, що ключові поля існують
                    user_data.setdefault("weights", {})
                    user_data.setdefault("day", 1)
                    user_data.setdefault("finished", False)
                    user_data.setdefault("asked_today", False)
                    user_data.setdefault("menu_sent_today", False)
                    user_data.setdefault("last_entry_date", None) # <<< ДОДАНО: Зберігаємо дату останнього запису ваги
                    user_weight_data[user_id] = user_data
                    logging.info(f"Дані користувача {user_id} завантажено.")
            except ValueError:
                logging.error(f"Некоректне ім'я файлу: {filename}")
            except Exception as e:
                 logging.error(f"Помилка завантаження даних з файлу {filename}: {e}")

# <<< ЗМІНА: Функції save/load_user_data тепер працюють напряму з user_weight_data та файлом
async def save_user_data_to_file(user_id: int) -> None:
    """Save current in-memory user data to their JSON file."""
    if user_weight_data[user_id] is not None:
        save_user_to_json(user_id, user_weight_data[user_id])
    else:
        logging.warning(f"Спроба зберегти порожні дані для користувача {user_id}")

# load_user_data не потрібна, бо ми завантажуємо все на старті в user_weight_data

# --- Допоміжні функції ---
async def send_safe_message(user_id: int, text: str, **kwargs):
    try:
        await bot.send_message(user_id, text, **kwargs)
        return True # <<< ДОДАНО: Повертаємо успіх
    except TelegramAPIError as e:
        logging.error(f"Помилка надсилання повідомлення користувачу {user_id}: {e}")
        # <<< ДОДАНО: Обробка блокування бота користувачем
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
        return False # <<< ДОДАНО: Повертаємо неуспіх

async def is_user_subscribed(user_id: int) -> bool:
    # Ця функція залишається без змін
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in {ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR}
    except TelegramAPIError as e:
        logging.error(f"Помилка перевірки підписки користувача {user_id} в каналі {CHANNEL_ID}: {e}")
        return False
    except Exception as e:
        logging.error(f"Непередбачена помилка перевірки підписки {user_id}: {e}")
        return False

# --- Функції кнопок та меню ---
# Залишаються без змін: create_buttons, get_subscribe_button, get_main_menu

def create_buttons(buttons: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=text, callback_data=callback)] for text, callback in buttons]
    )

def get_subscribe_button() -> InlineKeyboardMarkup:
    channel_link = getattr(config, 'CHANNEL_LINK', "https://t.me/tteessttooss") # Припустимо, посилання є в config
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
                InlineKeyboardButton(text="📖 Меню та Вага", callback_data="start_weight"), # Змінено текст для ясності
                InlineKeyboardButton(text="📝 Пройти тест", callback_data="start_test")
            ],
            [
                InlineKeyboardButton(text="🎧 Зв'язок з нами", callback_data="call_center")
            ]
        ]
    )

# --- Обробники команд та колбеків ---

@router.callback_query(F.data == "call_center")
async def handle_call_center_callback(callback: types.CallbackQuery) -> None:
    """Handle the 'Contact Us' button."""
    await callback.message.answer(f"Для зв'язку з підтримкою напишіть: {SUPPORT_USERNAME}")
    await callback.answer()

@router.message(CommandStart())
async def send_welcome(message: types.Message) -> None:
    user_id = message.from_user.id
    logging.info(f"Користувач {user_id} ({message.from_user.full_name}) запустив бота.")
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
        await message.answer(
            text,
            reply_markup=markup
        )

@router.callback_query(F.data == "check_subscription")
async def handle_check_subscription_callback(callback: types.CallbackQuery) -> None:
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    # <<< ЗМІНА: Використовуємо edit_text обережно, може викликати помилку, якщо повідомлення старе
    try:
        await callback.message.edit_text("⏳ Перевіряю підписку...")
    except TelegramBadRequest as e:
        logging.warning(f"Не вдалося редагувати повідомлення для перевірки підписки {user_id}: {e}")
        # Надішлемо нове повідомлення, якщо редагування не вдалося
        await callback.message.answer("⏳ Перевіряю підписку...")

    if await is_user_subscribed(user_id):
        # <<< ЗМІНА: Надсилаємо головне меню після перевірки
        await callback.message.answer("✅ Ви підписані! Можете користуватись ботом.", reply_markup=get_main_menu())
        try: # Спробуємо видалити повідомлення "Перевіряю підписку..."
           await callback.message.delete()
        except TelegramAPIError: pass # Ігноруємо помилку, якщо не вдалося видалити
    else:
        await callback.message.answer( # <<< ЗМІНА: Надсилаємо нове повідомлення замість редагування
            "❌ Ви все ще не підписані.", reply_markup=get_subscribe_button())
    await callback.answer()

# async def send_results(user_id: int, chat_id: int) -> None: # Ця функція більше не потрібна тут
#     await send_safe_message(chat_id, "Оберіть дію:", reply_markup=get_main_menu())

@router.callback_query(F.data == "start_weight")
async def handle_start_weight_callback(callback: types.CallbackQuery) -> None:
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    global user_weight_data

    user_data = user_weight_data.get(user_id) # Використовуємо .get() для безпеки

    if user_data:
        if user_data.get("finished"):
            await callback.answer("✅ Ви вже завершили програму 'Меню та Вага'.", show_alert=True)
            await callback.message.answer("Оберіть іншу дію:", reply_markup=get_main_menu()) # <<< ДОДАНО: Покажемо меню знову
            return
        else:
            # Якщо користувач вже активний, просто покажемо меню/нагадування
            current_day = user_data.get("day", 1)
            logging.info(f"Користувач {user_id} (активний учасник, день {current_day}) натиснув кнопку 'Меню та Вага'.")
            # Можна надіслати поточне меню ще раз, якщо він просить
            await send_menu(user_id, current_day)
            # Перевіримо, чи треба запитати вагу (якщо ще не питали/не вводили сьогодні)
            today_str = datetime.now().strftime("%Y-%m-%d")
            if today_str not in user_data.get("weights", {}):
                 await ask_weight(user_id)
            else:
                 await send_safe_message(user_id, f"Вашу вагу на сьогодні ({today_str}) вже записано.")

            await callback.answer(f"Ви на Дні {current_day}. Меню надіслано.")
            return

    # Якщо користувач новий або дані відсутні
    logging.info(f"Користувач {user_id} запускає програму 'Меню та Вага' ({TOTAL_WEIGHT_TRACKING_DAYS} днів).")
    user_weight_data[user_id] = {
        "weights": {},
        "day": 1,
        "finished": False,
        "asked_today": False,
        "menu_sent_today": False,
        "last_entry_date": None # <<< ДОДАНО
    }
    await save_user_data_to_file(user_id) # <<< ЗМІНА: Зберігаємо дані у файл

    # Надсилаємо інструкції (краще новим повідомленням, ніж редагувати)
    await send_safe_message(user_id, WEIGHT_TRACKING_INSTRUCTIONS)

    # Надсилаємо перше меню та запитуємо вагу
    await send_menu(user_id, 1)
    user_weight_data[user_id]['menu_sent_today'] = True # Позначаємо, що меню за 1-й день надіслано
    await ask_weight(user_id)
    user_weight_data[user_id]['asked_today'] = True # Позначаємо, що вагу запитали
    await save_user_data_to_file(user_id) # <<< ЗМІНА: Зберігаємо оновлені дані

    await callback.answer()


async def send_menu(user_id: int, day: int) -> None:
    """Надсилає меню на вказаний день."""
    menu_text = MENUS.get(day)
    if menu_text:
        logging.info(f"Надсилання меню Дня {day}/{TOTAL_WEIGHT_TRACKING_DAYS} користувачу {user_id}")
        full_text = f"📅 *Меню на День {day}*\n\n{menu_text}"
        markup = None
        if day == 3: # Додаємо кнопку тесту на 3-й день
             markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📝 Пройти тест", callback_data="start_test")]])

        await send_safe_message(user_id, full_text, reply_markup=markup, parse_mode="Markdown")
    else:
        logging.warning(f"Меню для дня {day} не знайдено в color_data.MENUS!")
        await send_safe_message(user_id, f"⚠️ Не можу знайти меню для дня {day}. Будь ласка, зв'яжіться з адміністратором ({SUPPORT_USERNAME}).")

async def ask_weight(user_id: int) -> None:
    """Запитує вагу у користувача."""
    logging.info(f"Запит ваги у користувача {user_id}")
    await send_safe_message(user_id, WEIGHT_QUESTION)


@router.message(F.text.regexp(r'^\d+([.,]\d+)?$'))
async def handle_weight_input(message: types.Message):
    """Обробляє введення ваги користувачем."""
    user_id = message.from_user.id
    chat_id = message.chat.id
    global user_weight_data

    user_data = user_weight_data.get(user_id)

    # Ігноруємо, якщо користувач не бере участь у програмі або вже завершив
    if not user_data or user_data.get("finished"):
        # Можна відповісти, що програма не активна, або просто проігнорувати
        # await message.reply("Наразі програма 'Меню та Вага' для вас не активна.")
        logging.debug(f"Отримано вагу від {user_id}, але програма не активна або завершена.")
        return

    try:
        weight_str = message.text.replace(',', '.')
        weight = float(weight_str)
        if not (20 < weight < 300): # Проста валідація ваги
            raise ValueError("Нереальна вага")
    except ValueError:
        await message.reply("❌ Будь ласка, введіть вашу вагу коректним числом (наприклад, 75.5 або 75,5).")
        return

    # <<< ЗМІНА: Використовуємо поточний день програми з user_data
    current_day = user_data.get("day", 1)
    today_str = datetime.now().strftime("%Y-%m-%d") # Дата фактичного введення

    # <<< ЗМІНА: Записуємо вагу для поточного дня *програми*, а не календарного дня
    # Використовуємо комбінацію дня програми та дати введення, щоб уникнути перезапису,
    # якщо користувач вводить вагу за вчорашній день програми сьогодні.
    # Краще просто зберігати вагу за *календарною* датою, коли вона була введена.
    # Програма сама визначить, до якого дня програми це відноситься при переході дня.

    if today_str in user_data.get("weights", {}):
        await message.reply(f"⚠️ Вага на сьогодні ({today_str}) вже записана: {user_data['weights'][today_str]:.1f} кг.")
        return

    # Зберігаємо вагу
    user_data.setdefault("weights", {})[today_str] = weight
    user_data["last_entry_date"] = today_str # <<< ДОДАНО: Оновлюємо дату останнього запису
    # Позначаємо, що на *сьогоднішній календарний день* вагу введено (для логіки нагадувань)
    # Цей прапор asked_today скинеться опівночі планувальником
    user_data["asked_today"] = True # Можна вважати, що якщо ввів - то й питали

    logging.info(f"Користувач {user_id} ввів вагу {weight:.1f} кг за {today_str} (День програми {current_day}/{TOTAL_WEIGHT_TRACKING_DAYS})")
    await message.reply(f"✅ Вага {weight:.1f} кг збережена (День {current_day}/{TOTAL_WEIGHT_TRACKING_DAYS}). Дякую!")

    # Перевірка на завершення програми НЕ тут, а при переході дня у планувальнику!
    # Тут ми просто зберігаємо вагу. День програми збільшиться опівночі.

    # Зберігаємо оновлені дані користувача
    await save_user_data_to_file(user_id) # <<< ЗМІНА


# --- Планувальник ---
async def scheduler():
    logging.info("Планувальник запущено.")
    while True:
        now = datetime.now()
        current_time = now.time()
        today_str = now.strftime("%Y-%m-%d")

        # <<< ЗМІНА: Копіюємо ключі, щоб уникнути помилок при видаленні користувача під час ітерації
        active_user_ids = list(user_weight_data.keys())

        for user_id in active_user_ids:
            user_data = user_weight_data.get(user_id)

            # Пропускаємо, якщо даних немає або програма завершена
            if not user_data or user_data.get("finished"):
                continue

            current_day = user_data.get("day", 1)

            # --- Логіка опівночі: Перехід на новий день ---
            # <<< ЗМІНА: Запускаємо трохи після півночі (00:01), щоб уникнути race conditions
            if current_time.hour == 0 and current_time.minute == 1:
                # Перевіряємо, чи був запис ваги за попередній день програми
                last_day_date = user_data.get("last_entry_date")
                yesterday_str = (now - timedelta(days=1)).strftime("%Y-%m-%d")

                # Якщо останній запис був не вчора (або його не було), можливо, надіслати повідомлення?
                if last_day_date != yesterday_str and current_day > 1: # Не нагадуємо після першого дня
                     logging.warning(f"Користувач {user_id} не ввів вагу за попередній день програми (День {current_day-1}).")
                     # Можна надіслати повідомлення, але це може бути спамом.
                     # await send_safe_message(user_id, f"⚠️ Ви не ввели вагу за День {current_day-1}. Продовжуємо програму.")

                # Збільшуємо день програми
                next_day = current_day + 1
                logging.info(f"Північ для {user_id}. Перехід з Дня {current_day} на День {next_day}.")
                user_data['day'] = next_day
                user_data['menu_sent_today'] = False # Скидаємо прапор меню
                user_data['asked_today'] = False   # Скидаємо прапор запиту ваги

                # Перевірка на завершення програми після збільшення дня
                if next_day > TOTAL_WEIGHT_TRACKING_DAYS:
                    user_data["finished"] = True
                    logging.info(f"Користувач {user_id} завершив програму 'Меню та Вага' ({TOTAL_WEIGHT_TRACKING_DAYS} днів).")

                    all_weights_entries = sorted(user_data.get("weights", {}).items()) # Сортуємо за датою
                    if len(all_weights_entries) >= 1:
                        first_day_weight = all_weights_entries[0][1] # Вага першого запису
                        last_day_weight = all_weights_entries[-1][1] # Вага останнього запису
                        weight_diff = last_day_weight - first_day_weight
                        sign = "+" if weight_diff >= 0 else ""
                        num_days_participated = len(all_weights_entries)

                        # <<< ДОДАНО: Перевіряємо, чи вдалося надіслати повідомлення
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
                         # Якщо немає записів ваги, просто повідомляємо про завершення
                         await send_safe_message(user_id, "🎉 Програму 'Меню та Вага' завершено! Дякуємо за участь!")

                await save_user_data_to_file(user_id) # Зберігаємо зміни (новий день, статус finished)
                # Якщо програма завершена, більше нічого для цього користувача сьогодні не робимо
                if user_data.get("finished"):
                    continue # Переходимо до наступного користувача

            # --- Логіка надсилання Меню ---
            if current_time.hour == MENU_TIME.hour and current_time.minute == MENU_TIME.minute:
                if not user_data.get('menu_sent_today'):
                    logging.info(f"Планувальник: надсилання меню Дня {current_day} користувачу {user_id}")
                    await send_menu(user_id, current_day)
                    user_data['menu_sent_today'] = True
                    await save_user_data_to_file(user_id)

            # --- Логіка Запиту Ваги ---
            if current_time.hour == WEIGHT_TIME.hour and current_time.minute == WEIGHT_TIME.minute:
                 # Перевіряємо, чи вага за СЬОГОДНІШНЮ календарну дату ще не введена
                if today_str not in user_data.get("weights", {}):
                    if not user_data.get('asked_today'): # Запитуємо, тільки якщо ще не питали АБО користувач не ввів сам
                        logging.info(f"Планувальник: запит ваги у користувача {user_id}")
                        await ask_weight(user_id)
                        user_data['asked_today'] = True
                        await save_user_data_to_file(user_id)

            # --- Логіка Нагадування про Вагу ---
            # <<< ДОДАНО: Блок нагадування
            if current_time.hour == REMINDER_TIME.hour and current_time.minute == REMINDER_TIME.minute:
                 # Перевіряємо, чи вага за СЬОГОДНІШНЮ календарну дату ще не введена
                 if today_str not in user_data.get("weights", {}):
                     # Перевіряємо, чи ми взагалі ПИТАЛИ сьогодні (щоб не нагадувати, якщо не питали)
                     if user_data.get('asked_today'):
                         logging.info(f"Планувальник: надсилання нагадування про вагу користувачу {user_id}")
                         await send_safe_message(user_id, WEIGHT_REMINDER)
                         # Не скидаємо asked_today, бо нагадування не означає, що відповіли
                         # Не зберігаємо дані тут, бо нічого не змінилося в user_data

        # Пауза перед наступною перевіркою
        await asyncio.sleep(60)

# --- Функція повідомлення про запуск --- (залишається без змін)
async def notify_users_on_startup():
    """Notify all active users that the bot has started."""
    logging.info("Повідомлення всім активним користувачам про запуск бота.")
    active_user_ids = list(user_weight_data.keys())
    for user_id in active_user_ids:
        user_data = user_weight_data.get(user_id)
        if user_data and not user_data.get("finished"): # Повідомляємо тільки активних
            try:
                await send_safe_message(user_id, "🤖 Бот перезапущено! Ви можете продовжити користуватися функціоналом.")
                logging.info(f"Повідомлення про запуск надіслано активному користувачу {user_id}.")
            except Exception as e:
                logging.error(f"Не вдалося надіслати повідомлення про запуск користувачу {user_id}: {e}")

# --- Головна функція ---
async def main() -> None:
    # Load all user data into memory
    load_all_users() # Завантажуємо дані *перед* усім іншим

    dp.include_router(router)
    dp.include_router(test_router)  # Include the test router
    scheduler_task = asyncio.create_task(scheduler()) # Запускаємо планувальник у фоні
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Запуск бота в режимі опитування (polling)...")

    # Повідомляємо користувачів про запуск (після завантаження даних)
    await notify_users_on_startup()

    try:
        await dp.start_polling(bot)
    finally:
        logging.info("Зупинка бота...")
        scheduler_task.cancel() # Зупиняємо планувальник
        try:
            await scheduler_task
        except asyncio.CancelledError:
            logging.info("Планувальник успішно зупинено.")
        # <<< ДОДАНО: Збереження даних всіх користувачів при зупинці
        logging.info("Збереження даних всіх користувачів перед виходом...")
        for user_id in user_weight_data:
             await save_user_data_to_file(user_id)
        logging.info("Дані збережено.")
        await bot.session.close() # Закриваємо сесію бота
        logging.info("Бот зупинено.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот зупинено вручну (Ctrl+C)")
    except Exception as e:
        logging.error(f"Критична помилка під час виконання: {e}", exc_info=True)