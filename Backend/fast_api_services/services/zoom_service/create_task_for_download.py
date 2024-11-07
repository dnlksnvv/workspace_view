from datetime import datetime
import pytz
from pymongo import MongoClient
from config import mongodb_adress

moscow_tz = pytz.timezone('Europe/Moscow')


address = f"mongodb://{mongodb_adress[0]}:{mongodb_adress[1]}"
mongo_client = MongoClient(address)
db = mongo_client.queue_workers
scheduled_tasks = db.download_tasks


def schedule_meeting_task(email, meeting_id, meeting_time):
    """
    Метод для записи задачи в базу данных MongoDB для выполнения в определенное время.
    """

    def parse_time_meeting(meeting_time):
        """Парсит время начала и окончания встречи."""
        start_time_str, end_time_str = meeting_time.split(" - ")
        return start_time_str.strip(), end_time_str.strip()

    start_time_str, end_time_str = parse_time_meeting(meeting_time)
    current_date = datetime.now(moscow_tz).date()
    end_time = datetime.strptime(f"{current_date} {end_time_str}", "%Y-%m-%d %H:%M")
    end_time = moscow_tz.localize(end_time)

    task_data = {
        "email": email,
        "meeting_id": meeting_id,
        "execute_time": end_time,
        "status": "pending"
    }

    scheduled_tasks.insert_one(task_data)
    print(f"Задача с email {email} и meeting_id {meeting_id} успешно добавлена в базу данных.")


def cancel_scheduled_task(meeting_id):
    """
    Метод для удаления задачи из базы данных MongoDB.
    """
    task = scheduled_tasks.find_one({"meeting_id": meeting_id})

    if task:
        # Удаление записи из MongoDB
        scheduled_tasks.delete_one({"_id": task["_id"]})
        print(f"Задача с ID встречи {meeting_id} удалена из MongoDB.")
    else:
        print(f"Задача с ID встречи {meeting_id} не найдена в MongoDB.")
