import json

output_json_file = 'sheets_data.json'
exclude_settings_file = 'exclude_settings.json'

# Загрузка настроек исключений из JSON файла
with open(exclude_settings_file, 'r', encoding='utf-8') as file:
    exclude_settings = json.load(file)

global_exclude = exclude_settings.get("global_exclude", [])
users_exclude = exclude_settings.get("users_exclude", {})

# Загрузка данных листов из JSON файла
with open(output_json_file, 'r', encoding='utf-8') as file:
    sheets_data = json.load(file)

def get_user_excluded_sheets(user_id):
    return users_exclude.get(str(user_id), [])

def list_sheets_for_user(user_id):
    user_exclude = get_user_excluded_sheets(user_id)
    all_excludes = set(global_exclude + user_exclude)
    return [sheet for sheet in sheets_data.keys() if sheet not in all_excludes]

def print_sheet_data(sheet_name):
    if sheet_name in sheets_data:
        print(f"Данные для листа '{sheet_name}':")
        for entry in sheets_data[sheet_name]:
            print(entry)
    else:
        print(f"Лист с названием '{sheet_name}' не найден в данных.")

# Запрашиваем у пользователя ID пользователя
user_id = input("Введите ID пользователя: ")

# Получаем список листов для данного пользователя
available_sheets = list_sheets_for_user(user_id)
print("Доступные листы:", available_sheets)

# Запрашиваем у пользователя название листа, чтобы вывести его содержимое
sheet_name = input("Введите название листа, чтобы вывести его содержимое: ")

# Выводим данные для выбранного листа
print_sheet_data(sheet_name)
