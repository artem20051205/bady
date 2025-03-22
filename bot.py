import logging
import asyncio
import json
import os
from collections import defaultdict
from aiogram import Bot, Dispatcher, types, Router
from aiogram.enums import ChatMemberStatus
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.filters import CommandStart
from color_data import color_dict, evaluation_criteria, color_to_system, evaluation_icons
import config
import aiofiles

# Константы и переменные
API_TOKEN = config.API_TOKEN
CHANNEL_ID = config.CHANNEL_ID
DATA_FILE = config.DATA_FILE
PHOTO_PATH = config.PHOTO_PATH
data_lock = asyncio.Lock()

# Логирование
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
router = Router()
dp = Dispatcher()

# Глобальные переменные для хранения данных пользователей
user_data = {}
user_scores = defaultdict(lambda: {color: 0 for color in list(color_dict.values())[0]})
user_progress = defaultdict(int)

# Функции для работы с данными
async def load_user_data():
    async with data_lock:
        if os.path.exists(DATA_FILE):
            try:
                async with aiofiles.open(DATA_FILE, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    return json.loads(content) if content else {'scores': {}, 'progress': {}}
            except Exception as e:
                logging.error(f"Ошибка загрузки данных: {e}")
    return {'scores': {}, 'progress': {}}

async def save_user_data(data):
    async with data_lock:
        try:
            async with aiofiles.open(DATA_FILE, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, ensure_ascii=False, indent=4))
        except Exception as e:
            logging.error(f"Ошибка сохранения данных: {e}")

async def init_user_data():
    global user_data, user_scores, user_progress
    user_data = await load_user_data()
    user_scores = defaultdict(lambda: {color: 0 for color in list(color_dict.values())[0]}, user_data.get('scores', {}))
    user_progress = defaultdict(int, user_data.get('progress', {}))

async def update_user_data():
    asyncio.create_task(save_user_data({'scores': dict(user_scores), 'progress': dict(user_progress)}))

# Проверка подписки
async def is_user_subscribed(user_id: int) -> bool:
    try:
        chat_member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return chat_member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]
    except Exception as e:
        logging.error(f"Ошибка проверки подписки: {e}")
        return False

# Генерация кнопок
def get_answer_buttons(question_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Так", callback_data=f"yes_{question_id}")],
        [InlineKeyboardButton(text="❌ Ні", callback_data=f"no_{question_id}")],
        [InlineKeyboardButton(text="⏭ Пропустити", callback_data=f"skip_{question_id}")]
    ])

def get_subscribe_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔔 Підписатися", url=f"https://t.me/tteessttooss")],
        [InlineKeyboardButton(text="✅ Перевірити підписку", callback_data="check_subscription")]
    ])

def get_start_test_buttons():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Так", callback_data="start_test")],
        [InlineKeyboardButton(text="❌ Ні", callback_data="cancel_start")]
    ])

def get_restart_test_buttons():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Так, почати заново", callback_data="restart_test")],
        [InlineKeyboardButton(text="❌ Ні", callback_data="cancel_restart")]
    ])

# Обработчики команд
@router.message(CommandStart())
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_progress and user_progress[user_id] > 0:
        await message.answer("Ви вже проходили тест. Хочете пройти ще раз?", reply_markup=get_restart_test_buttons())
    else:
        await message.answer("Ви хочете пройти тест?", reply_markup=get_start_test_buttons())

@router.callback_query(lambda c: c.data == "restart_test")
async def restart_test(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_scores[user_id] = {color: 0 for color in list(color_dict.values())[0]}
    user_progress[user_id] = 0
    await update_user_data()

    await callback_query.message.edit_text("Починаємо тест заново! Ось перше питання:")
    await send_next_question(user_id, callback_query.message)

@router.callback_query(lambda c: c.data == "cancel_restart")
async def cancel_restart(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text("Добре! Якщо передумаєте, просто напишіть /start")

@router.callback_query(lambda c: c.data == "start_test")
async def start_test(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_scores[user_id] = {color: 0 for color in list(color_dict.values())[0]}
    user_progress[user_id] = 0
    await update_user_data()

    await callback_query.message.edit_text("Починаємо тест! Ось перше питання:")
    await send_next_question(user_id, callback_query.message)

async def send_next_question(user_id, message):
    question_id = user_progress[user_id]
    if question_id < len(color_dict):
        question_text = list(color_dict.keys())[question_id]
        await message.edit_text(f"Питання {question_id + 1}: {question_text}", reply_markup=get_answer_buttons(question_id))
    else:
        await check_subscription(user_id, message)

@router.callback_query(lambda c: c.data.startswith(('yes_', 'no_', 'skip_')))
async def handle_answer(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    answer_type, question_id = callback_query.data.split('_')
    question_id = int(question_id)

    if answer_type == "yes":
        for color, value in color_dict[list(color_dict.keys())[question_id]].items():
            user_scores[user_id][color] += value

    user_progress[user_id] += 1
    await update_user_data()
    
    await send_next_question(user_id, callback_query.message)

async def check_subscription(user_id, message):
    if await is_user_subscribed(user_id):
        await send_results(user_id, message)
    else:
        await message.edit_text("❌ Щоб побачити результати, підпишіться на канал:", reply_markup=get_subscribe_button())

@router.callback_query(lambda c: c.data == "check_subscription")
async def check_subscription_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    is_subscribed = await is_user_subscribed(user_id)

    if is_subscribed:
        await callback_query.message.answer("✅ Ви підписані! Ось ваші результати:")
        await send_results(user_id, callback_query.message)
    else:
        await callback_query.message.edit_text(
            "❌ Щоб побачити результати, підпишіться на канал:", 
            reply_markup=get_subscribe_button()
        )

    # Проверяем, изменилось ли сообщение перед обновлением
    if callback_query.message.text != new_text:
        await callback_query.message.edit_text(new_text, reply_markup=new_markup)
    else:
        await callback_query.answer("Повідомлення вже актуальне!", show_alert=True)

async def send_results(user_id, message):
    scores = user_scores.get(user_id, {})
    
    if not scores:
        await message.answer("⚠️ Виникла помилка! Не вдалося отримати ваші результати.")
        logging.error(f"❌ Помилка: результати для {user_id} відсутні в user_scores.")
        return

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    result_text = "⬇️ *Ваші результати:*\n"
    for color, score in sorted_scores:
        evaluation = evaluate_color_score(color, score)
        system_name = color_to_system.get(color, "Невідома система")
        icon = evaluation_icons.get(evaluation, "⚪")
        result_text += f"{icon} *{system_name}:* {evaluation}\n"

    # Отправляем новое сообщение вместо редактирования
    try:
        await message.answer(result_text.strip(), parse_mode="Markdown")
        logging.info(f"✅ Успішно відправлені результати для {user_id}")
    except Exception as e:
        logging.error(f"❌ Помилка надсилання результатів: {e}")

def evaluate_color_score(color, score):
    for threshold, evaluation in evaluation_criteria[color]:
        if score <= threshold:
            return evaluation

async def main():
    await init_user_data()
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
