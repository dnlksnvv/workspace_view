import aiohttp
import asyncio
import datetime
from pymongo import MongoClient
from config import mongodb_adress


async def process_notifications(game_notifications):
    while True:
        now = datetime.datetime.now()

        notifications = game_notifications.find({"status": {"$nin": ["in_progress", "error"]}})
        notification_count = game_notifications.count_documents({"status": {"$nin": ["in_progress", "error"]}})
        print(f"Найдено {notification_count} уведомлений для обработки.")

        if notification_count == 0:
            print("Задачи отсутствуют, ждем 15 секунд перед следующей проверкой.")
        else:
            game_ids = []
            for notification in notifications:
                game_id_data = notification.get("game_id", {})

                # Извлекаем значение game_id
                if isinstance(game_id_data, dict) and "$numberLong" in game_id_data:
                    game_id = game_id_data["$numberLong"]
                else:
                    game_id = game_id_data  # Если структура другая, используем как есть

                print(f"Подготовка уведомления для game_id={game_id}")
                game_ids.append(game_id)

                # Обновляем статус на "in_progress" для текущего уведомления
                game_notifications.update_one(
                    {"_id": notification["_id"]},
                    {
                        "$set": {
                            "status": "in_progress",
                            "last_updated": now
                        }
                    }
                )

            # Отправляем все уведомления одним запросом
            success_ids, failed_ids = await send_notification_request(game_ids)

            # Проверяем результаты отправки
            if success_ids:
                print(f"Успешные уведомления для game_ids: {success_ids}")
                # Здесь можно раскомментировать удаление успешных записей
                game_notifications.delete_many({"game_id": {"$in": success_ids}})
                print(f"Эти уведомления будут удалены: {success_ids}")

            if failed_ids:
                # Обновляем статус на "error" для неудачных задач
                for failed_id in failed_ids:
                    game_notifications.update_one(
                        {"game_id": failed_id},
                        {
                            "$set": {
                                "status": "error",
                                "last_updated": now
                            }
                        }
                    )
                print(f"Неудачные уведомления для game_ids: {failed_ids}")
        await asyncio.sleep(120)


# Функция для обработки задач со статусом "error"
async def process_error_notifications(game_notifications):
    while True:
        now = datetime.datetime.now()

        # Находим все записи в статусе "error"
        error_notifications = game_notifications.find({"status": "error"})
        error_count = game_notifications.count_documents({"status": "error"})
        print(f"Найдено {error_count} уведомлений со статусом 'error' для повторной обработки.")

        if error_count == 0:
            print("Задачи с ошибками отсутствуют, ждем 30 секунд перед следующей проверкой.")
        else:
            game_ids = []
            for notification in error_notifications:
                game_id_data = notification.get("game_id", {})

                # Извлекаем значение game_id
                if isinstance(game_id_data, dict) and "$numberLong" in game_id_data:
                    game_id = game_id_data["$numberLong"]
                else:
                    game_id = game_id_data  # Если структура другая, используем как есть

                print(f"Повторная попытка отправки уведомления для game_id={game_id}")
                game_ids.append(game_id)

            # Отправляем все уведомления одним запросом
            success_ids, failed_ids = await send_notification_request(game_ids)

            # Проверяем результаты отправки
            if success_ids:
                print(f"Успешные уведомления для game_ids: {success_ids}")
                # Здесь можно раскомментировать удаление успешных записей
                game_notifications.delete_many({"game_id": {"$in": success_ids}})
                print(f"Эти уведомления будут удалены: {success_ids}")

            if failed_ids:
                print(f"Неудачные уведомления для game_ids: {failed_ids}")


        await asyncio.sleep(240)

# Функция для отправки уведомления на микросервис Telegram
async def send_notification_request(game_ids):
    success_ids = []
    failed_ids = []

    # Подключаемся к MongoDB
    mongo_client = MongoClient(f"mongodb://{mongodb_adress[0]}:{mongodb_adress[1]}/")
    db = mongo_client["schedule"]
    sheets_collection = db["sheets_data"]

    async with aiohttp.ClientSession() as session:
        url = "http://localhost:8004/api/telegram/send_notification"  # Микросервис для отправки уведомлений

        payload = {
            "game_ids": game_ids
        }

        try:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    print(f"Успешная отправка уведомлений для game_ids={game_ids}")
                    success_ids.extend(game_ids)

                    for game_id in game_ids:
                        sheets_collection.update_one(
                            {"data.id": int(game_id)},
                            {"$set": {"data.$.notificate": True}}
                        )
                        print(f"Поле 'notificate' для game_id={game_id} установлено в true")
                else:
                    print(f"Ошибка при отправке уведомлений: {response.status} - {await response.text()}")
                    print(f"Ошибка при отправке уведомлений: {response.status} - {await response.text()}")
                    failed_ids.extend(game_ids)

        except aiohttp.ClientError as e:
            print(f"Ошибка при отправке уведомлений для game_ids={game_ids}: {e}")
            failed_ids.extend(game_ids)

    return success_ids, failed_ids