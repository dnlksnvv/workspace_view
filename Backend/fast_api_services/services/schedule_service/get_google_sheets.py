import os
import json
import pandas as pd
import time
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from pymongo import MongoClient

from config import SPREADSHEET_ID
from services.schedule_service.check_game import process_sheets_data, schedule_notifications, \
    update_last_update_timestamp


def process_sheets_data_and_update_mongo():
    # Настройки MongoDB
    mongo_client = MongoClient("mongodb://localhost:27017/")
    db = mongo_client["schedule"]
    collection_sheets = db["sheets_data"]

    # Настройка для хранения времени последнего обновления
    info_db = mongo_client["info"]
    schedule_info = info_db["schedule"]

    # Настройки и файлы
    current_directory = os.path.dirname(os.path.abspath(__file__))
    SERVICE_ACCOUNT_FILE = os.path.join(current_directory, 'crucial-bloom-430402-b6-8c3a9b17ff2b.json')
    output_json_file = 'services/schedule_service/sheets_data.json'
    exclude_settings_file = 'services/schedule_service/exclude_settings.json'

    # Аутентификация и создание сервиса для доступа к Google Sheets API
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
    )
    service = build('sheets', 'v4', credentials=credentials)

    # Загрузка настроек исключений из JSON файла
    with open(exclude_settings_file, 'r', encoding='utf-8') as file:
        exclude_settings = json.load(file)
    global_exclude = exclude_settings.get("global_exclude", [])

    # Получение списка всех листов
    sheet_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    sheets = sheet_metadata.get('sheets', [])

    # Вывод названий всех листов
    sheet_names = [sheet.get('properties', {}).get('title') for sheet in sheets]
    print("Названия листов в таблице:")
    for name in sheet_names:
        print(name)

    exclude_settings['all_lists'] = sheet_names

    with open(exclude_settings_file, 'w', encoding='utf-8') as file:
        json.dump(exclude_settings, file, ensure_ascii=False, indent=4)

    # Обработка каждого листа, который не находится в глобальном исключении
    sheets_data = {}
    today_str = datetime.today().strftime('%Y-%m-%d')

    for sheet in sheets:
        sheet_name = sheet.get('properties', {}).get('title')
        sheet_gid = sheet.get('properties', {}).get('sheetId')

        if sheet_name not in global_exclude:
            range_name = f'{sheet_name}!A:Z'
            try:
                result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=range_name).execute()
                values = result.get('values', [])
            except Exception as e:
                print(f"Ошибка при запросе к листу {sheet_name}: {e}")
                continue

            # Если данные есть, обрабатываем их
            if values:
                df = pd.DataFrame(values)
                if df.empty:
                    continue

                df = df.iloc[:, :9]
                df = df[df[0].notna() & (df[0] != '')]
                df = df.astype(str)

                data_entries = []
                for index, row in df.iterrows():
                    entry_id = int(f"{sheet_gid}{index + 1}")
                    entry = {
                        'id': entry_id,
                        'link': f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={sheet_gid}&range=A{index + 1}",
                        'row_number': index + 1,
                        'data': [row[0], row[1], row[2], row[3], row[4], row[6], row[7]]
                    }

                    data_entries.append(entry)

                sheets_data[sheet_name] = data_entries

                document = {
                    'sheet_name': sheet_name,
                    'sheet_id': sheet_gid,
                    'data': data_entries,
                    'timestamp': datetime.now()
                }

                collection_sheets.update_one(
                    {'sheet_id': sheet_gid},
                    {'$set': document},
                    upsert=True
                )

            time.sleep(0.5)

    with open(output_json_file, 'w', encoding='utf-8') as file:
        json.dump(sheets_data, file, ensure_ascii=False, indent=4)

    print(f"Данные успешно сохранены в файлы {output_json_file} и записаны в MongoDB.")
    # Обновляем время последнего обновления в базе данных info
    last_update = datetime.now()
    schedule_info.update_one(
        {'name': 'last_update'},
        {'$set': {'time': last_update}},
        upsert=True
    )
    print(f"Время последнего обновления записано: {last_update}")


    print("Проверка игр:")
    process_sheets_data()
    schedule_notifications()
    update_last_update_timestamp()


if __name__ == "__main__":
    process_sheets_data_and_update_mongo()