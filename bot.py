import logging
import asyncio
import json
import os
from collections import defaultdict
from aiogram import Bot, Dispatcher, types, Router
from aiogram.enums import ChatMemberStatus
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile
import config
import aiofiles
from color_data import color_dict, evaluation_criteria, color_to_system, evaluation_icons

# Константы
API_TOKEN, CHANNEL_ID, DATA_FILE = config.API_TOKEN, config.CHANNEL_ID, config.DATA_FILE
bot, dp, router = Bot(token=API_TOKEN), Dispatcher(), Router()
data_lock = asyncio.Lock()

# Глобальные переменные
user_data = {}
user_scores = defaultdict(lambda: {color: 0 for color in list(color_dict.values())[0]})
user_progress = defaultdict(int)

# Логирование
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Работа с данными
async def load_user_data():
    if os.path.exists(DATA_FILE):
        async with aiofiles.open(DATA_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.loads(await f.read()) or {'scores': {}, 'progress': {}}
            except json.JSONDecodeError:
                logging.error("Ошибка загрузки данных")
    return {'scores': {}, 'progress': {}}

async def save_user_data():
    async with data_lock, aiofiles.open(DATA_FILE, 'w', encoding='utf-8') as f:
        await f.write(json.dumps({'scores': dict(user_scores), 'progress': dict(user_progress)}, ensure_ascii=False, indent=4))

async def init_user_data():
    global user_data, user_scores, user_progress
    user_data = await load_user_data()
    user_scores.update(user_data.get('scores', {}))
    user_progress.update(user_data.get('progress', {}))

# Проверка подписки
async def is_user_subscribed(user_id: int) -> bool:
    try:
        status = (await bot.get_chat_member(CHANNEL_ID, user_id)).status
        return status in {ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR}
    except Exception as e:
        logging.error(f"Ошибка проверки подписки: {e}")
    return False

# Кнопки
def create_buttons(buttons):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=text, callback_data=callback)] for text, callback in buttons])

def get_answer_buttons(qid):
    return create_buttons([("✅ Так", f"yes_{qid}"), ("❌ Ні", f"no_{qid}"), ("⏭ Пропустити", f"skip_{qid}")])

def get_subscribe_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔔 Підписатися", url="https://t.me/tteessttooss")],
        [InlineKeyboardButton(text="✅ Перевірити підписку", callback_data="check_subscription")]
    ])

def get_start_buttons():
    return create_buttons([("✅ Так", "start_test"), ("❌ Ні", "cancel_start")])

def get_restart_buttons():
    return create_buttons([("🔄 Так, почати заново", "restart_test"), ("❌ Ні", "cancel_restart")])
def get_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚙️ Опция 1 (в разработке)", callback_data="dev_1"),
            InlineKeyboardButton(text="🔧 Опция 2 (в разработке)", callback_data="dev_2")
        ],
        [
            InlineKeyboardButton(text="📜 Опция 3 (в разработке)", callback_data="dev_3"),
            InlineKeyboardButton(text="🎯 Опция 4 (в разработке)", callback_data="dev_4")
        ],
        [
            InlineKeyboardButton(text="📝 Пройти тест", callback_data="start_test")
        ]
    ])

# Обработчики
@router.message(CommandStart())
async def send_welcome(message: types.Message):
    photo = FSInputFile("img/1.png")  # Указываем путь к приветственному изображению
    await message.answer_photo(photo=photo, caption="👋 Добро пожаловать! Выберите действие:", reply_markup=get_main_menu())

# Обработчик для старта теста (если проходит впервые)
@router.callback_query(lambda c: c.data == "start_test")
async def start_test(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    # Если пользователь уже проходил тест — спрашиваем про перезапуск
    if user_progress[user_id] > 0:
        await callback.message.answer("🔄 Ви вже проходили тест. Хочете почати заново?", reply_markup=get_restart_buttons())
        return

    # Начинаем тест с нуля
    await reset_and_start_test(user_id, callback.message)


# Обработчик для перезапуска теста
@router.callback_query(lambda c: c.data == "restart_test")
async def restart_test(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    await reset_and_start_test(user_id, callback.message)


# Функция сброса и старта теста
async def reset_and_start_test(user_id, message):
    user_scores[user_id] = {color: 0 for color in list(color_dict.values())[0]}
    user_progress[user_id] = 0
    await save_user_data()

    await message.answer("Починаємо тест заново! Ось перше питання:")
    await send_next_question(user_id, message)

last_message_was_question = defaultdict(bool)

async def send_next_question(user_id, message):
    qid = user_progress[user_id]

    if qid >= len(color_dict):
        await send_results(user_id, message)
        last_message_was_question[user_id] = False  # После результатов - не вопрос
        return

    question_text = f"Питання {qid + 1}: {list(color_dict.keys())[qid]}"
    buttons = get_answer_buttons(qid)

    if last_message_was_question[user_id]:
        # Если предыдущее сообщение было вопросом — редактируем
        try:
            await message.edit_text(question_text, reply_markup=buttons)
        except Exception as e:
            logging.error(f"Ошибка при редактировании сообщения: {e}")
            await message.answer(question_text, reply_markup=buttons)
    else:
        # Если предыдущее сообщение не было вопросом — отправляем новое
        await message.answer(question_text, reply_markup=buttons)

    last_message_was_question[user_id] = True  # Помечаем, что отправлен вопрос

@router.callback_query(lambda c: c.data.startswith(('yes_', 'no_', 'skip_')))
async def handle_answer(callback: types.CallbackQuery):
    user_id, qid = callback.from_user.id, int(callback.data.split('_')[1])
    if "yes" in callback.data:
        for color, value in color_dict[list(color_dict.keys())[qid]].items():
            user_scores[user_id][color] += value
    user_progress[user_id] += 1
    await save_user_data()
    await send_next_question(user_id, callback.message)

@router.callback_query(lambda c: c.data.startswith(('yes_', 'no_', 'skip_')))
async def handle_answer(callback: types.CallbackQuery):
    user_id, qid = callback.from_user.id, int(callback.data.split('_')[1])
    if "yes" in callback.data:
        for color, value in color_dict[list(color_dict.keys())[qid]].items():
            user_scores[user_id][color] += value
    user_progress[user_id] += 1
    await save_user_data()
    await send_next_question(user_id, callback.message)

async def check_subscription(user_id, message):
    if await is_user_subscribed(user_id):
        await send_results(user_id, message)
    else:
        await message.edit_text("❌ Щоб побачити результати, підпишіться на канал:", reply_markup=get_subscribe_button())

@router.callback_query(lambda c: c.data == "check_subscription")
async def check_subscription_callback(callback: types.CallbackQuery):
    await callback.message.answer("✅ Ви підписані! Ось ваші результати:") if await is_user_subscribed(callback.from_user.id) else await callback.message.edit_text("❌ Підпишіться на канал:", reply_markup=get_subscribe_button())
    if await is_user_subscribed(callback.from_user.id):
        await send_results(callback.from_user.id, callback.message)

async def send_results(user_id, message):
    scores = user_scores.get(user_id, {})
    if not scores:
        return await message.answer("⚠️ Помилка! Не вдалося отримати результати.")

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    result_text = "⬇️ *Ваші результати:*\n" + "\n".join(
        f"{evaluation_icons.get(evaluate_color_score(color, score), '⚪')} *{color_to_system.get(color, 'Невідома система')}:* {evaluate_color_score(color, score)}"
        for color, score in sorted_scores
    )

    try:
        # Загружаем фото и отправляем вместе с текстом
        photo = FSInputFile("img/1.png")  # Указываем путь к фото
        await bot.send_photo(chat_id=user_id, photo=photo, caption=result_text, parse_mode="Markdown")
        
        # Убираем кнопки, редактируя предыдущее сообщение
        await message.edit_text("✅ Ваші результати надіслано!", reply_markup=None)
    except Exception as e:
        logging.error(f"❌ Ошибка при отправке фото или редактировании сообщения: {e}")
        await message.answer(result_text.strip(), parse_mode="Markdown")

def evaluate_color_score(color, score):
    return next((eval for threshold, eval in evaluation_criteria[color] if score <= threshold), "Невідомо")

async def main():
    await init_user_data()
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
