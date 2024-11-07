import json
import os
from datetime import datetime

json_file_path = 'services/schedule_service/lecture_on_platform.json'

def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return {}
    return {}

def filter_today_data(user_id):
    exclude_settings_file = 'services/schedule_service/exclude_settings.json'
    sheets_data_file = 'services/schedule_service/sheets_data.json'

    # Загрузка настроек исключений
    exclude_settings = load_json(exclude_settings_file)
    global_exclude = exclude_settings.get("global_exclude", [])
    users_exclude = exclude_settings.get("users_exclude", {}).get(str(user_id), [])

    # Загрузка данных из основного файла
    sheets_data = load_json(sheets_data_file)

    filtered_data = []

    # Текущая дата
    today = datetime.today().strftime('%d.%m.%y')
    print(f"Текущая дата: {today}")

    # Фильтрация данных на основе пользовательских исключений и текущей даты
    for sheet_name, entries in sheets_data.items():
        if sheet_name not in global_exclude and sheet_name not in users_exclude:
            for entry in entries:
                if len(entry['data']) > 2 and ', ' in entry['data'][2]:
                    # Парсинг даты и сравнение с текущей датой
                    entry_date = entry['data'][2].split(', ')[1]
                    if entry_date == today:
                        filtered_data.append({
                            "id": entry['id'],
                            "link": entry['link'],
                            "row_number": entry['row_number'],
                            "sheet_name": sheet_name,
                            "stream": entry['data'][0],
                            "topic": entry['data'][1],
                            "date": entry['data'][2],
                            "time": entry['data'][3],
                            "speaker": entry['data'][4],
                            "description": entry['data'][5] if len(entry['data']) > 5 else '',
                            "zoom": entry['data'][6] if len(entry['data']) > 6 else ''
                        })

    return filtered_data

def update_json_file(new_data):
    if os.path.exists(json_file_path):
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                existing_data = json.load(file)
        except json.JSONDecodeError:
            existing_data = []
    else:
        existing_data = []

    updated = False

    for new_item in new_data:
        new_id = new_item['id']
        found = False
        for existing_item in existing_data:
            if existing_item['id'] == new_id:
                found = True
                differences = {k: new_item[k] for k in new_item if
                               k != 'id' and new_item[k] != existing_item['google_sheets'].get(k)}
                if differences:
                    existing_item['google_sheets'].update(differences)
                    existing_item['platform_lecture'].update(differences)
                    updated = True
                break
        if not found:
            new_record = {
                "id": new_id,
                "google_sheets": {k: new_item[k] for k in new_item if k != 'id'},
                "platform_lecture": {k: new_item[k] for k in new_item if k != 'id'}
            }
            existing_data.append(new_record)
            updated = True

    if updated:
        with open(json_file_path, 'w', encoding='utf-8') as file:
            json.dump(existing_data, file, ensure_ascii=False, indent=4)
        print(f"Обновлены данные: {new_data}")
    else:
        print("Все id уже существуют или нет изменений.")

def get_lectures_main(user_id):
    data = filter_today_data(user_id)
    if data:
        update_json_file(data)
        return data
    else:
        return []

if __name__ == "__main__":
    user_id = 1
    data = get_lectures_main(user_id)