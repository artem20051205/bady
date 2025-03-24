import asyncio
import json
import logging
import os
from collections import defaultdict
from typing import Dict, Any

import aiofiles
from aiogram import Bot, Dispatcher, types, Router
from aiogram.enums import ChatMemberStatus
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton

import config
from color_data import color_dict, evaluation_criteria, color_to_system, evaluation_icons

# Инициализация токена, ID канала и файла для хранения данных
API_TOKEN: str = config.API_TOKEN
CHANNEL_ID: int = config.CHANNEL_ID
DATA_FILE: str = config.DATA_FILE

# Инициализация бота, диспетчера и роутера
bot: Bot = Bot(token=API_TOKEN)
dp: Dispatcher = Dispatcher()
router: Router = Router()

# Блокировка для синхронизации операций с файлом данных
data_lock = asyncio.Lock()

# Хранение данных пользователей: баллы и прогресс теста
user_scores: Dict[int, Dict[str, int]] = defaultdict(lambda: {color: 0 for color in list(color_dict.values())[0]})
user_progress: Dict[int, int] = defaultdict(int)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
# ==============================
# Функции работы с данными
# ==============================
async def load_user_data() -> Dict[str, Any]:
    if os.path.exists(DATA_FILE):
        async with aiofiles.open(DATA_FILE, 'r', encoding='utf-8') as f:
            try:
                data = json.loads(await f.read())
                return data or {'scores': {}, 'progress': {}}
            except json.JSONDecodeError:
                logging.error("Ошибка загрузки данных из файла JSON.")
    return {'scores': {}, 'progress': {}}

async def save_user_data() -> None:
    async with data_lock, aiofiles.open(DATA_FILE, 'w', encoding='utf-8') as f:
        data = {
            'scores': dict(user_scores),
            'progress': dict(user_progress)
        }
        await f.write(json.dumps(data, ensure_ascii=False, indent=4))

async def init_user_data() -> None:
    global user_scores, user_progress
    data = await load_user_data()
    user_scores.update(data.get('scores', {}))
    user_progress.update(data.get('progress', {}))
# ==============================
# Функции работы с подпиской
# ==============================
async def is_user_subscribed(user_id: int) -> bool:
    try:
        status = (await bot.get_chat_member(CHANNEL_ID, user_id)).status
        return status in {ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR}
    except Exception as e:
        logging.error(f"Ошибка проверки подписки пользователя {user_id}: {e}")
    return False
# ==============================
# Функции создания клавиатур
# ==============================
def create_buttons(buttons: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=text, callback_data=callback)] for text, callback in buttons]
    )

def get_answer_buttons(qid: int) -> InlineKeyboardMarkup:
    return create_buttons([
        ("✅ Так", f"yes_{qid}"),
        ("❌ Ні", f"no_{qid}"),
        ("⏭ Пропустити", f"skip_{qid}")
    ])

def get_subscribe_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔔 Підписатися", url="https://t.me/tteessttooss")],
            [InlineKeyboardButton(text="✅ Перевірити підписку", callback_data="check_subscription")]
        ]
    )

def get_start_buttons() -> InlineKeyboardMarkup:
    return create_buttons([
        ("✅ Так", "start_test"),
        ("❌ Ні", "cancel_start")
    ])

def get_restart_buttons() -> InlineKeyboardMarkup:
    return create_buttons([
        ("🔄 Так, почати заново", "restart_test"),
        ("❌ Ні", "cancel_restart")
    ])

def get_main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⚙️ Опція 1 (в розробці)", callback_data="dev_1"),
                InlineKeyboardButton(text="🔧 Опція 2 (в розробці)", callback_data="dev_2")
            ],
            [
                InlineKeyboardButton(text="📜 Опція 3 (в розробці)", callback_data="dev_3"),
                InlineKeyboardButton(text="🎯 Опція 4 (в розробці)", callback_data="dev_4")
            ],
            [
                InlineKeyboardButton(text="📝 Пройти тест", callback_data="start_test")
            ]
        ]
    )
# ==============================
# Функции отправки сообщений
# ==============================
@router.message(CommandStart())
async def send_welcome(message: types.Message) -> None:
    photo = FSInputFile("img/1.png")
    await message.answer_photo(
        photo=photo,
        caption="👋 Ласкаво просимо! Виберіть дію:",
        reply_markup=get_main_menu()
    )
last_message_was_question: defaultdict[int, bool] = defaultdict(bool)

async def send_next_question(user_id: int, message: types.Message) -> None:
    qid = user_progress[user_id]
    if qid >= len(color_dict):
        await send_results(user_id, message)
        last_message_was_question[user_id] = False
        return
    question_text = f"Питання {qid + 1}: {list(color_dict.keys())[qid]}"
    buttons = get_answer_buttons(qid)
    try:
        if last_message_was_question[user_id]:
            await message.edit_text(question_text, reply_markup=buttons)
        else:
            await message.answer(question_text, reply_markup=buttons)
    except Exception as e:
        logging.error(f"Помилка при відправці/редагуванні питання: {e}")
        await message.answer(question_text, reply_markup=buttons)
    last_message_was_question[user_id] = True


async def reset_and_start_test(user_id: int, message: types.Message) -> None:
    user_scores[user_id] = {color: 0 for color in list(color_dict.values())[0]}
    user_progress[user_id] = 0
    await save_user_data()
    await message.answer("Будь чесними із собою, коли відповідаєте.")
    await send_next_question(user_id, message)


@router.callback_query(lambda c: c.data == "start_test")
async def start_test(callback: types.CallbackQuery) -> None:
    user_id = callback.from_user.id
    if user_progress[user_id] > 0:
        await callback.message.answer(
            "🔄 Ви вже проходили тест. Хочете почати заново?",
            reply_markup=get_restart_buttons()
        )
        return
    await reset_and_start_test(user_id, callback.message)

@router.callback_query(lambda c: c.data == "restart_test")
async def restart_test(callback: types.CallbackQuery) -> None:
    user_id = callback.from_user.id
    await reset_and_start_test(user_id, callback.message)

@router.callback_query(lambda c: c.data.startswith(('yes_', 'no_', 'skip_')))
async def handle_answer(callback: types.CallbackQuery) -> None:
    user_id = callback.from_user.id
    try:
        qid = int(callback.data.split('_')[1])
    except (IndexError, ValueError):
        logging.error("Неправильний формат callback data.")
        return
    if callback.data.startswith("yes_"):
        # При ответе "так" суммируем баллы по каждому цвету
        for color, value in color_dict[list(color_dict.keys())[qid]].items():
            user_scores[user_id][color] += value
    user_progress[user_id] += 1
    await save_user_data()
    await send_next_question(user_id, callback.message)

@router.callback_query(lambda c: c.data == "check_subscription")
async def check_subscription_callback(callback: types.CallbackQuery) -> None:
    user_id = callback.from_user.id
    if await is_user_subscribed(user_id):
        await callback.message.answer("✅ Ви підписані! Ось ваші результати:")
        await send_results(user_id, callback.message)
    else:
        await callback.message.edit_text(
            "❌ Підпишіться на канал:",
            reply_markup=get_subscribe_button()
        )

async def check_subscription(user_id: int, message: types.Message) -> None:
    if await is_user_subscribed(user_id):
        await send_results(user_id, message)
    else:
        await message.edit_text(
            "❌ Щоб побачити результати, підпишіться на канал:",
            reply_markup=get_subscribe_button()
        )

async def send_results(user_id: int, message: types.Message) -> None:
    scores = user_scores.get(user_id, {})
    if not scores:
        await message.answer("⚠️ Помилка! Не вдалося отримати результати.")
        return
    # Сортировка результатов по убыванию баллов
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    result_lines = []
    for color, score in sorted_scores:
        evaluation = evaluate_color_score(color, score)
        icon = evaluation_icons.get(evaluation, '⚪')
        system = color_to_system.get(color, 'Невідома система')
        result_lines.append(f"{icon} *{system}:* {evaluation}")
    result_text = "⬇️ *Ваші результати:*\n" + "\n".join(result_lines)
    try:
        photo = FSInputFile("img/1.png")
        await bot.send_photo(
            chat_id=user_id,
            photo=photo,
            caption=result_text,
            parse_mode="Markdown"
        )
        await message.edit_text("✅ Ваші результати надіслано!", reply_markup=None)
    except Exception as e:
        logging.error(f"Помилка при відправці фото або редагуванні повідомлення: {e}")
        await message.answer(result_text.strip(), parse_mode="Markdown")

def evaluate_color_score(color: str, score: int) -> str:
    return next(
        (eval_str for threshold, eval_str in evaluation_criteria[color] if score <= threshold),
        "Невідомо"
    )
# ==============================
# Основная функция запуска бота
# ==============================
async def main() -> None:

    await init_user_data()
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
