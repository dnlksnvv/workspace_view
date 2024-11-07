import base64
import datetime
import json
import pytz
import requests
import time
from services.zoom_service.meet_create.date_reconstruct import process_time

accounts_path = "services/zoom_service/meet_create/accounts.json"

def load_account_info(email):
    with open(accounts_path, 'r') as file:
        accounts = json.load(file)
    return accounts.get(email)


def save_account_info(email, account_info):
    with open(accounts_path, 'r') as file:
        accounts = json.load(file)
    accounts[email] = account_info
    with open(accounts_path, 'w') as file:
        json.dump(accounts, file, indent=4)


def is_token_expired(token_expiry_time):
    current_time = int(time.time())
    return current_time >= token_expiry_time


def refresh_access_token(email):
    account_info = load_account_info(email)
    client_id = account_info['client_id']
    client_secret = account_info['client_secret']
    refresh_token = account_info['refresh_token']

    token_url = 'https://zoom.us/oauth/token'
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    auth_str = f'{client_id}:{client_secret}'
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()
    headers = {
        'Authorization': f'Basic {b64_auth_str}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.post(token_url, headers=headers, data=data)
    if response.status_code == 200:
        tokens = response.json()
        access_token = tokens['access_token']
        refresh_token = tokens['refresh_token']
        token_expiry_time = int(time.time()) + 3600
        account_info['access_token'] = access_token
        account_info['refresh_token'] = refresh_token
        account_info['token_expiry_time'] = token_expiry_time
        save_account_info(email, account_info)
        print(f'New Access Token: {access_token}')
        print(f'New Refresh Token: {refresh_token}')
        return access_token
    else:
        print(f'Error: {response.status_code}')
        print(response.json())
        return None



def create_meet(email, meeting_topic, start_time, time_period, duration_hours, duration_minutes, meeting_code):
    account_info = load_account_info(email)
    access_token = account_info['access_token']
    token_expiry_time = account_info['token_expiry_time']

    if is_token_expired(token_expiry_time):
        print("Token expired, refreshing token...")
        access_token = refresh_access_token(email)
        if not access_token:
            return


    time_format = "%I:%M %p"
    start_time_str = f"{start_time} {time_period}"
    start_time_dt = datetime.datetime.strptime(start_time_str, time_format)
    moscow_tz = pytz.timezone('Europe/Moscow')
    now = datetime.datetime.now(moscow_tz)
    start_time_dt = start_time_dt.replace(year=now.year, month=now.month, day=now.day)
    start_time_dt = moscow_tz.localize(start_time_dt)
    start_time_iso = start_time_dt.isoformat()
    duration = duration_hours * 60 + duration_minutes
    print(f"ТЕСТ ЗУМА Start time: {start_time_iso}")
    print(f"ТЕСТ ЗУМА Duration: {duration} minutes")


    print("Sending request to create meeting")
    meeting_details = {
        "topic": meeting_topic,
        "type": 2,
        "start_time": start_time_iso,
        "duration": duration,
        "timezone": "Europe/Moscow",
        "password": meeting_code,
        "settings": {
            "host_video": False,
            "participant_video": False,
            "join_before_host": False,
            "mute_upon_entry": True,
            "watermark": True,
            "audio": "both",
            "auto_recording": "cloud",
            "waiting_room": False,
            "approval_type": 2,
            "registrants_email_notification": False,
            "meeting_authentication": False,
        }
    }

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    response = requests.post(
        'https://api.zoom.us/v2/users/me/meetings',
        headers=headers,
        data=json.dumps(meeting_details)
    )


    if response.status_code == 201:
        meeting_info = response.json()
        start_time_formatted = start_time_dt.strftime("%H:%M")
        end_time_dt = start_time_dt + datetime.timedelta(minutes=duration)
        end_time_formatted = end_time_dt.strftime("%H:%M")

        meeting_id_str = str(meeting_info['id'])
        meeting_id_formatted = f"{meeting_id_str[:3]} {meeting_id_str[3:7]} {meeting_id_str[7:]}"

        print("Meeting created successfully:")
        print(f"Meeting ID: {meeting_id_formatted}")
        print(f"Meeting Topic: {meeting_info['topic']}")
        print(f"Meeting Start Time: {start_time_formatted} - {end_time_formatted}")
        print(f"Meeting Join URL: {meeting_info['join_url']}")
        print(f"Meeting Password: {meeting_info.get('password', 'No password')}")

        return email, f"{start_time_formatted} - {end_time_formatted}", meeting_info['join_url'], meeting_id_formatted, meeting_info.get('password', 'No password')
    else:
        print(f"Failed to create meeting: {response.status_code}")
        print(response.text)
        return email, None, None, None, None


def zoom_meeting_creator_api(email, speaker, theme, group, start_time, meeting_code):
    print(f"Initializing meeting creation for {email}")
    meeting_topic = f"{group} - {speaker} - {theme}"
    start_time_12, start_period, duration_hours, duration_minutes_rounded = process_time(start_time)

    account_info = load_account_info(email)
    if not account_info:
        print(f"No account information found for email: {email}")
        return

    meeting_info = create_meet(email, meeting_topic, start_time_12, start_period, duration_hours, duration_minutes_rounded,
                meeting_code)
    return (speaker, theme, group, meeting_topic) + meeting_info
