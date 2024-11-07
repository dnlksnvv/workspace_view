import os
import requests
from services.zoom_service.zoom_api_util import load_account_info, save_account_info, is_token_expired, refresh_access_token

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_FILE_PATH = os.path.join(BASE_DIR, 'meet_create', 'accounts.json')

def delete_meeting(email, meeting_id):
    account_info = load_account_info(email)
    access_token = account_info['access_token']
    token_expiry_time = account_info['token_expiry_time']

    if is_token_expired(token_expiry_time):
        print("Token expired, refreshing token...")
        access_token = refresh_access_token(email)
        if not access_token:
            return

    delete_url = f'https://api.zoom.us/v2/meetings/{meeting_id}'

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    response = requests.delete(delete_url, headers=headers)

    if response.status_code == 204:
        print(f"Meeting with ID {meeting_id} deleted successfully.")
        return True
    else:
        print(f"Failed to delete meeting: {response.status_code}")
        print(response.text)
        return False