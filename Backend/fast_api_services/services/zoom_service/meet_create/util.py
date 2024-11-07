import concurrent
import os
import time
import json

from services.zoom_service.create_task_for_download import schedule_meeting_task

from services.zoom_service.meet_create.zoom_meeting_creator_api import zoom_meeting_creator_api

import json

with open('services/zoom_service/meet_create/accounts.json', 'r') as f:
    accounts = json.load(f)

def save_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    return {}
def remove_quotes(value):
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    return value

def format_time(value):
    # Убираем все пробелы
    value = value.replace(' ', '')
    # Убираем все знаки, кроме цифр, двоеточия и тире
    value = ''.join([c for c in value if c.isdigit() or c in [':', '-']])
    # Добавляем пробелы перед и после тире
    value = value.replace('-', ' - ')
    return value

def format_zoom(value):
    zoom_map = {
        "zoom 1": "***********",
        "zoom 2": "***********",
        "zoom 3": "***********",
        "zoom 4": "***********",
        "zoom 5": "***********",
        "zoom 6": "***********",
        "zoom 7": "***********",
        "zoom 8": "***********",
        "zoom speaker": "***********",
        "zoom info": "***********"
    }
    return zoom_map.get(value, value)

def thread_meeting_creator(url, email, password, speaker, theme, group, start_time, code):
    print(f"Starting meeting creator with email: {email}")  # Отладочное сообщение
    result = zoom_meeting_creator_api(email, speaker, theme, group, start_time, code)
    return result


def start_meeting_creation(conference_data):
    print(conference_data)
    accounts = [
        (
            "https://zoom.us/signin#/login",
            conference_data['zoom'],
            conference_data['password'],
            conference_data['лектор'],
            conference_data['лекция'],
            conference_data['поток'],
            conference_data['время'],
            "111"
        )
    ]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for account in accounts:
            future = executor.submit(thread_meeting_creator, *account)
            futures.append(future)
            time.sleep(5)
        results = []
        for future in concurrent.futures.as_completed(futures):
            try:
                speaker, theme, group, topic, email, time_meeting, link, id, code = future.result()

                meeting_details = {
                    'speaker': speaker,
                    'theme': theme,
                    'group': group,
                    'topic': topic,
                    'email': email,
                    'time_meeting': time_meeting,
                    'link': link,
                    'id': id,
                    'code': code,
                    'date': conference_data.get('дата', '')
                }
                results.append(meeting_details)
            except Exception as e:
                print(f"Error during meeting creation: {e}")  # Отладочное сообщение
    print("Все встречи созданы.")
    return results

def process_conference_data(data: dict):
    conference_id = data.get('id')
    conference_data = data.get('data', {})
    conference_data['поток'] = remove_quotes(conference_data.get('поток', ''))
    conference_data['лекция'] = remove_quotes(conference_data.get('лекция', ''))
    conference_data['время'] = format_time(conference_data.get('время', ''))
    conference_data['лектор'] = conference_data.get('лектор', '')
    conference_data['zoom'] = format_zoom(conference_data.get('zoom', ''))
    zoom_email = conference_data['zoom']
    account_data = accounts.get(zoom_email, {})
    conference_data.update(account_data)
    result = start_meeting_creation(conference_data)
    print(f"Meeting Creation Result: {result}")

    for meeting in result:
        email = meeting.get('email', '')
        time_meeting = meeting.get('time_meeting', '')

        meeting_id = str(meeting.get('id', '')).replace(' ', '')
        schedule_meeting_task(email, meeting_id, time_meeting)

    return {
        'children_lecture_id': '',
        'status': 'success',
        'message': f'Data received for conference ID: {conference_id}',
        'meeting_details': result
    }


def converted_conference_from_file(conference_id):
    zoom_meeting_file = 'services/zoom_service/meet_create/zoom_meetings.json'
    zoom_meetings_data = load_json(zoom_meeting_file)
    conference_id = str(conference_id)
    meeting_info = zoom_meetings_data[conference_id]['meeting_info']
    data_for_processing = {
        "id": conference_id,
        "data": {
            "id": conference_id,
            "поток": meeting_info['stream'],
            "лекция": meeting_info['topic'],
            "дата": meeting_info['date'],
            "время": format_time(meeting_info['time']),
            "лектор": meeting_info['speaker'].replace("\n", " "),
            "zoom": meeting_info['zoom']
        }
    }

    result = process_conference_data(data_for_processing)
    zoom_meetings_data[conference_id]['formed_conference'] = result

    save_json(zoom_meeting_file, zoom_meetings_data)

    return {'status': result['status']}

