import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from pymongo import MongoClient
from gridfs import GridFS
from services.zoom_service.zoom_api_util import load_account_info, is_token_expired, refresh_access_token

def get_mongo_collections():
    """Инициализация подключения к MongoDB и GridFS коллекциям."""
    client = MongoClient('mongodb://localhost:27017/')
    db = client['zoom_files']
    screen_fs = GridFS(db, collection='shared_screen_with_speaker_view')
    audio_fs = GridFS(db, collection='audio_only')
    chat_fs = GridFS(db, collection='chat_file')
    return screen_fs, audio_fs, chat_fs

def check_recording_exists(recording_id):
    """Проверка наличия записи в базе данных."""
    screen_fs, audio_fs, chat_fs = get_mongo_collections()
    return any([
        screen_fs.exists({"recording_id": recording_id}),
        audio_fs.exists({"recording_id": recording_id}),
        chat_fs.exists({"recording_id": recording_id})
    ])

def update_task_status(meeting_id, status):
    """Обновляет статус задачи загрузки для указанного meeting_id."""
    client = MongoClient('mongodb://localhost:27017/')
    db = client.queue_workers
    download_tasks = db.download_tasks

    result = download_tasks.update_one(
        {"meeting_id": meeting_id},
        {"$set": {"status": status}}
    )

    if result.modified_count > 0:
        print(f"Updated status of meeting ID {meeting_id} to '{status}'.")
    else:
        print(f"Failed to update status of meeting ID {meeting_id} in MongoDB.")

def update_download_status(meeting_uuid, recording_id, status):
    """Обновляет статус загрузки записи в MongoDB."""
    client = MongoClient('mongodb://localhost:27017/')
    db = client.mds_workspace
    conference_videos = db.conference_videos
    result = conference_videos.update_one(
        {f"meetings.{meeting_uuid}.recordings.recording_id": recording_id},
        {"$set": {f"meetings.{meeting_uuid}.recordings.$.download_status": status}}
    )

    if result.modified_count > 0:
        print(f"Updated status of recording {recording_id} to '{status}'.")
    else:
        print(f"Failed to update status of recording {recording_id} in MongoDB.")


def download_recording_by_id(email, meeting_uuid, recording_id, meeting_id):
    if check_recording_exists(recording_id):
        print(f"Recording {recording_id} already exists in the database.")
        update_download_status(meeting_uuid, recording_id, 'downloaded')
        update_task_status(meeting_id, 'done')
        return None

    account_info = load_account_info(email)
    access_token = account_info['access_token']
    token_expiry_time = account_info['token_expiry_time']

    if is_token_expired(token_expiry_time):
        print("Token expired, refreshing token...")
        access_token = refresh_access_token(email)
        if not access_token:
            return None

    recordings_url = f"https://api.zoom.us/v2/meetings/{meeting_uuid}/recordings"

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    response = requests.get(recordings_url, headers=headers)
    if response.status_code == 200:
        response_json = response.json()
        for recording in response_json.get('recording_files', []):
            if recording['id'] == recording_id:
                download_url = recording.get('download_url')
                file_extension = recording.get('file_extension', 'mp4')
                file_name = f"recording_{recording_id}.{file_extension}"
                recording_type = recording.get('recording_type', 'unknown')

                file_path = download_and_save_file(download_url, file_name, headers)

                if file_path:
                    save_metadata_to_mongodb(file_name, file_path, meeting_uuid, recording_id, recording_type)
                    update_download_status(meeting_uuid, recording_id, 'downloaded')
                    update_task_status(meeting_id, 'done')
                    return file_name

        print(f"No recording found with ID: {recording_id}")
    else:
        print(f"Failed to retrieve recordings: {response.status_code} - {response.text}")
        return None

def save_metadata_to_mongodb(file_name, file_path, meeting_uuid, recording_id, recording_type):
    screen_fs, audio_fs, chat_fs = get_mongo_collections()
    if recording_type == 'shared_screen_with_speaker_view':
        fs = screen_fs
    elif recording_type == 'audio_only':
        fs = audio_fs
    elif recording_type == 'chat_file':
        fs = chat_fs
    else:
        print(f"Unknown recording type: {recording_type}")
        return

    file_metadata = {
        "filename": file_name,
        "file_path": file_path,
        "meeting_uuid": meeting_uuid,
        "recording_id": recording_id,
        "recording_type": recording_type
    }

    fs._GridFS__files.insert_one(file_metadata)
    print(f"Metadata for file {file_name} saved to MongoDB with file path: {file_path}")

def download_and_save_file(download_url, file_name, headers):
    try:
        download_directory = 'downloads'
        if not os.path.exists(download_directory):
            os.makedirs(download_directory)
        file_path = os.path.join(download_directory, file_name)


        with requests.get(download_url, headers=headers, stream=True) as r:
            r.raise_for_status()
            with open(file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"Downloaded recording saved as {file_path}")
        return file_path
    except requests.RequestException as e:
        print(f"Failed to download file: {e}")
        return None


def save_file_to_mongodb(file_name, meeting_uuid, recording_id, recording_type):
    screen_fs, audio_fs, chat_fs = get_mongo_collections()

    if recording_type == 'shared_screen_with_speaker_view':
        fs = screen_fs
    elif recording_type == 'audio_only':
        fs = audio_fs
    elif recording_type == 'chat_file':
        fs = chat_fs
    else:
        print(f"Unknown recording type: {recording_type}")
        return

    with open(file_name, 'rb') as file:
        file_id = fs.put(file, filename=file_name, meeting_uuid=meeting_uuid, recording_id=recording_id, recording_type=recording_type)
        print(f"File {file_name} saved to MongoDB with id: {file_id}")
    os.remove(file_name)

def download_recordings(email, meeting_uuid, recording_ids, meeting_id):
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(download_recording_by_id, email, meeting_uuid, recording_id, meeting_id) for recording_id in recording_ids]
        for future in as_completed(futures):
            future.result()