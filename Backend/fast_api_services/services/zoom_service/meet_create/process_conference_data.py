from services.zoom_service.meet_create.util import format_time, format_zoom, remove_quotes, start_meeting_creation

import json

with open('services/zoom_service/meet_create/accounts.json', 'r') as f:
    accounts = json.load(f)

def process_conference_data(data: dict):
    conference_id = data.get('id')
    conference_data = data.get('data', {})

    conference_data['поток'] = remove_quotes(conference_data.get('поток', ''))
    conference_data['лекция'] = remove_quotes(conference_data.get('лекция', ''))
    conference_data['время'] = format_time(conference_data.get('время', ''))
    conference_data['лектор'] = conference_data.get('лектор', '')
    conference_data['zoom'] = format_zoom(conference_data.get('zoom', ''))

    zoom_email = conference_data['zoom']
    account_data = accounts.get(zoom_email, {})
    conference_data.update(account_data)

    print(f"Conference Data: {conference_data}")
    result = start_meeting_creation(conference_data)
    print(f"Meeting Creation Result: {result}")
    return {
        'status': 'success',
        'message': f'Data received for conference ID: {conference_id}',
        'meeting_details': result
    }