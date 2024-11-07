import json
from datetime import datetime
import asyncio
import pytz
import os

from services.zoom_service.meet_check_status.zoom_meeting_check_status_api import get_meeting_info


current_directory = os.path.dirname(os.path.abspath(__file__))
zoom_meetings_file_path = os.path.join(current_directory, "zoom_meetings.json")


async def check_status_and_download(email, meeting_id):
    """Функция, которая периодически проверяет статус встречи и запускает загрузку записей, когда статус изменится"""
    while True:
        meeting_info = await get_meeting_info(email, meeting_id)
        if meeting_info and meeting_info['status'] != 'started':
            print(f"Meeting {meeting_id} has ended or is not started, starting download process.")
            break
        else:
            print(f"Meeting {meeting_id} is still ongoing, checking again in 10 seconds.")
            await asyncio.sleep(10)
