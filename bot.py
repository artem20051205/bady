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

API_TOKEN = config.API_TOKEN
CHANNEL_ID = config.CHANNEL_ID
DATA_FILE = config.DATA_FILE
PHOTO_PATH = config.PHOTO_PATH


# Логирование
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
router = Router()
dp = Dispatcher()

# Загрузка данных пользователей из файла

def load_user_data():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logging.error(f"Ошибка загрузки данных: {e}")
    return {'scores': {}, 'progress': {}}

def save_user_data(data):
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.error(f"Ошибка сохранения данных: {e}")

# Инициализация данных пользователей
user_data = load_user_data()
user_scores = defaultdict(lambda: {color: 0 for color in list(color_dict.values())[0]}, user_data.get('scores', {}))
user_progress = defaultdict(int, user_data.get('progress', {}))

# Функция обновления данных пользователей
def update_user_data():
    save_user_data({'scores': dict(user_scores), 'progress': dict(user_progress)})

# Генерация кнопок

def get_answer_buttons(question_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Так", callback_data=f"yes_{question_id}")],
        [InlineKeyboardButton(text="❌ Ні", callback_data=f"no_{question_id}")],
        [InlineKeyboardButton(text="⏭ Пропустити", callback_data=f"skip_{question_id}")]
    ])

def get_subscribe_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔔 Підписатися", url=f"https://t.me/{CHANNEL_ID}")],
        [InlineKeyboardButton(text="✅ Перевірити підписку", callback_data="check_subscription")]
    ])

def get_start_test_buttons():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Так", callback_data="start_test")],
        [InlineKeyboardButton(text="❌ Ні", callback_data="cancel_start")]
    ])

# Кнопки для начала нового теста
def get_restart_test_buttons():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Так, почати заново", callback_data="restart_test")],
        [InlineKeyboardButton(text="❌ Ні", callback_data="cancel_restart")]
    ])

@router.message(CommandStart())
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_progress and user_progress[user_id] > 0:
        await message.answer("Ви вже проходили тест. Хочете пройти ще раз?", reply_markup=get_restart_test_buttons())
    else:
        await message.answer("Ви хочете пройти тест?", reply_markup=get_start_test_buttons())

# Обработка перезапуска теста
@router.callback_query(lambda c: c.data == "restart_test")
async def restart_test(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_scores[user_id] = {color: 0 for color in list(color_dict.values())[0]}
    user_progress[user_id] = 0
    update_user_data()
    
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
    update_user_data()
    
    # Изменяем сообщение, а не удаляем
    await callback_query.message.edit_text("Починаємо тест! Ось перше питання:")
    await send_next_question(user_id, callback_query.message)

async def send_next_question(user_id, message):
    question_id = user_progress[user_id]
    if question_id < len(color_dict):
        question_text = list(color_dict.keys())[question_id]
        
        # Изменяем сообщение с новым вопросом
        await message.edit_text(
            f"Питання {question_id + 1}: {question_text}",
            reply_markup=get_answer_buttons(question_id)
        )
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
    update_user_data()
    
    # Обновляем сообщение с новым вопросом
    await send_next_question(user_id, callback_query.message)

async def check_subscription(user_id, message):
    try:
        chat_member = await bot.get_chat_member(f"@{CHANNEL_ID}", user_id)
        if chat_member.status not in ["left", "kicked"]:
            await send_results(user_id, message)  # Передаем message для редактирования
        else:
            await message.edit_text(
                "❌ Щоб побачити результати, підпишіться на канал:",
                reply_markup=get_subscribe_button()
            )
    except Exception as e:
        logging.error(f"Помилка перевірки підписки: {e}")
        await message.edit_text(
            "❌ Щоб побачити результати, підпишіться на канал:",
            reply_markup=get_subscribe_button()
        )

@router.callback_query(lambda c: c.data == "check_subscription")
async def check_subscription_callback(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
    await check_subscription(callback_query.from_user.id)

# Функция отправки результатов пользователю
async def send_results(user_id, message):
    scores = user_scores.get(user_id, {})
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    result_text = "⬇️ *Ваші результати:*\n"
    for color, score in sorted_scores:
        evaluation = evaluate_color_score(color, score)  # Получаем текстовую оценку
        system_name = color_to_system.get(color, "Невідома система")
        icon = evaluation_icons.get(evaluation, "⚪")  # Получаем цветную иконку
        
        result_text += f"{icon} {system_name}: {evaluation}\n"  # Формируем строку результата
    
    try:
        photo = FSInputFile(PHOTO_PATH)
        await bot.send_photo(user_id, photo, caption=result_text.strip(), parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Ошибка отправки фото: {e}")
        await message.edit_text(result_text.strip(), parse_mode="Markdown")

# Функция для оценки результатов по цвету
def evaluate_color_score(color, score):
    for threshold, evaluation in evaluation_criteria[color]:
        if score <= threshold:
            return evaluation

# Запуск бота
async def main():
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
