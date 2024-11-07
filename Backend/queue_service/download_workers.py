import datetime
import aiohttp
import asyncio

from config import main_backend_adress


# Функция для проверки задач и выполнения их по расписанию
async def process_tasks(scheduled_tasks):  # Принимаем коллекцию как параметр
    while True:
        now = datetime.datetime.now()

        # Обрабатываем задачи в статусе "pending", время которых уже наступило
        tasks = scheduled_tasks.find({"status": "pending", "execute_time": {"$lte": now}})
        for task in tasks:
            # Если задача в статусе "pending", обновляем статус и устанавливаем время последнего изменения
            scheduled_tasks.update_one(
                {"_id": task["_id"]},
                {
                    "$set": {
                        "status": "in_progress",
                        "last_updated": now  # Устанавливаем время изменения статуса
                    }
                }
            )
            print(f"Начало выполнения задачи: email={task['email']}, meeting_id={task['meeting_id']}, "
                  f"время выполнения: {task['execute_time']}")

            # Отправляем запрос на сервер на порту 8003 для запуска задачи на скачивание
            await send_download_request(task['email'], task['meeting_id'])

        # Проверяем задачи, которые в статусе "in_progress" и которые уже более 20 минут в этом статусе
        ten_minutes_ago = now - datetime.timedelta(minutes=20)
        #TODO исправить время на 20 минут!
        in_progress_tasks = scheduled_tasks.find({"status": "in_progress", "last_updated": {"$lte": ten_minutes_ago}})

        for task in in_progress_tasks:
            # Сбрасываем статус на "pending", если прошло более 10 минут с момента изменения статуса
            scheduled_tasks.update_one(
                {"_id": task["_id"]},
                {
                    "$set": {
                        "status": "pending"
                    },
                    "$unset": {
                        "last_updated": 1  # Удаляем поле "last_updated", чтобы его не было при сбросе
                    }
                }
            )
            print(f"Статус задачи сброшен на pending: email={task['email']}, meeting_id={task['meeting_id']}, "
                  f"время выполнения: {task['execute_time']}")

        # Ждем 10 секунд перед следующей проверкой
        await asyncio.sleep(120)

# Функция для отправки запроса на сервер на порту 8003
async def send_download_request(email, meeting_id):
    async with aiohttp.ClientSession() as session:
        url = f"http://{main_backend_adress[0]}:{main_backend_adress[1]}/api/zoom_service/start_download"
        payload = {
            "email": email,
            "meeting_id": meeting_id
        }
        try:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    print(f"Задача на скачивание успешно отправлена: email={email}, meeting_id={meeting_id}")
                else:
                    print(f"Ошибка при отправке задачи на скачивание: {response.status} - {await response.text()}")
        except aiohttp.ClientError as e:
            print(f"Ошибка при попытке отправить запрос: {e}")