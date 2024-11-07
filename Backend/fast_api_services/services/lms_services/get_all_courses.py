import json
import requests
import subprocess
import sys

# Пути к файлам
auth_json_file = 'lms_auth.json'
courses_json_file = 'lms_courses.json'

# API URL
api_url = 'https://api.mosdigitals.ru/-*************'

def get_token(user_id):
    with open(auth_json_file, 'r') as file:
        data = json.load(file)
        return data["users"][str(user_id)]["old_lsm_token"]["token"]

def update_courses_file(course_data):
    try:
        with open(courses_json_file, 'r') as file:
            file_content = file.read().strip()
            if file_content:
                existing_data = json.loads(file_content)
            else:
                existing_data = None
    except FileNotFoundError:
        existing_data = None

    if existing_data is None:
        existing_data = {
            "global_exclude": [],
            "users_include": {
                "1": [],
            },
            "couples": {}
        }

    for item in course_data:
        course_id = item["id"]
        course_name = item["course"]["name"]

        if str(course_id) not in existing_data["couples"]:
            existing_data["couples"][str(course_id)] = {
                "name": course_name,
                "tags": []
            }

    # Удаление курсов, которые больше не существуют в API
    existing_course_ids = {str(item["id"]) for item in course_data}
    existing_data["couples"] = {
        course_id: details for course_id, details in existing_data["couples"].items()
        if course_id in existing_course_ids
    }

    # Сохранение обновленного файла
    with open(courses_json_file, 'w') as file:
        json.dump(existing_data, file, indent=4, ensure_ascii=False)

def fetch_and_update_courses(retry=False):
    token = get_token(1)

    headers = {
        'Authorization': f'Bearer {token}'
    }

    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if data["success"] and data["code"] == 200:
            course_items = data["data"]["items"]
            update_courses_file(course_items)
        else:
            print("API returned an error:", data["message"])
    elif response.status_code == 401 and not retry:
        print("Failed to fetch data from API. Status code: 401. Attempting to refresh token...")
        # Запуск скрипта для обновления токена с использованием текущего интерпретатора Python
        subprocess.run([sys.executable, "login_and_get_token.py"], check=True)
        # Повторная попытка выполнения
        fetch_and_update_courses(retry=True)
    else:
        print("Failed to fetch data from API. Status code:", response.status_code)

if __name__ == "__main__":
    fetch_and_update_courses()
