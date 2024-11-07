import json
import requests
import requests.auth
import urllib
import time
from flask import Flask, request


CLIENT_ID = "********************"
CLIENT_SECRET = "********************"
REDIRECT_URI = "http://localhost:5001/callback"
ACCOUNTS_FILE_PATH = 'accounts.json'  # Путь к файлу accounts.json

app = Flask(__name__)


@app.route('/')
def homepage():
    return f'<a href="{make_authorization_url()}">Authenticate with Zoom</a>'


def make_authorization_url():
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI
    }
    url = "https://zoom.us/oauth/authorize?" + urllib.parse.urlencode(params)
    return url


@app.route('/callback')
def zoom_callback():
    error = request.args.get('error', '')
    if error:
        return f"Error: {error}"

    code = request.args.get('code')
    access_token, refresh_token, token_expiry_time = get_token(code)

    if access_token:
        email = "********************"
        update_account_tokens(email, access_token, refresh_token, token_expiry_time, CLIENT_ID, CLIENT_SECRET)
        return f"Tokens обновлены для {email} и сохранены в accounts.json"
    else:
        return "Не удалось получить токен"


def get_token(code):
    client_auth = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
    post_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI
    }

    response = requests.post("https://zoom.us/oauth/token", auth=client_auth, data=post_data)
    token_json = response.json()

    if response.status_code == 200:
        access_token = token_json["access_token"]
        refresh_token = token_json["refresh_token"]
        token_expiry_time = token_json.get("expires_in", 3600) + int(time.time())  # Время жизни токена
        return access_token, refresh_token, token_expiry_time
    else:
        print(f"Ошибка: {token_json}")
        return None, None, None


def update_account_tokens(email, access_token, refresh_token, token_expiry_time, client_id, client_secret):
    try:
        with open(ACCOUNTS_FILE_PATH, 'r') as file:
            accounts = json.load(file)

        if email in accounts:
            accounts[email]['access_token'] = access_token
            accounts[email]['refresh_token'] = refresh_token
            accounts[email]['token_expiry_time'] = token_expiry_time
            accounts[email]['client_id'] = client_id
            accounts[email]['client_secret'] = client_secret

            with open(ACCOUNTS_FILE_PATH, 'w') as file:
                json.dump(accounts, file, indent=4)
            print(f"Токены успешно обновлены для {email}.")
        else:
            print(f"Email {email} не найден в accounts.json.")
    except Exception as e:
        print(f"Ошибка при обновлении токенов: {e}")


if __name__ == '__main__':
    app.run(debug=True, port=5001)
