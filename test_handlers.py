from aiogram import types, F, Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from typing import Dict, Any
import logging
from color_data import color_dict, evaluation_criteria, evaluation_icons, color_to_system
from utils import save_user_data, load_user_from_json, send_safe_message

router = Router()

# States for user data collection
class UserData(StatesGroup):
    full_name = State()
    age = State()
    height_weight = State()
    diagnoses = State()
    medications = State()

# Test progress and scores
user_test_scores: Dict[int, Dict[str, int]] = {}
user_test_progress: Dict[int, int] = {}
user_last_question_msg_id: Dict[int, int] = {}

def get_answer_buttons(qid: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Так", callback_data=f"yes_{qid}")],
            [InlineKeyboardButton(text="❌ Ні", callback_data=f"no_{qid}")],
            [InlineKeyboardButton(text="⏭ Пропустити", callback_data=f"skip_{qid}")]
        ]
    )

def evaluate_color_score(color: str, score: int) -> str:
    criteria = evaluation_criteria.get(color)
    if not criteria:
        return "Немає критеріїв"
    criteria_sorted = sorted(criteria, key=lambda x: x[0])
    for threshold, eval_str in criteria_sorted:
        if score <= threshold:
            return eval_str
    if criteria_sorted:
        return criteria_sorted[-1][1]
    return "Невідомо"

async def reset_and_start_test(user_id: int, chat_id: int, bot: Bot) -> None:
    """Reset test progress and start the test."""
    global user_test_scores, user_test_progress, user_last_question_msg_id

    user_test_scores[user_id] = {color: 0 for color in list(color_dict.values())[0]}
    user_test_progress[user_id] = 0
    user_last_question_msg_id[user_id] = 0

    await save_user_data(user_id, "test_scores", user_test_scores[user_id])
    await save_user_data(user_id, "test_progress", user_test_progress[user_id])

    await send_safe_message(bot, chat_id, "📝 Тест розпочато! Будь ласка, відповідайте чесно.")
    await send_next_question(user_id, chat_id, bot)

async def send_next_question(user_id: int, chat_id: int, bot: Bot) -> None:
    global user_last_question_msg_id
    qid = user_test_progress.get(user_id, 0)

    if qid >= len(color_dict):
        last_msg_id = user_last_question_msg_id.get(user_id, 0)
        if last_msg_id:
            try:
                await bot.delete_message(chat_id, last_msg_id)
            except TelegramAPIError as e:
                logging.warning(f"Не вдалося видалити останнє повідомлення з питанням {last_msg_id} для {user_id}: {e}")
            user_last_question_msg_id[user_id] = 0
        await send_safe_message(bot, chat_id, "Тест завершено!")
        await send_results(user_id, chat_id, bot)
        return

    question_text = f"❓ Питання {qid + 1}/{len(color_dict)}: {list(color_dict.keys())[qid]}"
    buttons = get_answer_buttons(qid)
    last_msg_id = user_last_question_msg_id.get(user_id, 0)

    try:
        if last_msg_id:
            # Edit the existing message
            await bot.edit_message_text(
                text=question_text,
                chat_id=chat_id,
                message_id=last_msg_id,
                reply_markup=buttons
            )
            logging.debug(f"Відредаговано повідомлення {last_msg_id} для питання {qid} користувача {user_id}")
        else:
            # Send a new message if no existing message ID is found
            sent_message = await bot.send_message(
                chat_id=chat_id,
                text=question_text,
                reply_markup=buttons
            )
            user_last_question_msg_id[user_id] = sent_message.message_id
            logging.debug(f"Надіслано нове повідомлення для питання {qid} користувача {user_id}")
    except TelegramBadRequest as e:
        logging.warning(f"Не вдалося відредагувати повідомлення {last_msg_id} для {user_id} (можливо, текст той самий): {e}. Спроба відправити нове.")
        user_last_question_msg_id[user_id] = 0
        await send_next_question(user_id, chat_id, bot)
    except TelegramAPIError as e:
        logging.error(f"Помилка API під час редагування або надсилання повідомлення для {user_id}: {e}")

async def send_results(user_id: int, chat_id: int, bot: Bot) -> None:
    """Send formatted test results to the user."""
    scores = user_test_scores.get(user_id)
    if not scores:
        logging.warning(f"Результати тесту для користувача {user_id} не знайдено.")
        await send_safe_message(bot, chat_id, "⚠️ Не вдалося знайти ваші результати. Спробуйте пройти тест заново.")
        return

    # Sort scores in descending order
    sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    results_text = "📊 *Ваші результати тесту:*\n\n"
    for color, score in sorted_scores:
        system_name = color_to_system.get(color, "Невідомо")
        evaluation_text = evaluate_color_score(color, score)
        icon = evaluation_icons.get(evaluation_text, "❓")
        results_text += f"{icon} {system_name}: {evaluation_text}\n"

    results_text += "\nДякуємо за участь!"

    try:
        # Send the results as a photo with caption
        photo_path = "img/results_image.jpg"  # Replace with the actual path to your results image
        with open(photo_path, "rb") as photo:
            await bot.send_photo(chat_id, photo, caption=results_text, parse_mode="Markdown")
    except FileNotFoundError:
        logging.error(f"Файл зображення результатів ({photo_path}) не знайдено. Надсилання тексту.")
        await send_safe_message(bot, chat_id, results_text, parse_mode="Markdown")
    except TelegramAPIError as e:
        logging.error(f"Не вдалося надіслати фото результатів для {user_id}: {e}. Надсилання тексту.")
        await send_safe_message(bot, chat_id, results_text, parse_mode="Markdown")

@router.callback_query(F.data == "start_test")
async def handle_start_test_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    bot = callback.bot  # Get the bot instance

    # Check if user data already exists
    existing_data = load_user_from_json(user_id)
    if existing_data:
        logging.info(f"Користувач {user_id} вже вводив свої дані. Пропускаємо введення.")
        await state.update_data(**existing_data)
        await callback.message.answer("Ваші дані вже збережено. Починаємо тест...")
        await reset_and_start_test(user_id, chat_id, bot)
        await callback.answer()
        return

    # If no existing data, proceed with data collection
    await state.set_state(UserData.full_name)
    await callback.message.answer("Будь ласка, введіть ваше ПІБ:")
    await callback.answer()

@router.callback_query(F.data.startswith(('yes_', 'no_', 'skip_')))
async def handle_answer_callback(callback: types.CallbackQuery) -> None:
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    bot = callback.bot  # Get the bot instance

    try:
        action, qid_str = callback.data.split('_', 1)
        qid = int(qid_str)
    except (ValueError, IndexError):
        logging.error(f"Невірний формат callback data: {callback.data} від користувача {user_id}")
        await callback.answer("Сталася помилка.", show_alert=True)
        return

    current_progress = user_test_progress.get(user_id, -1)
    if qid != current_progress:
        await callback.answer("Ви вже відповіли на це питання.", show_alert=True)
        return

    if action == "yes":
        question_key = list(color_dict.keys())[qid]
        for color, value in color_dict[question_key].items():
            current_scores = user_test_scores.setdefault(user_id, {c: 0 for c in list(color_dict.values())[0]})
            current_scores[color] = current_scores.get(color, 0) + value

    user_test_progress[user_id] = current_progress + 1

    await save_user_data(user_id, "test_scores", user_test_scores[user_id])
    await save_user_data(user_id, "test_progress", user_test_progress[user_id])

    await send_next_question(user_id, chat_id, bot)
    await callback.answer()
