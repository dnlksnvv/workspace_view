import os
import base64
import json
import time
import requests

# Определение абсолютного пути к accounts.json
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_FILE_PATH = os.path.join(BASE_DIR, 'meet_create', 'accounts.json')

def load_account_info(email):
    with open(ACCOUNTS_FILE_PATH, 'r') as file:
        accounts = json.load(file)
    return accounts.get(email)

def save_account_info(email, account_info):
    with open(ACCOUNTS_FILE_PATH, 'r') as file:
        accounts = json.load(file)
    accounts[email] = account_info
    with open(ACCOUNTS_FILE_PATH, 'w') as file:
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

