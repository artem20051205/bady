import logging
import asyncio
import json
import os
from collections import defaultdict
from aiogram import Bot, Dispatcher, types, Router
from aiogram.enums import ChatMemberStatus
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram import F

from color_data import color_dict

API_TOKEN = "7244256073:AAHO41bWchf_6ZvJHWGN_6A_JydJFc826l4"
CHANNEL_ID = "@tteessttooss"

# Путь к файлу, в котором будут храниться данные
DATA_FILE = 'user_data.json'

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
router = Router()
dp = Dispatcher()

# Загрузка данных пользователей из файла
def load_user_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# Сохранение данных пользователей в файл
def save_user_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Загружаем данные пользователей из файла
user_scores = load_user_data().get('scores', defaultdict(lambda: {color: 0 for color in next(iter(color_dict.values()))}))
user_progress = load_user_data().get('progress', defaultdict(int))

# Генерация инлайн-кнопок для ответов
def get_answer_buttons(question_id):
    buttons = [
        [InlineKeyboardButton(text="✅ Да", callback_data=f"yes_{question_id}")],
        [InlineKeyboardButton(text="❌ Нет", callback_data=f"no_{question_id}")],
        [InlineKeyboardButton(text="⏭ Пропустить", callback_data=f"skip_{question_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Кнопка подписки
def get_subscribe_button():
    return InlineKeyboardMarkup(inline_keyboard=[ 
        [InlineKeyboardButton(text="🔔 Подписаться", url=f"https://t.me/{CHANNEL_ID[1:]}")],
        [InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_subscription")]
    ])

# Функция для сброса данных пользователя
def reset_user_data(user_id):
    user_scores[user_id] = {color: 0 for color in next(iter(color_dict.values()))}
    user_progress[user_id] = 0
    update_user_data()

# Обработчик команды /start
@router.message(CommandStart())
async def send_welcome(message: types.Message):
    if message.from_user.id in user_scores:  # Если пользователь уже есть в данных
        buttons = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Перепройти тест", callback_data="restart_test")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_restart")]
        ])
        await message.answer("Вы уже проходили тест. Хотите пройти его заново?", reply_markup=buttons)
    else:
        user_scores[message.from_user.id] = {color: 0 for color in next(iter(color_dict.values()))}
        user_progress[message.from_user.id] = 0
        update_user_data()  # Сохраняем данные после инициализации
        await message.answer("Привет! Давай пройдем тест. Нажимай на кнопки под вопросами.")
        await send_next_question(message.from_user.id)

# Функция отправки вопросов
async def send_next_question(user_id):
    question_id = user_progress[user_id]
    if question_id < len(color_dict):
        question_text = list(color_dict.keys())[question_id]
        logging.debug(f"Отправляю вопрос {question_id + 1} пользователю {user_id}")
        await bot.send_message(user_id, f"Вопрос {question_id + 1}: {question_text}", reply_markup=get_answer_buttons(question_id))
    else:
        await check_subscription(user_id)

# Обработчик инлайн-кнопок с ответами
@router.callback_query(F.data.startswith(('yes_', 'no_', 'skip_')))
async def handle_answer(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    answer_type, question_id = callback_query.data.split('_')
    question_id = int(question_id)

    if answer_type == "yes":
        for color, value in color_dict[list(color_dict.keys())[question_id]].items():
            user_scores[user_id][color] += value

    user_progress[user_id] += 1
    update_user_data()  # Сохраняем данные после изменений
    await callback_query.message.delete()
    await send_next_question(user_id)

# Проверка подписки перед показом результатов
async def check_subscription(user_id):
    try:
        chat_member = await bot.get_chat_member(CHANNEL_ID, user_id)
        if chat_member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR]:
            await send_results(user_id)
        else:
            await bot.send_message(user_id, f"❌ Чтобы увидеть результаты, подпишитесь на канал: {CHANNEL_ID}", reply_markup=get_subscribe_button())
    except Exception as e:
        logging.error(f"Ошибка проверки подписки: {e}")
        await bot.send_message(user_id, f"⚠ Ошибка: {e}\n\nПроверь, что бот является администратором в канале!")

# Проверка подписки по кнопке
@router.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    await callback_query.message.delete()
    await check_subscription(user_id)

# Обработчик инлайн-кнопок для перезапуска теста
@router.callback_query(F.data == "restart_test")
async def restart_test(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    reset_user_data(user_id)
    await callback_query.message.delete()
    await callback_query.message.answer("Давай пройдем тест заново. Нажимай на кнопки под вопросами.")
    await send_next_question(user_id)

# Обработчик инлайн-кнопок для отмены перезапуска теста
@router.callback_query(F.data == "cancel_restart")
async def cancel_restart(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
    await callback_query.message.answer("Хорошо, продолжаем с текущими результатами.")

# Критерии оценки для каждого цвета
evaluation_criteria = {
    "yellow": [(2, "очень хорошо"), (4, "хорошо"), (9, "удовлетворительно"), (float('inf'), "неудовлетворительно")],
    "green": [(2, "очень хорошо"), (4, "хорошо"), (9, "удовлетворительно"), (float('inf'), "неудовлетворительно")],
    "cyan": [(2, "очень хорошо"), (3, "хорошо"), (7, "удовлетворительно"), (float('inf'), "неудовлетворительно")],
    "red": [(2, "очень хорошо"), (5, "хорошо"), (9, "удовлетворительно"), (float('inf'), "неудовлетворительно")],
    "gray": [(2, "очень хорошо"), (4, "хорошо"), (7, "удовлетворительно"), (float('inf'), "неудовлетворительно")],
    "purple": [(0, "очень хорошо"), (3, "хорошо"), (5, "удовлетворительно"), (float('inf'), "неудовлетворительно")],
    "orange": [(0, "очень хорошо"), (1, "хорошо"), (4, "удовлетворительно"), (float('inf'), "неудовлетворительно")],
    "magenta": [(2, "очень хорошо"), (5, "хорошо"), (9, "удовлетворительно"), (float('inf'), "неудовлетворительно")],
    "blue": [(1, "очень хорошо"), (3, "хорошо"), (8, "удовлетворительно"), (float('inf'), "неудовлетворительно")],
    "pink": [(1, "очень хорошо"), (3, "хорошо"), (6, "удовлетворительно"), (float('inf'), "неудовлетворительно")]
}

# Функция для оценки результатов по цвету
def evaluate_color_score(color, score):
    for threshold, evaluation in evaluation_criteria[color]:
        if score <= threshold:
            return f"{color.capitalize()}: {evaluation}"

# Отправка итоговых результатов
async def send_results(user_id):
    scores = user_scores[user_id]
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    result_text = "🎨 *Ваши результаты:*\n"
    for color, score in sorted_scores:
        result_text += f"{color.capitalize()}: {score} баллов\n"
        result_text += f"\n{evaluate_color_score(color, score)}"

    await bot.send_message(user_id, result_text, parse_mode="Markdown")

# Сохранение данных после каждого изменения
def update_user_data():
    data = {
        'scores': user_scores,
        'progress': user_progress
    }
    save_user_data(data)

# Запуск бота (Aiogram 3.x)
async def main():
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
