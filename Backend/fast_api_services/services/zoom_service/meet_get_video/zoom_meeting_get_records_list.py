import asyncio
import requests
from pymongo import MongoClient

from services.zoom_service.meet_check_status.zoom_meeting_check_status_api import get_meeting_info
from services.zoom_service.zoom_api_util import load_account_info, is_token_expired, refresh_access_token
from services.zoom_service.meet_get_video.zoom_download_records import download_recordings
from config import mongodb_adress

check_interval = 120

def update_task_status(meeting_id, status):
    """Обновляет статус задачи в коллекции download_tasks в MongoDB."""
    address = f"mongodb://{mongodb_adress[0]}:{mongodb_adress[1]}"
    client = MongoClient(address)
    db = client.queue_workers
    download_tasks = db.download_tasks

    result = download_tasks.update_one(
        {"meeting_id": meeting_id},
        {"$set": {"status": status}}
    )

    if result.modified_count > 0:
        print(f"Task status for meeting {meeting_id} updated to '{status}'.")
    else:
        print(f"Failed to update task status for meeting {meeting_id}.")


async def check_status_and_download(email, meeting_id):
    """Функция периодически проверяет статус встречи и запускает загрузку записей, когда статус изменится"""
    address = f"mongodb://{mongodb_adress[0]}:{mongodb_adress[1]}"
    client = MongoClient(address)
    db = client.mds_workspace
    conference_videos = db.conference_videos

    not_found_attempts = 0
    ongoing_attempts = 0
    check_interval = 120

    while True:
        meeting_info = await get_meeting_info(email, meeting_id)

        if meeting_info is None:
            # Ошибка, встреча не найдена
            not_found_attempts += 1
            if not_found_attempts >= 5:
                print(f"Failed to retrieve meeting status after 3 attempts. Exiting.")
                break
            print(f"Meeting {meeting_id} not found, retrying in 10 minutes.")
            await asyncio.sleep(480)  # Ждем 10 минут перед повторной попыткой

        elif meeting_info['status'] in ['ended', 'waiting']:
            # Встреча завершена или в ожидании
            print(f"Meeting {meeting_id} {email} has ended or is waiting, starting download process.")
            await start_getting_recordings(email, meeting_id)
            break

        elif meeting_info['status'] == 'started':
            # Встреча еще продолжается
            ongoing_attempts += 1
            if ongoing_attempts > 20:
                print(f"Meeting {meeting_id} {email} is still ongoing after 20 attempts, exiting.")
                break
            print(f"Meeting {meeting_id} {email} is still ongoing, checking again in {check_interval} seconds.")
            await asyncio.sleep(check_interval)

            if ongoing_attempts == 1:
                check_interval = 120  # 1 минута
            elif ongoing_attempts == 2:
                check_interval = 240  # 5 минут
            elif ongoing_attempts >= 3:
                check_interval = 480  # 10 минут
        else:
            print(f"Unknown status for meeting {meeting_id}: {meeting_info['status']}. Retrying...")
            await asyncio.sleep(480)


def check_url_availability(url):
    try:
        response = requests.head(url)
        return response.status_code == 200
    except requests.RequestException as e:
        print(f"Error checking URL availability: {e}")
        return False


def save_new_recordings_to_db(meeting_id, meeting_uuid, recordings, status, topic):
    """Сохраняет записи в MongoDB под ключом meeting_id, затем meeting_uuid."""
    address = f"mongodb://{mongodb_adress[0]}:{mongodb_adress[1]}"
    client = MongoClient(address)
    db = client.mds_workspace
    conference_videos = db.conference_videos

    if status == "deleted":
        print(f"Skipping saving for Meeting UUID {meeting_uuid} because the status is 'deleted'.")
        return

    update_data = {
        f"meetings.{meeting_uuid}.status": status,
        f"meetings.{meeting_uuid}.topic": topic  # Сохраняем название конференции
    }

    if not recordings:
        conference_videos.update_one(
            {"meeting_id": meeting_id},
            {"$set": update_data},
            upsert=True
        )
        print(f"Meeting UUID {meeting_uuid} saved to MongoDB with status {status} and topic '{topic}'.")
    else:
        for recording in recordings:
            recording['download_status'] = 'not_downloaded'

            if recording['recording_type'] == 'shared_screen_with_speaker_view':
                recording['kinescope_status'] = 'not_upload'
                recording['kinescope_code'] = 'None'

            existing_recording = conference_videos.find_one(
                {"meeting_id": meeting_id,
                 f"meetings.{meeting_uuid}.recordings.recording_id": recording['recording_id']}
            )

            if existing_recording:
                print(
                    f"Recording {recording['recording_id']} already exists for Meeting UUID {meeting_uuid}, skipping.")
            else:
                conference_videos.update_one(
                    {"meeting_id": meeting_id},
                    {
                        "$push": {f"meetings.{meeting_uuid}.recordings": recording},
                        "$set": {f"meetings.{meeting_uuid}.status": status,
                                 f"meetings.{meeting_uuid}.topic": topic}
                    },
                    upsert=True
                )
                print(
                    f"New recording {recording['recording_id']} for Meeting UUID {meeting_uuid} saved to MongoDB with status {status}.")

        print(f"Successfully saved all recordings for Meeting UUID {meeting_uuid}.")
        print("Recording IDs:")
        for recording in recordings:
            print(f"- {recording['recording_id']}")


async def get_recordings_by_meeting_uuid(email, meeting_id, meeting_uuid):
    account_info = await asyncio.to_thread(load_account_info, email)
    access_token = account_info['access_token']
    token_expiry_time = account_info['token_expiry_time']

    if is_token_expired(token_expiry_time):
        print("Token expired, refreshing token...")
        access_token = await asyncio.to_thread(refresh_access_token, email)
        if not access_token:
            return None

    recordings_url = f"https://api.zoom.us/v2/meetings/{meeting_uuid}/recordings"

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    response = await asyncio.to_thread(requests.get, recordings_url, headers=headers)

    if response.status_code == 200:
        response_json = response.json()

        topic = response_json.get("topic", "Unknown Topic")

        recordings = []
        recording_status = "success"

        for recording in response_json.get('recording_files', []):
            recording_type = recording.get('recording_type', 'Unknown Type')

            download_url = recording.get('download_url')
            if await asyncio.to_thread(check_url_availability, download_url):
                print("Recording is available for download.")
            else:
                print("Recording is still processing.")
                recording_status = "processing"
            print("-" * 40)

            recordings.append({
                "recording_id": recording['id'],
                "recording_type": recording_type,
                "file_size": recording.get('file_size', 0),
                "start_time": recording['recording_start'],
                "end_time": recording.get('recording_end', 'N/A'),
            })

        await asyncio.to_thread(save_new_recordings_to_db, meeting_id, response_json['uuid'], recordings, recording_status, topic)
        return recording_status
    else:
        if response.status_code == 404:
            response_json = response.json()
            code = response_json.get("code", "Unknown Code")
            message = response_json.get("message", "No message provided")
            print(f"Zoom API Error - Code: {code}, Message: {message}")

            if "не существует" in message:
                recording_status = "deleted"
                update_task_status(meeting_id, 'deleted_in_zoom')
            else:
                recording_status = "processing"

            await asyncio.to_thread(save_new_recordings_to_db, meeting_id, meeting_uuid, [], recording_status, "Unknown Topic")
        else:
            print(f"Failed to retrieve recordings: {response.status_code} - {response.text}")
        return None


async def get_all_meetings_by_meeting_id(email, meeting_id):
    account_info = await asyncio.to_thread(load_account_info, email)
    access_token = account_info['access_token']
    token_expiry_time = account_info['token_expiry_time']

    if is_token_expired(token_expiry_time):
        print("Token expired, refreshing token...")
        access_token = await asyncio.to_thread(refresh_access_token, email)
        if not access_token:
            return None

    meetings_url = f"https://api.zoom.us/v2/past_meetings/{meeting_id}/instances"

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    response = await asyncio.to_thread(requests.get, meetings_url, headers=headers)

    if response.status_code == 200:
        meetings_response = response.json()
        if 'meetings' in meetings_response:
            return meetings_response['meetings']
        else:
            print("Unexpected API response format.")
            print(meetings_response)
            return None
    else:
        print(f"Failed to retrieve meetings: {response.status_code} - {response.text}")
        return None


async def start_getting_recordings(email, meeting_id):
    attempts = 0
    max_attempts = 20

    while attempts < max_attempts:
        all_meetings = await get_all_meetings_by_meeting_id(email, meeting_id)

        if all_meetings:
            incomplete_meetings = []

            for meeting in all_meetings:
                if isinstance(meeting, dict) and 'uuid' in meeting:
                    print(f"Fetching recordings for meeting UUID: {meeting['uuid']}")
                    recording_status = await get_recordings_by_meeting_uuid(email, meeting_id, meeting['uuid'])

                    if recording_status == "success":
                        print(f"Recordings for meeting UUID {meeting['uuid']} successfully processed.")

                        address = f"mongodb://{mongodb_adress[0]}:{mongodb_adress[1]}"
                        client = MongoClient(address)
                        db = client.mds_workspace
                        conference_videos = db.conference_videos

                        meeting_data = conference_videos.find_one({"meeting_id": meeting_id})
                        if meeting_data and "meetings" in meeting_data:
                            for uuid, details in meeting_data["meetings"].items():
                                print(f"Meeting UUID: {uuid}")
                                if "recordings" in details:
                                    recording_ids = [recording['recording_id'] for recording in details["recordings"]]
                                    print("Recording IDs:")
                                    for recording_id in recording_ids:
                                        print(f"- {recording_id}")

                                    download_recordings(email, uuid, recording_ids, meeting_id)

                    elif recording_status in ["processing", None]:
                        print(f"Recording for meeting UUID {meeting['uuid']} not ready, will retry.")
                        incomplete_meetings.append(meeting)

            if not incomplete_meetings:
                print("All recordings successfully processed.")
                return
            else:
                print(f"Still waiting on {len(incomplete_meetings)} meetings, retrying...")

            attempts += 1
            if attempts >= max_attempts:
                print(f"Reached maximum attempts ({max_attempts}). Stopping retries.")
                return
            else:
                await asyncio.sleep(10)
        else:
            print("No meetings found, retrying...")
            attempts += 1
            if attempts >= max_attempts:
                print(f"Reached maximum attempts ({max_attempts}). Stopping retries.")
                return
            await asyncio.sleep(10)

    print("Processing complete. All available recordings have been processed and saved to MongoDB.")


async def async_task(email, meeting_id):
    await check_status_and_download(email, meeting_id)

def run_task(email, meeting_id):
    try:
        address = f"mongodb://{mongodb_adress[0]}:{mongodb_adress[1]}"
        mongo_client = MongoClient(address)
        db = mongo_client.mds_workspace
        conference_videos = db.conference_videos
        asyncio.run(async_task(email, meeting_id))
    finally:
        print(f"Lock released for meeting ID: {meeting_id}")
