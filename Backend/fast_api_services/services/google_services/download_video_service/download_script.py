import os
import sys
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from database import Base, VideoDownload

if len(sys.argv) < 2:
    raise ValueError("File ID is required as an argument")

# Абсолютный путь к файлу с учетными данными
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, 'credentials.json')

# ID файла, который вы хотите скачать
FILE_ID = sys.argv[1]

# Путь, куда будет сохранен скачанный файл
DESTINATION_FILE_PATH = os.path.join(BASE_DIR, f'downloads/{FILE_ID}.mp4')

# Проверка существования файла с учетными данными
if not os.path.isfile(SERVICE_ACCOUNT_FILE):
    raise FileNotFoundError(f"Credential file not found: {SERVICE_ACCOUNT_FILE}")

# Создание учетных данных
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=['https://www.googleapis.com/auth/drive']
)

# Создание службы API
service = build('drive', 'v3', credentials=credentials)

# Настройка базы данных
DATABASE_URL = "sqlite:///./users.db"  # Убедитесь, что это правильный путь к вашей базе данных
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

# Запрос на получение файла
request = service.files().get_media(fileId=FILE_ID)

# Скачивание файла
fh = io.FileIO(DESTINATION_FILE_PATH, 'wb')
downloader = MediaIoBaseDownload(fh, request)

done = False
while not done:
    status, done = downloader.next_chunk()
    print(f"Download {int(status.progress() * 100)}%.")

    # Обновление статуса загрузки в базе данных
    video_download = session.query(VideoDownload).filter_by(file_id=FILE_ID).first()
    if video_download:
        video_download.download_status = int(status.progress() * 100)
        session.commit()

print("Download complete!")
