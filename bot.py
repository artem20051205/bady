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
from aiogram.types import FSInputFile

from color_data import color_dict

API_TOKEN = "7930245702:AAGUmtTAd1YV2zKDBLIBb1hgewYFaFtH3mI"
CHANNEL_ID = "@tteessttooss"
photo = FSInputFile("img/1.png")

# Путь к файлу, в котором будут храниться данные
DATA_FILE = 'user_data.json'

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levellevelname)s - %(message)s")

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
        [InlineKeyboardButton(text="✅ Так", callback_data=f"yes_{question_id}")],
        [InlineKeyboardButton(text="❌ Ні", callback_data=f"no_{question_id}")],
        [InlineKeyboardButton(text="⏭ Пропустити", callback_data=f"skip_{question_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Кнопка подписки
def get_subscribe_button():
    return InlineKeyboardMarkup(inline_keyboard=[ 
        [InlineKeyboardButton(text="🔔 Підписатися", url=f"https://t.me/{CHANNEL_ID[1:]}")],
        [InlineKeyboardButton(text="✅ Перевірити підписку", callback_data="check_subscription")]
    ])

# Функция для сброса данных пользователя
def reset_user_data(user_id):
    user_scores[user_id] = {color: 0 for color in next(iter(color_dict.values()))}
    user_progress[user_id] = 0
    update_user_data()

# Функция для запроса начала теста
def get_start_test_buttons():
    buttons = [
        [InlineKeyboardButton(text="✅ Так", callback_data="start_test")],
        [InlineKeyboardButton(text="❌ Ні", callback_data="cancel_start")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Обработчик команды /start
@router.message(CommandStart())
async def send_welcome(message: types.Message):
    await message.answer("Ви хочете пройти тест?", reply_markup=get_start_test_buttons())

# Функция отправки вопросов
async def send_next_question(user_id):
    question_id = user_progress[user_id]
    if question_id < len(color_dict):
        question_text = list(color_dict.keys())[question_id]
        logging.debug(f"Відправляю питання {question_id + 1} користувачу {user_id}")
        await bot.send_message(user_id, f"Питання {question_id + 1}: {question_text}", reply_markup=get_answer_buttons(question_id))
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
            await bot.send_message(user_id, f"❌ Щоб побачити результати, підпишіться на канал: {CHANNEL_ID}", reply_markup=get_subscribe_button())
    except Exception as e:
        logging.error(f"Помилка перевірки підписки: {e}")
        await bot.send_message(user_id, f"❌ Щоб побачити результати, підпишіться на канал: {CHANNEL_ID}", reply_markup=get_subscribe_button())

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
    await callback_query.message.answer("Давай пройдемо тест знову. Натискай на кнопки під питаннями.")
    await send_next_question(user_id)

# Обработчик инлайн-кнопок для отмены перезапуска теста
@router.callback_query(F.data == "cancel_restart")
async def cancel_restart(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
    await callback_query.message.answer("Добре, продовжуємо з поточними результатами.")

# Обработчик инлайн-кнопок для начала теста
@router.callback_query(F.data == "start_test")
async def start_test(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id in user_scores:  # Если пользователь уже есть в данных
        buttons = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Пройти тест знову", callback_data="restart_test")],
            [InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_restart")]
        ])
        await callback_query.message.answer_photo(photo, caption="Ви вже проходили тест. Хочете пройти його знову?", reply_markup=buttons)
    else:
        user_scores[user_id] = {color: 0 for color in next(iter(color_dict.values()))}
        user_progress[user_id] = 0
        update_user_data()  # Сохраняем данные после инициализации
        await callback_query.message.answer_photo(photo, caption="Привіт! Давай пройдемо тест. Натискай на кнопки під питаннями.")
        await send_next_question(user_id)
    await callback_query.message.delete()

# Обработчик инлайн-кнопок для отмены начала теста
@router.callback_query(F.data == "cancel_start")
async def cancel_start(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
    await callback_query.message.answer("Добре, якщо передумаєте, просто надішліть команду /start.")

# Критерии оценки для каждого цвета
evaluation_criteria = {
    "yellow": [(2, "дуже добре"), (4, "добре"), (9, "задовільно"), (float('inf'), "незадовільно")],
    "green": [(2, "дуже добре"), (4, "добре"), (9, "задовільно"), (float('inf'), "незадовільно")],
    "cyan": [(2, "дуже добре"), (3, "добре"), (7, "задовільно"), (float('inf'), "незадовільно")],
    "red": [(2, "дуже добре"), (5, "добре"), (9, "задовільно"), (float('inf'), "незадовільно")],
    "gray": [(2, "дуже добре"), (4, "добре"), (7, "задовільно"), (float('inf'), "незадовільно")],
    "purple": [(0, "дуже добре"), (3, "добре"), (5, "задовільно"), (float('inf'), "незадовільно")],
    "orange": [(0, "дуже добре"), (1, "добре"), (4, "задовільно"), (float('inf'), "незадовільно")],
    "magenta": [(2, "дуже добре"), (5, "добре"), (9, "задовільно"), (float('inf'), "незадовільно")],
    "blue": [(1, "дуже добре"), (3, "добре"), (8, "задовільно"), (float('inf'), "незадовільно")],
    "pink": [(1, "дуже добре"), (3, "добре"), (6, "задовільно"), (float('inf'), "незадовільно")]
}

# Функция для оценки результатов по цвету
def evaluate_color_score(color, score):
    for threshold, evaluation in evaluation_criteria[color]:
        if score <= threshold:
            return f"{color.capitalize()}: {evaluation}"

# Mapping of colors to system names
color_to_system = {
    "yellow": "Травна система",
    "green": "Шлунково-кишковий тракт",
    "cyan": "Серцево-судинна система",
    "red": "Нервова система",
    "gray": "Імунна система",
    "purple": "Дихальна система",
    "orange": "Сечовидільна система",
    "magenta": "Ендокринна система",
    "blue": "Опорно-рухова система",
    "pink": "Шкіра"
}

# Отправка итоговых результатов
async def send_results(user_id):
    scores = user_scores[user_id]
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    result_text = "🎨 *Ваші результати:*\n"
    for color, score in sorted_scores:
        evaluation = evaluate_color_score(color, score)
        if "задовільно" in evaluation or "незадовільно" in evaluation:
            system_name = color_to_system[color]
            result_text += f"{system_name}: {score} балів\n"
            result_text += f"{evaluation}\n\n"

    await bot.send_photo(user_id, photo, caption=result_text.strip(), parse_mode="Markdown")

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
