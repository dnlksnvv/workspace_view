import asyncio
import requests
from services.zoom_service.zoom_api_util import load_account_info, is_token_expired, refresh_access_token

async def get_meeting_info(email, meeting_id):
    account_info = await asyncio.to_thread(load_account_info, email)
    access_token = account_info['access_token']
    token_expiry_time = account_info['token_expiry_time']

    if is_token_expired(token_expiry_time):
        print("Token expired, refreshing token...")
        access_token = await asyncio.to_thread(refresh_access_token, email)
        if not access_token:
            return

    status_url = f'https://api.zoom.us/v2/meetings/{meeting_id}'

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    response = await asyncio.to_thread(requests.get, status_url, headers=headers)

    if response.status_code == 200:
        meeting_info = response.json()

        meeting_id = meeting_info.get('id', 'Unknown ID')
        meeting_uuid = meeting_info.get('uuid', 'Unknown UUID')
        meeting_status = meeting_info.get('status', 'unknown')
        start_time = meeting_info.get('start_time', 'Unknown')
        end_time = 'Not Ended'

        if meeting_status == 'ended':
            end_time = meeting_info.get('end_time', 'Unknown')

        return {
            'id': meeting_id,
            'uuid': meeting_uuid,
            'status': meeting_status,
            'start_time': start_time,
            'end_time': end_time
        }
    else:
        print(f"Failed to retrieve meeting status: {response.status_code} - {response.text}")
        return None