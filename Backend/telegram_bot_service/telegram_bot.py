import asyncio
import logging
import re

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Router, F
from pymongo import MongoClient
from config import TELEGRAM_API_TOKEN, mongodb_adress
from utils.get_game_data import get_game_data
import aiosqlite
from datetime import datetime


bot = Bot(token=TELEGRAM_API_TOKEN)
dp = Dispatcher()
router = Router()

mongo_client = MongoClient(f"mongodb://{mongodb_adress[0]}:{mongodb_adress[1]}/")
db = mongo_client["schedule"]
dbinfo = mongo_client["info"]
sheets_collection = db["sheets_data"]

logging.basicConfig(level=logging.INFO)

USERS = [99999999999]

async def get_last_update_time():
    last_update_record = dbinfo["schedule_games"].find_one({"name": "last_update"})
    if last_update_record:
        return last_update_record['time']
    return None


def format_update_time(last_update_time):
    now = datetime.now()

    if isinstance(last_update_time, str):
        last_update_time = datetime.fromisoformat(last_update_time)

    # Разница во времени
    delta = now - last_update_time
    last_update_time_str = last_update_time.strftime("%H:%M")

    if delta.days == 0:
        return f"Сегодня в {last_update_time_str}"
    elif delta.days == 1:
        return f"Вчера в {last_update_time_str}"
    elif delta.days == 2:
        return f"Позавчера в {last_update_time_str}"
    elif 3 <= delta.days <= 6:
        return f"{delta.days} дня назад в {last_update_time_str}"
    elif 7 <= delta.days < 14:
        return f"На прошлой неделе в {last_update_time_str}"
    else:
        return last_update_time.strftime("%d.%m в %H:%M")


def replace_links_with_word(description: str) -> str:
    return re.sub(r"(https?://[^\s]+)", r"[ссылка](\1)", description)

from datetime import datetime

async def delete_expired_ids():
    # Получаем все game_ids из локальной базы данных
    async with aiosqlite.connect("game_ids.db") as db:
        async with db.execute("SELECT game_id FROM game_ids") as cursor:
            rows = await cursor.fetchall()
            game_ids = [row[0] for row in rows]

    for game_id in game_ids:
        game_data = get_game_data(game_id, sheets_collection)

        if game_data:
            game_date_str = game_data['date']

            game_date_str = re.sub(r'^[а-яё]{2}, ', '', game_date_str, flags=re.IGNORECASE)

            try:
                game_date = datetime.strptime(game_date_str, "%d.%m.%y")
            except ValueError as e:
                print(f"Ошибка при разборе даты для ID {game_id}: {e}")
                continue

            if game_date < datetime.now():  # Исправлено на datetime.now()
                async with aiosqlite.connect("game_ids.db") as db:
                    await db.execute("DELETE FROM game_ids WHERE game_id = ?", (game_id,))
                    await db.commit()
                print(f"Удалён ID {game_id} с прошедшей датой {game_date_str}")


async def send_message_with_buttons_to_users(message: str, buttons_markup: InlineKeyboardMarkup):
    for user_id in USERS:
        try:
            await bot.send_message(chat_id=user_id, text=message, reply_markup=buttons_markup)
            print(f"Сообщение успешно отправлено пользователю {user_id}")
        except Exception as e:
            print(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")

async def notify_users_with_game_data(game_data_list: list):
    last_update_time = await get_last_update_time()
    message = "Пора готовиться к играм!\n\n"

    if last_update_time:
        formatted_time = format_update_time(last_update_time)
        message = f"Последнее обновление: {formatted_time}\n\n{message}"

    buttons_markup = InlineKeyboardMarkup(inline_keyboard=[])

    for game_data in game_data_list:
        date = game_data['date']
        stream = game_data['stream']
        button_text = f"{date} - {stream}"
        print(button_text)
        if len(button_text) > 64:
            button_text = button_text[:61] + "..."

        buttons_markup.inline_keyboard.append(
            [InlineKeyboardButton(text=button_text, callback_data=str(game_data['id']))]
        )

    await send_message_with_buttons_to_users(message, buttons_markup)


@router.callback_query(F.data.isdigit())
async def process_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    game_id = int(callback_query.data)

    game_data = get_game_data(game_id, sheets_collection)

    if game_data:
        game_data['description'] = replace_links_with_word(game_data['description'])

        message = (
            f"📌 *Поток:* {game_data['stream']}\n"
            f"📌️ *Тема:* {game_data['title']}\n"
            f"📌 *Дата:* {game_data['date']}\n"
            f"📌 *Спикер(ы):* {game_data['speaker']}\n\n"
            f"*Описание:*\n{game_data['description']}\n\n"
            f"[Перейти к расписанию]({game_data['link']})"
        )

        back_button_markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="back")]
        ])

        await bot.edit_message_text(chat_id=user_id, message_id=callback_query.message.message_id, text=message,
                                    reply_markup=back_button_markup, parse_mode="Markdown", disable_web_page_preview=True)
        print(f"Game Data for ID {game_id}: {game_data}")
    else:
        await bot.edit_message_text(chat_id=user_id, message_id=callback_query.message.message_id,
                                    text=f"Данные для Game ID {game_id} не найдены.")

    await callback_query.answer()


async def load_game_ids() -> list:
    # Вызываем функцию
    await delete_expired_ids()
    async with aiosqlite.connect("game_ids.db") as db:
        async with db.execute("SELECT game_id FROM game_ids") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

@router.callback_query(F.data == "back")
async def handle_back(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    game_ids = await load_game_ids()
    last_update_time = await get_last_update_time()

    print(last_update_time)

    last_update_time = await get_last_update_time()
    message = "Пора готовиться к играм!\n\n"

    if last_update_time:
        formatted_time = format_update_time(last_update_time)
        message = f"Последнее обновление: {formatted_time}\n\n{message}"

    buttons_markup = InlineKeyboardMarkup(inline_keyboard=[])

    for game_id in game_ids:
        game_data = get_game_data(game_id, sheets_collection)
        if game_data:
            date = game_data['date']
            stream = game_data['stream']
            button_text = f"️🕹️ {date} - {stream}"
            buttons_markup.inline_keyboard.append(
                [InlineKeyboardButton(text=button_text, callback_data=str(game_id))]
            )

    if not buttons_markup.inline_keyboard:
        message = "Нет доступных игр. Пожалуйста, проверьте позже."

    await bot.edit_message_text(chat_id=user_id, message_id=callback_query.message.message_id, text=message,
                                reply_markup=buttons_markup)

    await callback_query.answer()

async def start_bot():
    print("Бот запущен и готов к отправке сообщений!")
    dp.include_router(router)
    await dp.start_polling(bot)



if __name__ == "__main__":
    asyncio.run(start_bot())