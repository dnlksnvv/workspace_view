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
    from services.lms_services.utils.auth.login_and_get_token import get_new_code  # Импортируем ваш метод
    get_new_code(user_id)  # Передаем ID пользователя для обновления токена
    time.sleep(5)  # Задержка на некоторое время, чтобы токен успел обновиться

def extract_id_from_url(url):
    """
    Извлекает ID из URL.
    """
    match = re.search(r'/groups/(\d+)', url)
    return match.group(1) if match else None

def fetch_lessons_by_type(user_id, token_key, group_url, lesson_type=4):
    # Извлекаем токен из файла
    token = get_token_from_file(user_id, token_key)

    if not token:
        print("Не удалось найти токен для данного пользователя.")
        return

    # Извлекаем ID группы из URL
    group_id = extract_id_from_url(group_url)

    if not group_id:
        print("Не удалось извлечь ID группы из URL.")
        return

    # URL API с номером набора
    url = f'https://api.mosdigitals.ru/groups/{group_id}'

    # Заголовки, включая токен аутентификации
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    try:
        # Отправляем GET запрос к API
        response = requests.get(url, headers=headers)

        # Проверяем, успешен ли запрос
        if response.status_code == 200:
            data = response.json()

            # Проходим по каждому модулю и каждому уроку внутри модуля
            for module in data.get("data", {}).get("modules", []):
                for lesson in module.get("lessons", []):
                    # Фильтруем уроки по lessonType
                    if lesson.get("lessonType") == lesson_type:
                        # Подготовка данных для PATCH-запроса
                        lesson_id = lesson["id"]
                        lesson_data = {
                            "name": lesson.get("name", ""),
                            "description": "<p>Коллеги, спасибо за участие! Пожалуйста, оставьте оценку и свой комментарий о лекции, это поможет нам стать лучше 💜</p><p><a target=\"_blank\" href=\"https://forms.yandex.ru/cloud/-*************/\">https://forms.yandex.ru/cloud/-*************/</a></p>",
                            "lessonType": lesson.get("lessonType"),
                            "lessonData": {
                                "type": lesson.get("lessonData", {}).get("type", ""),
                                "duration": lesson.get("lessonData", {}).get("duration", 0),
                                "date": None,  # Сбрасываем date
                                "teachers": lesson.get("lessonData", {}).get("teachers", ""),
                                "url": None,  # Сбрасываем url
                                "videoCode": None  # Сбрасываем videoCode
                            }
                        }

                        # URL для PATCH-запроса
                        patch_url = f'https://api.mosdigitals.ru/lessons/{lesson_id}'

                        # Выполняем PATCH запрос
                        patch_response = requests.patch(patch_url, headers=headers, json=lesson_data)

                        if patch_response.status_code == 200:
                            print(f"Урок {lesson_id} успешно обновлен.")
                        else:
                            print(f"Ошибка обновления урока {lesson_id}: {patch_response.status_code}, {patch_response.text}")

        elif response.status_code == 401:
            print("Ошибка: токен невалидный или истекший. Пытаюсь получить новый токен...")
            get_new_token(user_id)  # Обновляем токен

            # Повторяем попытку запроса с новым токеном
            token = get_token_from_file(user_id, token_key)  # Получаем новый токен
            headers['Authorization'] = f'Bearer {token}'

            # Повторный запрос
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                for module in data.get("data", {}).get("modules", []):
                    for lesson in module.get("lessons", []):
                        if lesson.get("lessonType") == lesson_type:
                            lesson_id = lesson["id"]
                            lesson_data = {
                                "name": lesson.get("name", ""),
                                "description": "<p>Коллеги, спасибо за участие! Пожалуйста, оставьте оценку и свой комментарий о лекции, это поможет нам стать лучше 💜</p><p><a target=\"_blank\" href=\"https://forms.yandex.ru/cloud/-*************/\">https://forms.yandex.ru/cloud/-*************/</a></p>",
                                "lessonType": lesson.get("lessonType"),
                                "lessonData": {
                                    "type": lesson.get("lessonData", {}).get("type", ""),
                                    "duration": lesson.get("lessonData", {}).get("duration", 0),
                                    "date": None,
                                    "teachers": lesson.get("lessonData", {}).get("teachers", ""),
                                    "url": None,
                                    "videoCode": None
                                }
                            }
                            patch_url = f'https://api.mosdigitals.ru/lessons/{lesson_id}'
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

def process_courses(user_id, token_key, urls, clean_after_duplicate=False):
    """
    Обрабатывает массив URL-адресов курсов, дублируя и очищая их по очереди.
    """
    for url in urls:
        print(f"Обработка курса по ссылке: {url}")
        duplicate_course(user_id, token_key, url, clean_after_duplicate)

def duplicate_course(user_id, token_key, url, clean_after_duplicate=False):
    # Извлекаем токен из файла
    token = get_token_from_file(user_id, token_key)

    if not token:
        print("Не удалось найти токен для данного пользователя.")
        return

    # Извлекаем ID курса из URL
    course_id = extract_id_from_url(url)

    if not course_id:
        print("Не удалось извлечь ID курса из URL.")
        return

    # Заголовки, включая токен аутентификации
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    # URL для получения информации о курсе
    course_info_url = f'https://api.mosdigitals.ru/groups/{course_id}'
    # URL для дублирования курса
    duplicate_url = f'https://api.mosdigitals.ru/groups/{course_id}/duplicate'

    try:
        # Отправляем запрос для получения информации о курсе
        response = requests.get(course_info_url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            original_course_name = data.get("data", {}).get("course", {}).get("name", "")
            original_course_link = f'https://lk.mosdigitals.ru/groups/{course_id}'

            # Отправляем запрос на дублирование курса
            duplicate_response = requests.get(duplicate_url, headers=headers)

            if duplicate_response.status_code == 200:
                duplicate_data = duplicate_response.json()
                new_course_name = duplicate_data.get("data", {}).get("courseName", "")
                new_course_id = duplicate_data.get("data", {}).get("id", "")
                invite_token = duplicate_data.get("data", {}).get("inviteToken", "")

                # Формируем ссылки
                new_course_link = f'https://lk.mosdigitals.ru/groups/{new_course_id}'
                invite_link = f'https://lk.mosdigitals.ru/invitation?group={invite_token}'

                red_text = '\033[91m'
                red_border = '\033[91m\033[1m'
                reset = '\033[0m'

                # Выводим результаты в консоль
                print(f'Название курса: {original_course_name}')
                print(f'Первоначальная ссылка: {original_course_link}\n')

                print(f'{red_text}ОБЯЗАТЕЛЬНО ДОБАВЬ В НАБОР ССЫЛКУ НА ЧАТ И РАСПИСАНИЕ!{reset}')
                print(f'Название курса: {new_course_name}')
                print(f'{red_border}{"=" * 40}{reset}')
                print(f'{red_border}Новая ссылка: {new_course_link}{reset}')
                print(f'{red_border}Пригласительная ссылка: {invite_link}{reset}')
                print(f'{red_border}{"=" * 40}{reset}')

                # Выполняем очистку уроков, если clean_after_duplicate=True
                if clean_after_duplicate:
                    print("Очистка уроков после дублирования...")
                    fetch_lessons_by_type(user_id, token_key, new_course_link)

            elif duplicate_response.status_code == 400 and "errors.entity.duplicate" in duplicate_response.text:
                print("Курс уже дублирован или существует другой конфликт. Проверьте существующие курсы и повторите попытку.")

            else:
                print(f"Ошибка дублирования курса: {duplicate_response.status_code}, {duplicate_response.text}")

        elif response.status_code == 401:
            print("Ошибка: токен невалидный или истекший. Пытаюсь получить новый токен...")
            get_new_token(user_id)  # Обновляем токен

            # Повторяем попытку дублирования курса с новым токеном
            token = get_token_from_file(user_id, token_key)  # Получаем новый токен
            headers['Authorization'] = f'Bearer {token}'

            # Повторный запрос для получения информации о курсе
            response = requests.get(course_info_url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                original_course_name = data.get("data", {}).get("course", {}).get("name", "")
                original_course_link = f'https://lk.mosdigitals.ru/groups/{course_id}'

                # Повторный запрос на дублирование курса
                duplicate_response = requests.get(duplicate_url, headers=headers)

                if duplicate_response.status_code == 200:
                    duplicate_data = duplicate_response.json()
                    new_course_name = duplicate_data.get("data", {}).get("courseName", "")
                    new_course_id = duplicate_data.get("data", {}).get("id", "")
                    invite_token = duplicate_data.get("data", {}).get("inviteToken", "")

                    # Формируем ссылки
                    new_course_link = f'https://lk.mosdigitals.ru/groups/{new_course_id}'
                    invite_link = f'https://lk.mosdigitals.ru/invitation?group={invite_token}'


                    red_text = '\033[91m'
                    red_border = '\033[91m\033[1m'
                    reset = '\033[0m'

                    # Выводим результаты в консоль
                    print(f'Название курса: {original_course_name}')
                    print(f'Первоначальная ссылка: {original_course_link}\n')

                    print(f'{red_text}ОБЯЗАТЕЛЬНО ДОБАВЬ В НАБОР ССЫЛКУ НА ЧАТ И РАСПИСАНИЕ!{reset}')
                    print(f'Название курса: {new_course_name}')
                    print(f'{red_border}{"=" * 40}{reset}')
                    print(f'{red_border}Новая ссылка: {new_course_link}{reset}')
                    print(f'{red_border}Пригласительная ссылка: {invite_link}{reset}')
                    print(f'{red_border}{"=" * 40}{reset}')


                    if clean_after_duplicate:
                        print("Очистка уроков после дублирования...")
                        fetch_lessons_by_type(user_id, token_key, new_course_link)

                elif duplicate_response.status_code == 400 and "errors.entity.duplicate" in duplicate_response.text:
                    print("Курс уже дублирован или существует другой конфликт. Проверьте существующие курсы и повторите попытку.")

                else:
                    print(f"Ошибка дублирования курса: {duplicate_response.status_code}, {duplicate_response.text}")
            else:
                print(f"Ошибка повторного получения информации о курсе: {response.status_code}, {response.text}")

        else:
            print(f"Ошибка получения информации о курсе: {response.status_code}, {response.text}")

    except Exception as e:
        print(f"Произошла ошибка: {e}")


user_id = '1'
token_key = 'old_lsm_token'
course_urls = ["https://lk.mosdigitals.ru/groups/-*************"]

# Обработка всех курсов по очереди
process_courses(user_id, token_key, course_urls, clean_after_duplicate=True)