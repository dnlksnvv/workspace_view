import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import mds_login, mds_password

class MdsAuth:
    def __init__(self, driver):
        self.driver = driver
        self.auth = False

    def login(self):
        if not self.auth:
            print("Выполняется авторизация...")
            try:
                # Процесс авторизации
                time.sleep(1)
                username = mds_login
                time.sleep(1)
                password = mds_password
                time.sleep(1)

                login_field_element = WebDriverWait(self.driver, 60).until(
                    EC.element_to_be_clickable((By.XPATH, login_field)))
                login_field_element.click()
                login_field_element.send_keys(username)

                password_field_element = WebDriverWait(self.driver, 60).until(
                    EC.element_to_be_clickable((By.XPATH, password_field)))
                password_field_element.click()
                password_field_element.send_keys(password)

                next_button = WebDriverWait(self.driver, 60).until(
                    EC.element_to_be_clickable((By.XPATH, next)))
                next_button.click()

                self.auth = True  # Обновляем статус авторизации
                print("Авторизация успешно выполнена.")
            except Exception as e:
                print(f"Ошибка при авторизации: {str(e)}")
        else:
            # Если уже авторизованы
            print("Авторизирован")


    def _input_login(self, username):
        login_field_element = self.driver.find_element(By.XPATH, login_field)
        login_field_element.send_keys(username)

    def _input_password(self, password):
        password_field_element = self.driver.find_element(By.XPATH, password_field)
        password_field_element.send_keys(password)

    def _click_next(self):
        next_button = self.driver.find_element(By.XPATH, next)
        next_button.click()

    def _login_field_click(self):
        login_field_clic = self.driver.find_element(By.XPATH, login_field)
        login_field_clic.click()

    def _password_field_click(self):
        password_field_clic = self.driver.find_element(By.XPATH, password_field)
        password_field_clic.click()


next = '/html/body/div[1]/div/div/main/div/div/div/form/button'
login_field = '/html/body/div[1]/div/div/main/div/div/div/form/div[1]/div[1]/div[1]/div/div/div/input'
password_field = '/html/body/div[1]/div/div/main/div/div/div/form/div[1]/div[2]/div[1]/div/div/div/input'