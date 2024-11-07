import requests
import json
import re
import time

def get_token_from_file(user_id, token_key, file_path="../../lms_auth.json"):
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
    print("Обновление токена...")
    from services.lms_services.utils.auth.login_and_get_token import get_new_code
    get_new_code(user_id)
    time.sleep(5)

def fetch_students(user_id, token_key, group_url):
    token = get_token_from_file(user_id, token_key)

    if not token:
        print("Не удалось найти токен для данного пользователя.")
        return []

    group_id = extract_id_from_url(group_url)

    if not group_id:
        print("Не удалось извлечь ID группы из URL.")
        return []

    url = f'https://api.mosdigitals.ru/groups/{group_id}'

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            students = data.get("data", {}).get("students", [])
            return [
                {
                    "id": student["id"],
                    "firstName": student["firstName"],
                    "lastName": student["lastName"]
                }
                for student in students
            ]

        elif response.status_code == 401:
            print("Ошибка: токен невалидный или истекший. Пытаюсь получить новый токен...")
            get_new_token(user_id)
            token = get_token_from_file(user_id, token_key)
            headers['Authorization'] = f'Bearer {token}'
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                students = data.get("data", {}).get("students", [])
                return [
                    {
                        "id": student["id"],
                        "firstName": student["firstName"],
                        "lastName": student["lastName"]
                    }
                    for student in students
                ]
            else:
                print(f"Ошибка повторного запроса: {response.status_code}, {response.text}")

        else:
            print(f"Ошибка запроса: {response.status_code}, {response.text}")

    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return []

def fetch_student_stats(user_id, token_key, student_id, group_id):
    token = get_token_from_file(user_id, token_key)

    if not token:
        print("Не удалось найти токен для данного пользователя.")
        return None

    url = f'https://api.mosdigitals.ru/users/{student_id}/stats'

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            study_groups = data.get("data", {}).get("studyGroups", [])

            for group in study_groups:
                if group.get("id") == group_id:
                    modules = group.get("modules", [])
                    lesson_statuses = []

                    for module in modules:
                        lessons = module.get("lessons", [])
                        for lesson in lessons:
                            lesson_status = lesson.get("status")
                            lesson_statuses.append(lesson_status)

                    return lesson_statuses

        elif response.status_code == 401:
            print("Ошибка: токен невалидный или истекший. Пытаюсь получить новый токен...")
            get_new_token(user_id)
            token = get_token_from_file(user_id, token_key)
            headers['Authorization'] = f'Bearer {token}'
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                study_groups = data.get("data", {}).get("studyGroups", [])

                for group in study_groups:
                    if group.get("id") == group_id:
                        modules = group.get("modules", [])
                        lesson_statuses = []

                        for module in modules:
                            lessons = module.get("lessons", [])
                            for lesson in lessons:
                                lesson_status = lesson.get("status")
                                lesson_statuses.append(lesson_status)

                        return lesson_statuses
            else:
                print(f"Ошибка повторного запроса: {response.status_code}, {response.text}")

        else:
            print(f"Ошибка запроса: {response.status_code}, {response.text}")

    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return None

def extract_id_from_url(url):
    match = re.search(r'/groups/(\d+)', url)
    return int(match.group(1)) if match else None

# Основной код
user_id = '1'  # Укажите ID пользователя
token_key = 'old_lsm_token'  # Укажите ключ токена
group_url = "https://api.mosdigitals.ru/groups/-*************"

group_id = extract_id_from_url(group_url)
students = fetch_students(user_id, token_key, group_url)

for student in students:
    student_id = student["id"]
    student_stats = fetch_student_stats(user_id, token_key, student_id, group_id)
    if student_stats:
        completed_lessons = sum(1 for status in student_stats if status == 4)
        total_lessons = len(student_stats)
        completion_percentage = (completed_lessons / total_lessons) * 100 if total_lessons > 0 else 0

        print(f"{student['firstName']} {student['lastName']} - {completion_percentage:.0f}%")