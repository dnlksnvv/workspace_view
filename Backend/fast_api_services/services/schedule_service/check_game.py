import pymongo
from datetime import datetime, timedelta
import re

# Подключение к MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["schedule"]
sheets_collection = db["sheets_data"]
schedule_collection = db["schedule_games"]
game_notification_collection = client["queue_workers"]["game_notification"]
info_db = client["info"]
schedule_games = info_db["schedule_games"]

# Задаём ключевые слова
KEYWORDS = ["заранее", "выслать", "поделить", "высылаем", "игра", "игре", "игру", "игры", "за две недели", "разделить", "команды", "делим"]

def is_future_event(event_date_str):
    """Проверяем, является ли событие будущим и возвращаем дату"""
    try:
        clean_date_str = event_date_str.split(", ")[1].strip()

        parts = clean_date_str.split(".")
        day = parts[0].zfill(2)
        month = parts[1].zfill(2)
        year = parts[2]
        clean_date_str = f"{day}.{month}.{year}"

        event_date = datetime.strptime(clean_date_str, "%d.%m.%y")
        return event_date
    except (IndexError, ValueError):
        return None

def contains_keywords(description):
    """Проверка, содержит ли описание ключевые слова"""
    description_lower = description.lower()
    for keyword in KEYWORDS:
        if re.search(rf"\b{keyword}\b", description_lower):
            return True
    return False

def process_sheets_data():
    """Основная функция для обработки данных из Google Sheets и обновления базы schedule_games"""
    for sheet in sheets_collection.find():
        sheet_data = sheet["data"]

        for entry in sheet_data:
            entry_data = entry["data"]
            event_date_str = entry_data[2]
            event_description = entry_data[5]

            event_date = is_future_event(event_date_str)

            if event_date and contains_keywords(event_description):
                existing_entry = schedule_collection.find_one({"id": entry["id"]})

                if existing_entry:
                    existing_date_str = existing_entry.get("date")

                    if existing_date_str:
                        try:
                            existing_clean_date = existing_date_str.split(", ")[1].strip()
                            existing_parts = existing_clean_date.split(".")
                            existing_day = existing_parts[0].zfill(2)
                            existing_month = existing_parts[1].zfill(2)
                            existing_year = existing_parts[2]
                            existing_clean_date = f"{existing_day}.{existing_month}.{existing_year}"
                            existing_date = datetime.strptime(existing_clean_date, "%d.%m.%y")

                            if existing_date != event_date:
                                schedule_collection.update_one(
                                    {"id": entry["id"]},
                                    {"$set": {"date": event_date_str, "notificate": False}}
                                )
                                print(f"Дата обновлена для id: {entry['id']}, notificate сброшен на False")
                            else:
                                print(f"Занятие уже существует с той же датой: {entry['id']}")
                        except (IndexError, ValueError):
                            print(f"Некорректный формат даты для существующей записи: {existing_entry['id']}")
                    else:
                        schedule_collection.update_one(
                            {"id": entry["id"]},
                            {"$set": {"date": event_date_str, "notificate": False}}
                        )
                        print(f"Добавлена дата для id: {entry['id']}, notificate сброшен на False")
                else:
                    # Используем upsert, чтобы избежать дублирования записей с одинаковым id
                    schedule_collection.update_one(
                        {"id": entry["id"]},
                        {"$set": {
                            "date": event_date_str,
                            "notificate": False
                        }},
                        upsert=True
                    )
                    print(f"Добавлена новая запись для id: {entry['id']}")

def schedule_notifications():
    """Проверяем, нужно ли отправить уведомления для занятий через 14 дней или ранее"""
    today = datetime.today()
    two_weeks_later = today + timedelta(days=14)

    for entry in schedule_collection.find({"notificate": False}):
        entry_date_str = entry.get("date")
        try:
            clean_date_str = entry_date_str.split(", ")[1].strip()
            parts = clean_date_str.split(".")
            day = parts[0].zfill(2)
            month = parts[1].zfill(2)
            year = parts[2]
            clean_date_str = f"{day}.{month}.{year}"
            entry_date = datetime.strptime(clean_date_str, "%d.%m.%y")

            if today <= entry_date <= two_weeks_later:
                game_notification_collection.update_one(
                    {"game_id": entry["id"]},
                    {"$set": {"game_id": entry["id"], "timestamp": datetime.now()}},
                    upsert=True
                )
                schedule_collection.update_one(
                    {"id": entry["id"]},
                    {"$set": {"notificate": True}}
                )
                print(f"Записан id в game_notification: {entry['id']}")
        except (ValueError, IndexError):
            print(f"Некорректная дата для id: {entry['id']}")

def update_last_update_timestamp():
    """Обновление времени последнего обновления в коллекции schedule_games"""
    last_update = datetime.now()
    schedule_games.update_one(
        {'name': 'last_update'},
        {'$set': {'time': last_update}},
        upsert=True
    )
    print(f"Время последнего обновления записано: {last_update}")


if __name__ == "__main__":
    process_sheets_data()
    schedule_notifications()
    update_last_update_timestamp()