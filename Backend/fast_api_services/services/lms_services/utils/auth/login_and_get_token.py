import json
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from services.lms_services.utils.auth.mds_auth import MdsAuth

driver_path = '/opt/homebrew/bin/chromedriver'
json_file_path = '../../lms_auth.json'

def update_json_file(user_id, token, status_code):
    # Если файл существует, загружаем данные
    if os.path.exists(json_file_path):
        try:
            with open(json_file_path, 'r') as file:
                data = json.load(file)
        except json.JSONDecodeError:
            data = {"users": {}}
    else:
        data = {"users": {}}

    # Обновляем данные пользователя
    user_id = str(user_id)  # Приводим user_id к строковому типу
    if user_id not in data["users"]:
        data["users"][user_id] = {}

    # Если статусный код не 200, оставляем токен не тронутым
    if status_code != 200:
        if "old_lsm_token" in data["users"][user_id]:
            data["users"][user_id]["old_lsm_token"]["status_code"] = status_code
        else:
            data["users"][user_id]["old_lsm_token"] = {"token": None, "status_code": status_code}
    else:
        data["users"][user_id]["old_lsm_token"] = {
            "token": token,
            "status_code": status_code
        }

    # Записываем обратно в файл
    with open(json_file_path, 'w') as file:
        json.dump(data, file, indent=4)

def get_new_code(user_id):
    # Настройки для перехвата сетевых запросов
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_options.add_experimental_option('prefs', {'profile.default_content_setting_values.cookies': 2})
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--remote-debugging-port=9222")

    # Настройки для логов сетевых запросов
    chrome_options.set_capability("goog:loggingPrefs", {'performance': 'ALL'})

    # Инициализируем драйвер
    service = Service(executable_path=driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    url = 'https://lk.mosdigitals.ru/auth/signin'
    driver.get(url)

    # Инициализируем и выполняем авторизацию
    mds_auth = MdsAuth(driver)
    mds_auth.login()

    # Ожидаем некоторое время, чтобы все сетевые запросы завершились
    time.sleep(10)

    # Перехватываем и выводим сетевые логи
    logs = driver.get_log('performance')
    signin_data = None

    for log in logs:
        message = json.loads(log['message'])['message']
        if 'Network.responseReceived' in message['method']:
            request_id = message['params']['requestId']
            if 'response' in message['params']:
                url = message['params']['response']['url']
                try:
                    response = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                    if 'https://api.mosdigitals.ru/auth/signin' in url:
                        signin_data = response['body']
                        break
                except Exception as e:
                    print(f"Error retrieving response body for {url}: {e}")

    if signin_data:
        print("Received signin response:", signin_data)
        signin_response = json.loads(signin_data)
        token = signin_response['data']['token'] if signin_response['success'] else None
        status_code = signin_response['code']
        update_json_file(user_id, token, status_code)
    else:
        print("Signin response not found.")

    # Закрываем драйвер после завершения работы
    driver.quit()

if __name__ == "__main__":
    get_new_code(1)
