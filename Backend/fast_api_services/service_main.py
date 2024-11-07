from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel
from pymongo import MongoClient

from config import mongodb_adress
from services.zoom_service.meet_get_video.zoom_meeting_get_records_list import run_task
from services.schedule_service.get_google_sheets import process_sheets_data_and_update_mongo

app = FastAPI()

# Подключение к базе данных MongoDB
mongo_client = MongoClient(f"mongodb://{mongodb_adress[0]}:{mongodb_adress[1]}")
db = mongo_client.mds_workspace
scheduled_tasks = db.scheduled_tasks


class TaskRequest(BaseModel):
    email: str
    meeting_id: str

# Эндпоинт для запуска задачи через background task
@app.post("/api/zoom_service/start_download")
async def start_download(task_request: TaskRequest, background_tasks: BackgroundTasks, request: Request):
    meeting_id = task_request.meeting_id
    email = task_request.email

    if not meeting_id or not email:
        raise HTTPException(status_code=400, detail="Invalid input data")

    # Запускаем асинхронную задачу в фоне
    background_tasks.add_task(run_task, task_request.email, task_request.meeting_id)
    return {"message": f"Task for meeting {meeting_id} is being processed."}


# Подключение к базе данных MongoDB
mongo_client = MongoClient(f"mongodb://{mongodb_adress[0]}:{mongodb_adress[1]}")
db = mongo_client.mds_workspace
scheduled_tasks = db.scheduled_tasks

# Эндпоинт для запуска задачи обработки Google Sheets данных
@app.post("/api/schedule_service/process_sheets")
async def process_sheets(background_tasks: BackgroundTasks):
    try:
        # Запускаем задачу в фоне
        background_tasks.add_task(process_sheets_data_and_update_mongo)
        return {"message": "Sheets data processing has been initiated."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")