import requests
import json
import os

from config import API_KEY, PROJECT_ID

BASE_URL = "https://api.kinescope.io/v1"
FILE_PATH = "kinescope_folders.json"

def fetch_folders(project_id):
    url = f"{BASE_URL}/projects/{project_id}/folders?order=created_at.desc&page=1&per_page=999"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching folders: {response.status_code}")
        print(response.text)
        return None

def update_couples(folders_data, existing_structure):
    # Получаем текущие папки из структуры
    existing_folder_ids = set(existing_structure['couples'].keys())

    # Получаем папки из загруженных данных
    new_folder_ids = set()

    for folder in folders_data['data']:
        folder_id = folder['id']
        new_folder_ids.add(folder_id)
        if folder_id in existing_structure['couples']:
            existing_structure['couples'][folder_id].update({
                "name": folder['name'],
                "project_id": folder['project_id'],
                "parent_id": folder['parent_id'],
                "size": folder['size'],
                "items_count": folder['items_count'],
                "created_at": folder['created_at']
            })
        else:
            existing_structure['couples'][folder_id] = {
                "name": folder['name'],
                "project_id": folder['project_id'],
                "parent_id": folder['parent_id'],
                "size": folder['size'],
                "items_count": folder['items_count'],
                "created_at": folder['created_at'],
                "tags": []
            }

    # Определяем папки, которых нет среди загруженных данных и удаляем их
    folders_to_remove = existing_folder_ids - new_folder_ids
    for folder_id in folders_to_remove:
        del existing_structure['couples'][folder_id]

    return existing_structure

def load_existing_structure(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    else:
        return {
            "global_exclude": [],
            "users_include": {
                "1": [],
                "2": [],
                "6": []
            },
            "couples": {}
        }

def save_structure(file_path, structure):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(structure, file, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    folders_data = fetch_folders(PROJECT_ID)
    if folders_data:
        existing_structure = load_existing_structure(FILE_PATH)
        updated_structure = update_couples(folders_data, existing_structure)
        save_structure(FILE_PATH, updated_structure)
        print("Updated structure saved to file.")
