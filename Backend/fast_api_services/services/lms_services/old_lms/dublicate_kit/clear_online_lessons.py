import requests
import json
import re
import time

def get_token_from_file(user_id, token_key, file_path="../../lms_auth.json"):
    """
    Извлекает токен из файла JSON для заданного пользователя и ключа.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            user_data = data.get("users", {}).get(str(user_id), {})
            token_data = user_data.get(token_key, {})
            return token_data.get("token", None)
    except Exception as e:
        print(f"Ошибка чтения файла токенов: {e}")
        return None

def get_new_token(user_id):
    """
    Вызывает метод для обновления токена.
    """
    print("Обновление токена...")
    from services.lms_services.utils.auth.login_and_get_token import get_new_code
    get_new_code(user_id)
    time.sleep(5)

def extract_id_from_url(url):
    """
    Извлекает ID из URL.
    """
    match = re.search(r'/groups/(\d+)', url)
    return match.group(1) if match else None

def process_field(value, expected_type=str):
    """
    Преобразует значение в ожидаемый тип или возвращает None, если значение пустое.
    """
    if value is None or value == "":
        return None
    try:

        return expected_type(value)
    except (ValueError, TypeError):

        return None

def fetch_lessons_by_type(user_id, token_key, group_url, lesson_type=4):

    token = get_token_from_file(user_id, token_key)

    if not token:
        print("Не удалось найти токен для данного пользователя.")
        return


    group_id = extract_id_from_url(group_url)

    if not group_id:
        print("Не удалось извлечь ID группы из URL.")
        return


    url = f'https://api.mosdigitals.ru/groups/{group_id}'


    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    try:

        response = requests.get(url, headers=headers)


        if response.status_code == 200:
            data = response.json()


            for module in data.get("data", {}).get("modules", []):
                for lesson in module.get("lessons", []):

                    if lesson.get("lessonType") == lesson_type:

                        lesson_id = lesson["id"]
                        lesson_data = {
                            "name": process_field(lesson.get("name", "")),
                            "description": "<p>Коллеги, спасибо за участие! Пожалуйста, оставьте оценку и свой комментарий о лекции, это поможет нам стать лучше 💜</p><p><a target=\"_blank\" href=\"https://forms.yandex.ru/-*************/\">https://forms.yandex.ru-*************/</a></p>",
                            "lessonType": process_field(lesson.get("lessonType"), int),
                            "lessonData": {
                                "type": process_field(lesson.get("lessonData", {}).get("type", ""), str),
                                "duration": process_field(lesson.get("lessonData", {}).get("duration", 90), float),
                                "date": None,
                                "teachers": process_field(lesson.get("lessonData", {}).get("teachers", ""), str),
                                "url": None,
                                "videoCode": None
                            }
                        }


                        lesson_data["lessonData"]["type"] = lesson_data["lessonData"]["type"] or ""
                        lesson_data["lessonData"]["duration"] = lesson_data["lessonData"]["duration"] if lesson_data["lessonData"]["duration"] is not None else 0


                        patch_url = f'https://api.mosdigitals.ru/lessons/{lesson_id}'


                        patch_response = requests.patch(patch_url, headers=headers, json=lesson_data)

                        if patch_response.status_code == 200:
                            print(f"Урок {lesson_id} успешно обновлен.")
                        else:
                            print(f"Ошибка обновления урока {lesson_id}: {patch_response.status_code}, {patch_response.text}")

        elif response.status_code == 401:
            print("Ошибка: токен невалидный или истекший. Пытаюсь получить новый токен...")
            get_new_token(user_id)


            token = get_token_from_file(user_id, token_key)
            headers['Authorization'] = f'Bearer {token}'


            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                for module in data.get("data", {}).get("modules", []):
                    for lesson in module.get("lessons", []):
                        if lesson.get("lessonType") == lesson_type:
                            lesson_id = lesson["id"]
                            lesson_data = {
                                "name": process_field(lesson.get("name", "")),
                                "description": "<p>Коллеги, спасибо за участие! Пожалуйста, оставьте оценку и свой комментарий о лекции, это поможет нам стать лучше 💜</p><p><a target=\"_blank\" href=\"https://forms.yandex.ru/cloud/-*************/\">https://forms.yandex.ru/cloud/-*************/</a></p>",
                                "lessonType": process_field(lesson.get("lessonType"), int),
                                "lessonData": {
                                    "type": process_field(lesson.get("lessonData", {}).get("type", ""), str),
                                    "duration": process_field(lesson.get("lessonData", {}).get("duration", 90), float),
                                    "date": None,
                                    "teachers": process_field(lesson.get("lessonData", {}).get("teachers", ""), str),
                                    "url": None,
                                    "videoCode": None
                                }
                            }


                            lesson_data["lessonData"]["type"] = lesson_data["lessonData"]["type"] or ""
                            lesson_data["lessonData"]["duration"] = lesson_data["lessonData"]["duration"] if lesson_data["lessonData"]["duration"] is not None else 0

                            patch_url = f'https://api.mosdigitals.ru/-*************/{lesson_id}'
                            patch_response = requests.patch(patch_url, headers=headers, json=lesson_data)

                            if patch_response.status_code == 200:
                                print(f"Урок {lesson_id} успешно обновлен.")
                            else:
                                print(f"Ошибка обновления урока {lesson_id}: {patch_response.status_code}, {patch_response.text}")
            else:
                print(f"Ошибка повторного запроса: {response.status_code}, {response.text}")

        else:
            print(f"Ошибка запроса: {response.status_code}, {response.text}")

    except Exception as e:
        print(f"Произошла ошибка: {e}")


# Пример использования
user_id = '1'  # Укажите ID пользователя
token_key = 'old_lsm_token'  # Укажите ключ токена

group_url = 'https://lk.mosdigitals.ru/-*************'

fetch_lessons_by_type(user_id, token_key, group_url)