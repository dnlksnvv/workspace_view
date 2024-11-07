from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
import json

from config import mongodb_adress

app = FastAPI()

mongo_client = MongoClient(f"mongodb://{mongodb_adress[0]}:{mongodb_adress[1]}/")
db = mongo_client["schedule"]
sheets_collection = db["sheets_data"]

class NotificationRequest(BaseModel):
    game_id: int


# Эндпоинт для отправки уведомлений
@app.post("/api/telegram/send_notification")
async def send_notification(notification: NotificationRequest):
    try:
        game_id = notification.game_id

        # Поиск во всех документах в коллекции sheets_data
        sheets = sheets_collection.find({})
        found = False
        for sheet in sheets:
            for data_entry in sheet.get('data', []):
                if data_entry.get('id') == game_id:
                    found = True
                    # Вывод данных объекта в консоль
                    print(f"Найдено занятие с game_id={game_id}:")
                    print(json.dumps(data_entry, ensure_ascii=False, indent=4))

        if not found:
            return {"status": "error", "message": f"Не найдено занятие с game_id={game_id}"}

        # Уведомление может быть отправлено здесь, например через Telegram API
        print(f"Отправляем уведомление для game_id={game_id}")

        return {"status": "success", "message": f"Уведомление для game_id={game_id} отправлено"}

    except Exception as e:
        print(f"Ошибка при отправке уведомления для game_id={notification.game_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при отправке уведомления")


# Эндпоинт для проверки статуса микросервиса
@app.get("/health")
async def health_check():
    return {"status": "ok"}