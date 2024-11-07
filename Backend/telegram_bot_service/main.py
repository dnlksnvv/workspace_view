from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
import asyncio
from telegram_bot import notify_users_with_game_data, start_bot, delete_expired_ids
from config import mongodb_adress
from utils.get_game_data import get_game_data  # Импортируем функцию для получения данных
import aiosqlite

app = FastAPI()

# Подключение к MongoDB
mongo_client = MongoClient(f"mongodb://{mongodb_adress[0]}:{mongodb_adress[1]}/")
db = mongo_client["schedule"]
sheets_collection = db["sheets_data"]

class NotificationRequest(BaseModel):
    game_ids: list[int]  # Принимаем список game_ids

@app.post("/api/telegram/send_notification")
async def send_notification(notification: NotificationRequest):
    game_ids = notification.game_ids
    all_game_data = []

    # Получаем данные по каждому game_id
    for game_id in game_ids:
        game_data = get_game_data(game_id, sheets_collection)
        if not game_data:
            raise HTTPException(status_code=404, detail=f"Данные для game_id={game_id} не найдены")

        all_game_data.append(game_data)


    await save_game_ids(game_ids)
    await notify_users_with_game_data(all_game_data)  # Передаем полный список данных

    return {"status": "success", "message": f"Уведомления для game_ids={game_ids} отправлены"}


# Функция для сохранения game_ids в SQLite
async def save_game_ids(game_ids):
    await delete_expired_ids()
    async with aiosqlite.connect("game_ids.db") as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS game_ids (
                            id INTEGER PRIMARY KEY,
                            game_id INTEGER NOT NULL
                        )''')
        for game_id in game_ids:
            await db.execute("INSERT OR REPLACE INTO game_ids (id, game_id) VALUES (?, ?)", (game_id, game_id))
        await db.commit()
async def load_game_ids() -> list:
    async with aiosqlite.connect("game_ids.db") as db:
        async with db.execute("SELECT game_id FROM game_ids") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]  # Возвращаем список game_id

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(start_bot())

@app.get("/health")
async def health_check():
    return {"status": "ok"}