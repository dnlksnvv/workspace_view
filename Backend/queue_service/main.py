import asyncio
import aiohttp
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from pymongo import MongoClient

from config import main_backend_adress, mongodb_adress
from download_workers import process_tasks
from update_scheduler_and_game_notifications_worker import process_notifications, process_error_notifications

app = FastAPI()

# Подключение к базе данных MongoDB
mongo_client = MongoClient(f"mongodb://{mongodb_adress[0]}:{mongodb_adress[1]}/")
db = mongo_client.queue_workers
scheduled_tasks = db.download_tasks
game_notifications = db.game_notification

scheduler = AsyncIOScheduler()

async def call_schedule_update():
    "http://localhost:8003/api/schedule_service/process_sheets"
    """Функция для вызова эндпоинта обновления расписания"""
    url = f"http://{main_backend_adress[0]}:{main_backend_adress[1]}/api/schedule_service/process_sheets"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url) as response:
                if response.status == 200:
                    print("Запрос на обновление расписания успешно отправлен")
                else:
                    print(f"Ошибка при обновлении расписания: {response.status}")
        except Exception as e:
            print(f"Ошибка при отправке запроса: {str(e)}")

# Запуск процесса обработки задач
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(process_tasks(scheduled_tasks))  # Передаем коллекцию в процесс
    asyncio.create_task(process_notifications(game_notifications))
    asyncio.create_task(process_error_notifications(game_notifications))

    scheduler.add_job(call_schedule_update, CronTrigger(hour=15, minute=30))
    scheduler.add_job(call_schedule_update, CronTrigger(hour=10, minute=0))

    scheduler.start()

# Запуск приложения
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
