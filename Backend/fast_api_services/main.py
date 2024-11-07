# Стандартные библиотеки Python
import asyncio
import os
import sys
import json
import logging
import subprocess
import time
from datetime import datetime, timedelta
from sqlite3 import IntegrityError
from typing import Optional, List

# Сторонние библиотеки
import bcrypt
import jwt
import pytz
import requests
from bs4 import BeautifulSoup
from bson import ObjectId
from fastapi import FastAPI, Depends, Body, Query, Response, status, Request, BackgroundTasks, HTTPException, Cookie
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
from pymongo import MongoClient
from gridfs import GridFS
import ffmpeg

# Локальные модули
from database import User, SessionLocal, VideoDownload, init_db
from config import mongodb_adress
from services.kinescope_services.get_all_folders import save_structure
from services.schedule_service.get_archive_lectures_for_user import get_archive_lectures_main
from services.schedule_service.get_today_lectures_for_user import load_json, get_lectures_main
from services.zoom_service.create_task_for_download import cancel_scheduled_task
from services.zoom_service.meet_create.util import process_conference_data, converted_conference_from_file
from services.zoom_service.meet_delete.zoom_meeting_delete_api import delete_meeting
from services.zoom_service.meet_get_video.find_real_video_meeting.predict_conference import find_closest_meeting
from services.zoom_service.meet_get_video.zoom_meeting_get_records_list import run_task


SECRET_KEY = os.getenv("SECRET_KEY", "********************")
invite_code = "********************"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
EXCLUDE_PATHS = ["/api/register/", "/api/token", "/api/get-conference-video-list", "/api/zoom_service/start_download"]
class EmailRequest(BaseModel):
    email: str

app = FastAPI()

@app.middleware("http")
async def check_authentication(request: Request, call_next):
    # Если путь запроса в списке исключений, пропускаем его без проверки
    if request.url.path in EXCLUDE_PATHS:
        return await call_next(request)

    # Ищем токен в cookies
    token = request.cookies.get("access_token")
    if not token:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": "Not authenticated"})

    # Проверяем токен
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        request.state.user = payload.get("sub")  # Сохраняем информацию о пользователе в `request.state`
    except jwt.ExpiredSignatureError:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": "Token has expired"})
    except jwt.PyJWTError:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": "Token is invalid"})

    # Продолжаем обработку запроса
    response = await call_next(request)
    return response


'''####################################'''

address = f"mongodb://{mongodb_adress[0]}:{mongodb_adress[1]}"
client = MongoClient(address)
db = client.mds_workspace
conference_videos = db.conference_videos


# Настройка уровня логирования для SQLAlchemy
logging.getLogger('sqlalchemy').setLevel(logging.WARNING)

# Добавляем CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Указываем ваш фронтенд адрес
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


lms_courses_file_path = 'services/lms_services/lms_courses.json'
kinescope_folders_file_path = "services/kinescope_services/kinescope_folders.json"
zoom_meetings_file_path = 'services/zoom_service/meet_create/zoom_meetings.json'
linking_channels_file_path = 'services/telegram_services/linking_channels.json'
sheets_data_file_path = "services/schedule_service/sheets_data.json"
lecture_on_platform_file_path = "services/schedule_service/lecture_on_platform.json"


class UserRegistration(BaseModel):
    firstName: str
    lastName: str
    email: str
    password: str
    confirmPassword: str
    inviteCode: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

@app.post("/api/register/", response_model=Token)
async def register(user: UserRegistration, db: Session = Depends(get_db)):
    if user.password != user.confirmPassword:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    if user.inviteCode and not validate_invite_code(user.inviteCode):
        raise HTTPException(status_code=400, detail="Invalid invite code")

    hashed_password = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt()).decode('utf-8')

    new_user = User(
        first_name=user.firstName,
        last_name=user.lastName,
        email=user.email,
        password=hashed_password
    )

    db.add(new_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Failed to register user")

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": new_user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/token", response_model=Token)
async def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    response = JSONResponse(content={"access_token": access_token, "token_type": "bearer"})
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

@app.get("/api/protected-route")
async def protected_route(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

        return {"email": user.email, "first_name": user.first_name, "last_name": user.last_name}
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

def validate_invite_code(code: str) -> bool:
    return code == invite_code

@app.get("/api/schedule_service/today_lectures")
async def get_today_lectures(request: Request, db: Session = Depends(get_db)):
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Token missing")

    try:
        # Декодируем токен
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token is invalid")

    # Получаем пользователя по email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_id = user.id

    # Получаем сегодняшние лекции
    filtered_data = get_lectures_main(user_id)

    # Формируем результат из данных о лекциях
    result = []
    existing_data = load_json(lecture_on_platform_file_path)
    for item in existing_data:
        if item['id'] in [data['id'] for data in filtered_data]:
            result.append({
                "id": item['id'],
                **item['platform_lecture']
            })

    return result

@app.get("/api/schedule_service/archive_lectures")
async def get_archive_lectures(request: Request, db: Session = Depends(get_db)):
    # Извлечение токена из cookies
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Token missing")

    try:
        # Декодирование токена
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token is invalid")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token is invalid")

    # Поиск пользователя по email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_id = user.id

    # Получение архива лекций
    filtered_data = get_archive_lectures_main(user_id)

    # Формирование результата из platform_lecture
    result = []
    existing_data = load_json(lecture_on_platform_file_path)
    for item in existing_data:
        if item['id'] in [data['id'] for data in filtered_data]:
            result.append({
                "id": item['id'],
                **item['platform_lecture']
            })

    return result

@app.put("/api/schedule_service/update_lecture")
async def update_lecture(request: Request):
    update_data = await request.json()
    lecture_id = update_data.pop('id', None)

    if not lecture_id:
        raise HTTPException(status_code=400, detail="Lecture ID is required")

    existing_data = load_json(lecture_on_platform_file_path)

    found = False
    for item in existing_data:
        if item['id'] == lecture_id:
            item['platform_lecture'].update(update_data)
            found = True
            break

    if not found:
        raise HTTPException(status_code=404, detail="Lecture ID not found")

    with open(lecture_on_platform_file_path, 'w', encoding='utf-8') as file:
        json.dump(existing_data, file, ensure_ascii=False, indent=4)

    return {"detail": "Lecture updated successfully"}

@app.post("/api/schedule_service/reset_lecture")
async def reset_lecture(request: Request):
    update_data = await request.json()
    lecture_id = update_data.get('id', None)
    print(lecture_id)

    if not lecture_id:
        raise HTTPException(status_code=400, detail="Lecture ID is required")

    existing_data = load_json(lecture_on_platform_file_path)

    found = False
    for item in existing_data:
        if item['id'] == lecture_id:
            item['platform_lecture'] = item['google_sheets']
            found = True
            break

    if not found:
        raise HTTPException(status_code=404, detail="Lecture ID not found")

    with open(lecture_on_platform_file_path, 'w', encoding='utf-8') as file:
        json.dump(existing_data, file, ensure_ascii=False, indent=4)

    return {"detail": "Lecture reset successfully"}

from fastapi import Header, Cookie

@app.post("/api/zoom_service/create_meet")
async def create_meet(request: Request, db: Session = Depends(get_db)):
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Token missing")

    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token is invalid")

    data = await request.json()
    conference_id = data.get('conference_id')
    force_recreate = data.get('force_recreate', False)
    print("ПОЛУЧАЕМЫЕ ДАННЫЕ", data)

    if not conference_id:
        raise HTTPException(status_code=400, detail="Conference ID is required")

    # Получение пользователя по email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Получение данных о лекции
    lecture_data = get_lecture_data(conference_id)
    if not lecture_data:
        raise HTTPException(status_code=404, detail="Lecture not found")

    # Проверка наличия конференции
    if not force_recreate and check_conference_exists(conference_id):
        return {'status': 'conference_already_exists'}

    # Чтение существующих данных из файла
    try:
        with open(zoom_meetings_file_path, 'r', encoding='utf-8') as file:
            existing_data = json.load(file)
    except FileNotFoundError:
        existing_data = {}
    except json.JSONDecodeError:
        existing_data = {}

    # Извлечение и очистка stream
    stream = lecture_data.get('stream', '').strip().replace('\n', ' ')

    # Создание JSON-документа для Zoom конференции
    zoom_meeting_data = {
        str(conference_id): {
            "user_id": user.id,
            "tags": [stream],  # Добавляем очищенный stream в массив tags
            "meeting_info": lecture_data
        }
    }

    # Обновление данных или добавление новой записи
    existing_data.update(zoom_meeting_data)

    # Сохранение данных в файл
    with open(zoom_meetings_file_path, 'w', encoding='utf-8') as file:
        json.dump(existing_data, file, ensure_ascii=False, indent=4)

    response = converted_conference_from_file(conference_id)

    return response

def get_lecture_data(conference_id):
    existing_data = load_json(lecture_on_platform_file_path)

    for item in existing_data:
        if item['id'] == conference_id:
            return item['platform_lecture']
    return None



@app.get("/api/zoom_service/get_conference_data")
async def get_conference_data(conference_id: int, request: Request, db: Session = Depends(get_db)):
    # Извлечение токена из cookies
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Token missing")

    try:
        # Декодирование токена
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token is invalid")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token is invalid")

    # Поиск пользователя по email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Продолжение оригинальной логики
    with open(zoom_meetings_file_path, 'r', encoding='utf-8') as file:
        zoom_meetings = json.load(file)

    conference_id_str = str(conference_id)  # Преобразование conference_id в строку

    # Убедимся, что структура данных представляет собой словарь
    if isinstance(zoom_meetings, dict):
        # Первоначальная проверка на наличие conference_id
        if conference_id_str in zoom_meetings:
            formed_conference = zoom_meetings[conference_id_str].get("formed_conference", {})
            if formed_conference:
                children_lecture_ids = formed_conference.get("children_lecture_id", [])
                meeting_details = formed_conference.get("meeting_details", [{}])[0]
                response_data = {
                    "children_lecture_ids": children_lecture_ids,
                    "speaker": meeting_details.get("speaker"),
                    "theme": meeting_details.get("theme"),
                    "topic": meeting_details.get("topic"),
                    "email": meeting_details.get("email"),
                    "date": meeting_details.get("date"),
                    "link": meeting_details.get("link"),
                    "time_meeting": meeting_details.get("time_meeting"),
                    "id": meeting_details.get("id"),
                    "code": meeting_details.get("code"),
                    "inherited": False,
                    "conference_key": conference_id_str,  # Добавляем ключ конференции
                    "tags": zoom_meetings[conference_id_str].get("tags", [])
                }
                return {"meeting_details": [response_data]}

        # Проверка всех записей на наличие совпадения по children_lecture_id
        for key, value in zoom_meetings.items():
            children_lecture_ids = value.get("formed_conference", {}).get("children_lecture_id", [])
            if isinstance(children_lecture_ids, list) and conference_id_str in children_lecture_ids:
                formed_conference = value.get("formed_conference", {})
                if formed_conference:
                    meeting_details = formed_conference.get("meeting_details", [{}])[0]
                    response_data = {
                        "speaker": meeting_details.get("speaker"),
                        "theme": meeting_details.get("theme"),
                        "topic": meeting_details.get("topic"),
                        "email": meeting_details.get("email"),
                        "date": meeting_details.get("date"),
                        "link": meeting_details.get("link"),
                        "time_meeting": meeting_details.get("time_meeting"),
                        "id": meeting_details.get("id"),
                        "code": meeting_details.get("code"),
                        "inherited": True,
                        "conference_key": key,  # Добавляем ключ главной конференции
                        "tags": zoom_meetings[key].get("tags", [])
                    }
                    return {"meeting_details": [response_data]}

        return {"message": "Данные для конференции не найдены"}
    else:
        raise HTTPException(status_code=404, detail="Conference ID not found")


from fastapi import Request
from typing import List
from pydantic import BaseModel


class ConferenceDataRequest(BaseModel):
    conference_ids: List[int]


@app.post("/api/zoom_service/get_all_conference_data")
async def get_all_conference_data(request: Request, data: ConferenceDataRequest, db: Session = Depends(get_db)):
    conference_ids = data.conference_ids
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Token missing")

    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token is invalid")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token is invalid")

    # Поиск пользователя по email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Чтение данных конференций из файла
    with open(zoom_meetings_file_path, 'r', encoding='utf-8') as file:
        zoom_meetings = json.load(file)

    conference_data = {}

    # Получение данных для всех conference_ids
    for conference_id in conference_ids:
        conference_id_str = str(conference_id)

        if isinstance(zoom_meetings, dict):
            # Если ID найден напрямую
            if conference_id_str in zoom_meetings:
                formed_conference = zoom_meetings[conference_id_str].get("formed_conference", {})
                if formed_conference:
                    children_lecture_ids = formed_conference.get("children_lecture_id", [])
                    meeting_details = formed_conference.get("meeting_details", [{}])[0]
                    response_data = {
                        "children_lecture_ids": children_lecture_ids,
                        "speaker": meeting_details.get("speaker"),
                        "theme": meeting_details.get("theme"),
                        "topic": meeting_details.get("topic"),
                        "email": meeting_details.get("email"),
                        "date": meeting_details.get("date"),
                        "link": meeting_details.get("link"),
                        "time_meeting": meeting_details.get("time_meeting"),
                        "id": meeting_details.get("id"),
                        "code": meeting_details.get("code"),
                        "inherited": False,
                        "conference_key": conference_id_str,
                        "tags": zoom_meetings[conference_id_str].get("tags", [])
                    }
                    conference_data[conference_id_str] = {"meeting_details": [response_data]}
            else:
                for key, value in zoom_meetings.items():
                    children_lecture_ids = value.get("formed_conference", {}).get("children_lecture_id", [])
                    if isinstance(children_lecture_ids, list) and conference_id_str in children_lecture_ids:
                        formed_conference = value.get("formed_conference", {})
                        if formed_conference:
                            meeting_details = formed_conference.get("meeting_details", [{}])[0]
                            response_data = {
                                "speaker": meeting_details.get("speaker"),
                                "theme": meeting_details.get("theme"),
                                "topic": meeting_details.get("topic"),
                                "email": meeting_details.get("email"),
                                "date": meeting_details.get("date"),
                                "link": meeting_details.get("link"),
                                "time_meeting": meeting_details.get("time_meeting"),
                                "id": meeting_details.get("id"),
                                "code": meeting_details.get("code"),
                                "inherited": True,
                                "conference_key": key,
                                "tags": zoom_meetings[key].get("tags", [])
                            }
                            conference_data[conference_id_str] = {"meeting_details": [response_data]}

    return conference_data

class ConferenceIdsRequest(BaseModel):
    conference_ids: List[int]

def check_conference_exists(conference_id):
    try:
        with open(zoom_meetings_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except FileNotFoundError:
        print("File not found.")
        return False
    except json.JSONDecodeError:
        print("Error decoding JSON or file is empty.")
        return False

    conference_id_str = str(conference_id)
    if conference_id_str in data and 'formed_conference' in data[conference_id_str]:
        print(f"Conference {conference_id} exists with formed conference data.")
        return True
    else:
        print(f"Conference {conference_id} does not exist or has no formed conference data.")
        return False


@app.get("/api/telegram_service/get_channels")
async def get_channels():
    try:
        with open(linking_channels_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        channels = data.get("couples", {})
        global_exclude = data.get("global_exclude", [])
        return {"channels": channels, "global_exclude": global_exclude}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="linking_channels.json file not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error decoding JSON linking_channels.json")

@app.post("/api/telegram_service/update_channel_exclude")
async def update_channel_exclude(request: Request):
    update_data = await request.json()
    channel_id = update_data.get('channel_id')
    action = update_data.get('action')

    if not channel_id or action not in ["add", "remove"]:
        raise HTTPException(status_code=400, detail="Invalid data")


    try:
        with open(linking_channels_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Channels file not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error decoding JSON")

    if action == "add" and channel_id not in data["global_exclude"]:
        data["global_exclude"].append(channel_id)
    elif action == "remove" and channel_id in data["global_exclude"]:
        data["global_exclude"].remove(channel_id)

    with open(linking_channels_file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

    return {"global_exclude": data["global_exclude"]}

@app.get("/api/get_unique_tags")
async def get_unique_tags(request: Request, db: Session = Depends(get_db)):
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Token missing")

    try:
        # Декодирование токена
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token is invalid")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token is invalid")

    # Поиск пользователя по email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Загрузка уникальных тегов
    with open(sheets_data_file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    unique_tags = set()
    for key in data:
        for item in data[key]:
            tag = item['data'][0].replace('\n', ' ').strip()
            unique_tags.add(tag)

    return {"tags": list(unique_tags)}

@app.post("/api/telegram_service/update_channel_tags")
async def update_channel_tags(channel_id: str = Body(...), tags: list = Body(...)):
    try:
        with open(linking_channels_file_path, "r+", encoding="utf-8") as file:
            data = json.load(file)
            if channel_id in data["couples"]:
                data["couples"][channel_id]["tags"] = tags
                file.seek(0)
                json.dump(data, file, ensure_ascii=False, indent=4)
                file.truncate()
                return {"channel_id": channel_id, "tags": tags}
            else:
                raise HTTPException(status_code=404, detail="Channel not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/telegram_service/update_user_channel")
async def update_user_channel(request: Request, db: Session = Depends(get_db)):
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Token missing")

    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token is invalid")

    data = await request.json()
    channel_id = data.get('channel_id')
    action = data.get('action')

    if not channel_id or not action:
        raise HTTPException(status_code=400, detail="Channel ID and action are required")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_id = str(user.id)
    print(f"Channel ID: {channel_id}, Email: {email}, Action: {action}")

    try:
        with open(linking_channels_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        if action == 'add':
            if user_id in data["users_include"]:
                if channel_id not in data["users_include"][user_id]:
                    data["users_include"][user_id].append(channel_id)
            else:
                data["users_include"][user_id] = [channel_id]
        elif action == 'remove':
            if user_id in data["users_include"]:
                if channel_id in data["users_include"][user_id]:
                    data["users_include"][user_id].remove(channel_id)

        with open(linking_channels_file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

        return {"message": "Status updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/telegram_service/log_user_email")
async def log_user_email(request: Request, db: Session = Depends(get_db)):
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Token missing")

    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token is invalid")

    # Находим пользователя по email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        print(f"User with Email: {email} not found")
        raise HTTPException(status_code=404, detail="User not found")

    user_id = user.id
    print(f"User ID: {user_id}, Email: {email}")

    # Читаем данные из файла linking_channels.json
    try:
        with open(linking_channels_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Linking channels file not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error decoding JSON")

    # Получаем массив с ID каналов для данного пользователя
    user_channels = data.get('users_include', {}).get(str(user_id), [])
    print(f"Channels for User ID {user_id}: {user_channels}")

    return {"user_channels": user_channels}


from fastapi import Header, Cookie

@app.post("/api/user_channels")
async def get_user_channels(access_token: str = Cookie(None), db: Session = Depends(get_db)):
    if not access_token:
        raise HTTPException(status_code=401, detail="Token missing")

    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token is invalid")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_id = user.id

    try:
        with open(linking_channels_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Linking channels file not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error decoding JSON")

    user_channels = data.get('users_include', {}).get(str(user_id), [])
    channel_info = {channel_id: data["couples"].get(channel_id) for channel_id in user_channels}

    return {"user_channels": channel_info}

@app.post("/api/zoom_service/remove_tags")
async def remove_tags(request: Request):
    data = await request.json()
    conference_id = data.get('conference_id')
    tags = data.get('tags')

    if not conference_id or not tags:
        raise HTTPException(status_code=400, detail="Conference ID and tags are required")

    try:
        with open(zoom_meetings_file_path, 'r+', encoding='utf-8') as file:
            data = json.load(file)
            if conference_id in data:
                existing_tags = data[conference_id].get("tags", [])
                updated_tags = [tag for tag in existing_tags if tag not in tags]
                data[conference_id]["tags"] = updated_tags
                file.seek(0)
                json.dump(data, file, ensure_ascii=False, indent=4)
                file.truncate()
                return {"conference_id": conference_id, "tags": updated_tags}
            else:
                raise HTTPException(status_code=404, detail="Conference not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/zoom_service/add_tags")
async def add_tags(conference_id: str = Body(...), tags: list = Body(...)):
    try:
        with open(zoom_meetings_file_path, 'r+', encoding='utf-8') as file:
            data = json.load(file)
            if conference_id in data:
                existing_tags = data[conference_id].get("tags", [])
                updated_tags = list(set(existing_tags + tags))
                data[conference_id]["tags"] = updated_tags
                file.seek(0)
                json.dump(data, file, ensure_ascii=False, indent=4)
                file.truncate()
                return {"conference_id": conference_id, "tags": updated_tags}
            else:
                raise HTTPException(status_code=404, detail="Conference not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/zoom_service/update_children_lectures")
async def update_children_lectures(request: Request):
    data = await request.json()
    parent_id = str(data.get('parent_id'))
    children_ids = [str(child_id) for child_id in data.get('children_ids', [])]
    print(data)

    if not parent_id or not children_ids:
        raise HTTPException(status_code=400, detail="Parent ID and Children IDs are required")

    try:
        with open(zoom_meetings_file_path, 'r+', encoding='utf-8') as file:
            zoom_meetings = json.load(file)

            if parent_id in zoom_meetings:
                zoom_meetings[parent_id]['formed_conference']['children_lecture_id'] = children_ids

                # Сохраняем обновленные данные обратно в файл
                file.seek(0)
                json.dump(zoom_meetings, file, ensure_ascii=False, indent=4)
                file.truncate()

                # Возвращаем обновленные данные конференции
                response_data = zoom_meetings[parent_id]['formed_conference']
                return response_data
            else:
                raise HTTPException(status_code=404, detail="Parent Conference not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/zoom_service/remove_child_lecture")
async def remove_child_lecture(parent_id: int = Body(...), child_id: int = Body(...)):
    with open(zoom_meetings_file_path, 'r+', encoding='utf-8') as file:
        zoom_meetings = json.load(file)

        parent_id_str = str(parent_id)
        child_id_str = str(child_id)
        print(parent_id_str, child_id_str)

        if parent_id_str in zoom_meetings:
            children_lecture_ids = zoom_meetings[parent_id_str].get('formed_conference', {}).get('children_lecture_id',
                                                                                                 [])
            if child_id_str in children_lecture_ids:
                children_lecture_ids.remove(child_id_str)
                zoom_meetings[parent_id_str]['formed_conference']['children_lecture_id'] = children_lecture_ids

                file.seek(0)
                json.dump(zoom_meetings, file, ensure_ascii=False, indent=4)
                file.truncate()

                return {"status": "success", "message": "Child lecture removed successfully"}

        raise HTTPException(status_code=404, detail="Parent or child lecture not found")
class DeleteConferenceRequest(BaseModel):
    conference_id: str
    email: str
    meeting_id: str



@app.post("/api/zoom_service/delete_conference")
async def delete_conference(request: DeleteConferenceRequest):
    conference_id = request.conference_id
    email = request.email
    meeting_id = request.meeting_id
    try:
        with open(zoom_meetings_file_path, 'r+', encoding='utf-8') as file:
            zoom_meetings = json.load(file)

            if conference_id in zoom_meetings:
                del zoom_meetings[conference_id]

                file.seek(0)
                json.dump(zoom_meetings, file, ensure_ascii=False, indent=4)
                file.truncate()

                zoom_delete_result = delete_meeting(email, meeting_id)
                cancel_scheduled_task(meeting_id)

                if zoom_delete_result:
                    return {"status": "success", "message": "Конференция успешна удалена в Zoom"}
                else:
                    return {"status": "partial_success", "message": "Ошибка при удалении конференции в Zoom. \n Пожалуйста, зайди в Zoom и удали вручную"}
            else:
                raise HTTPException(status_code=404, detail="Conference not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class DownloadRequest(BaseModel):
    file_id: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def on_startup():
    init_db()
def get_file_title(file_url):
    try:
        response = requests.get(file_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        title_tag = soup.find('title')
        if title_tag:
            full_title = title_tag.text
            if " - Google Диск" in full_title:
                return full_title.replace(" - Google Диск", "")
            else:
                return full_title
        else:
            return "Title tag not found"
    except Exception as e:
        return f"Error: {e}"

@app.post("/api/download/")
async def start_download(request: DownloadRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    print(f"Received download request for file_id: {request.file_id}")

    file_url = f'https://drive.google.com/file/d/{request.file_id}/view'

    file_title = get_file_title(file_url)
    print(f"File title: {file_title}")

    file_type = "mp4"

    video_download = VideoDownload(file_id=request.file_id, file_name=file_title, file_type=file_type, download_status=0)
    db.add(video_download)
    db.commit()
    db.refresh(video_download)

    def run_download_script(file_id):
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'services/google_services/download_video_service/download_script.py')
        python_path = sys.executable  # Используем текущий интерпретатор Python
        result = subprocess.run([python_path, script_path, file_id], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error running script: {result.stderr}")
        else:
            print(f"Script output: {result.stdout}")

    background_tasks.add_task(run_download_script, request.file_id)
    return {"message": "Download started", "id": video_download.id, "file_name": video_download.file_name, "file_type": video_download.file_type}

@app.get("/api/downloads/")
async def get_downloads(db: Session = Depends(get_db)):
    downloads = db.query(VideoDownload).all()
    return downloads

@app.delete("/api/download/{file_id}")
async def delete_download(file_id: str, db: Session = Depends(get_db)):
    video_download = db.query(VideoDownload).filter_by(file_id=file_id).first()
    if not video_download:
        raise HTTPException(status_code=404, detail="Download not found")

    # Удаление файла с диска
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    downloads_folder_path = os.path.join(BASE_DIR, 'services/google_services/download_video_service/downloads', f"{file_id}.mp4")
    if os.path.exists(downloads_folder_path):
        try:
            os.remove(downloads_folder_path)
            print(f"File {downloads_folder_path} removed from disk.")
        except Exception as e:
            print(f"Error removing file {downloads_folder_path}: {e}")
            raise HTTPException(status_code=500, detail=f"Error removing file: {e}")
    else:
        print(f"File {downloads_folder_path} not found on disk.")

    # Удаление записи о загрузке из базы данных
    db.delete(video_download)
    db.commit()
    return {"message": "Download deleted"}

def load_existing_structure(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    else:
        return None

@app.get("/api/kinescope-folders")
async def get_kinescope_folders(request: Request, db: Session = Depends(get_db)):

    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Token missing")

    try:
        # Декодирование токена
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token is invalid")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token is invalid")

    # Поиск пользователя по email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    data = load_existing_structure(kinescope_folders_file_path)
    if data:
        return data
    else:
        return {"message": "Data not found"}

class UpdateTagsRequest(BaseModel):
    folder_id: str
    tags: list

@app.post("/api/update_tags")
async def update_tags(request: UpdateTagsRequest):
    data = load_existing_structure(kinescope_folders_file_path)
    if not data or request.folder_id not in data["couples"]:
        raise HTTPException(status_code=404, detail="Folder not found")

    data["couples"][request.folder_id]["tags"] = request.tags
    save_structure(kinescope_folders_file_path, data)

    return data["couples"][request.folder_id]


'''ПОТОКИ СТАРОЙ LMS'''
@app.get("/api/lk_service/get_streams")
async def get_streams(request: Request, db: Session = Depends(get_db)):
    # Извлечение токена из cookies
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Token missing")

    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token is invalid")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token is invalid")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        with open(lms_courses_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        streams = data.get("couples", {})
        global_exclude = data.get("global_exclude", [])
        return {"streams": streams, "global_exclude": global_exclude}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="old_lms_courses.json file not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error decoding JSON old_lms_courses.json")

@app.post("/api/lk_service/update_stream_exclude")
async def update_stream_exclude(request: Request):
    update_data = await request.json()
    stream_id = update_data.get('stream_id')
    action = update_data.get('action')

    if not stream_id or action not in ["add", "remove"]:
        raise HTTPException(status_code=400, detail="Invalid data")

    try:
        with open(lms_courses_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Streams file not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error decoding JSON")

    if action == "add" and stream_id not in data["global_exclude"]:
        data["global_exclude"].append(stream_id)
    elif action == "remove" and stream_id in data["global_exclude"]:
        data["global_exclude"].remove(stream_id)

    with open(lms_courses_file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

    return {"global_exclude": data["global_exclude"]}

@app.post("/api/lk_service/update_stream_tags")
async def update_stream_tags(stream_id: str = Body(...), tags: list = Body(...)):
    try:
        with open(lms_courses_file_path, "r+", encoding="utf-8") as file:
            data = json.load(file)
            if stream_id in data["couples"]:
                data["couples"][stream_id]["tags"] = tags
                file.seek(0)
                json.dump(data, file, ensure_ascii=False, indent=4)
                file.truncate()
                return {"stream_id": stream_id, "tags": tags}
            else:
                raise HTTPException(status_code=404, detail="Stream not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/lk_service/log_user_email")
async def lk_log_user_email(request: Request, db: Session = Depends(get_db)):
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Token missing")

    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token is invalid")

    # Находим пользователя по email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        print(f"User with Email: {email} not found")
        raise HTTPException(status_code=404, detail="User not found")

    user_id = user.id
    print(f"User ID: {user_id}, Email: {email}")

    try:
        with open(lms_courses_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Linking streams file not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error decoding JSON")

    # Получаем массив с ID каналов для данного пользователя
    user_streams = data.get('users_include', {}).get(str(user_id), [])
    print(f"Streams for User ID {user_id}: {user_streams}")

    return {"user_streams": user_streams}

@app.post("/api/lk_service/update_user_stream")
async def update_user_stream(request: Request, db: Session = Depends(get_db)):
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Token missing")

    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token is invalid")

    data = await request.json()
    stream_id = data.get('stream_id')
    action = data.get('action')

    if not stream_id or not action:
        raise HTTPException(status_code=400, detail="Stream ID and action are required")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_id = str(user.id)
    print(f"Stream ID: {stream_id}, Email: {email}, Action: {action}")

    try:
        with open(lms_courses_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        if action == 'add':
            if user_id in data["users_include"]:
                if stream_id not in data["users_include"][user_id]:
                    data["users_include"][user_id].append(stream_id)
            else:
                data["users_include"][user_id] = [stream_id]
        elif action == 'remove':
            if user_id in data["users_include"]:
                if stream_id in data["users_include"][user_id]:
                    data["users_include"][user_id].remove(stream_id)

        with open(lms_courses_file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

        return {"message": "Status updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


'''РАБОТА С ЗАПИСЯМИ КОНФЕРЕНЦИЙ В ZOOM'''
def convert_objectid_to_str(obj):
    """Конвертирует ObjectId в строку."""
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: convert_objectid_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid_to_str(i) for i in obj]
    return obj

@app.post("/api/get-conference-video-list")
async def get_conference_video_list(request: Request):
    data = await request.json()
    lecture_id = str(data.get('lectureId'))
    print(f"Received lecture ID: {lecture_id}")

    # Загрузка данных из zoom_meetings.json
    try:
        with open(zoom_meetings_file_path, 'r', encoding='utf-8') as file:
            zoom_meetings = json.load(file)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="zoom_meetings.json file not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error decoding JSON")

    # Поиск структуры по lecture_id
    if lecture_id in zoom_meetings:
        meeting_details = zoom_meetings[lecture_id].get("formed_conference", {}).get("meeting_details", [])
        if meeting_details:
            meeting_id = meeting_details[0].get("id", "")
            email = meeting_details[0].get("email", "")
            date = meeting_details[0].get("date", "")
            time_meeting = meeting_details[0].get("time_meeting", "")
            print(f"Meeting ID: {meeting_id}, Email: {email}, Date: {date}, Time: {time_meeting}")

            # Удаление всех пробелов
            meeting_id_cleaned = meeting_id.replace(" ", "")
            print(f"Cleaned meeting ID: {meeting_id_cleaned}, Email: {email}")

            # Парсинг даты и времени
            date_str = date.split(", ")[1]  # "14.08.24"
            start_time_str, end_time_str = time_meeting.split(" - ")  # "19:00", "20:30"
            combined_start = f"{date_str} {start_time_str}"
            combined_end = f"{date_str} {end_time_str}"

            # Парсинг в объекты datetime
            local_timezone = pytz.timezone("Europe/Moscow")
            start_time = local_timezone.localize(datetime.strptime(combined_start, "%d.%m.%y %H:%M"))
            end_time = local_timezone.localize(datetime.strptime(combined_end, "%d.%m.%y %H:%M"))

            # Перевод времени в UTC
            start_time_utc = start_time.astimezone(pytz.utc)
            end_time_utc = end_time.astimezone(pytz.utc)

            print(f"Start Time UTC: {start_time_utc}, End Time UTC: {end_time_utc}")

            # Получение данных из базы данных
            meeting_data_from_db = conference_videos.find_one({"meeting_id": meeting_id_cleaned})

            if not meeting_data_from_db:
                return {"status_code": 204, "message": "No data found for this meeting ID in the database."}

            # Извлекаем конференции и даты их начала и конца из базы данных
            conferences = []
            for uuid, details in meeting_data_from_db.get("meetings", {}).items():
                for recording in details.get("recordings", []):
                    if recording["recording_type"] == "shared_screen_with_speaker_view":
                        conferences.append({
                            "uuid": uuid,
                            "start": recording["start_time"],
                            "end": recording["end_time"]
                        })

            start_time_utc_str = start_time_utc.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
            end_time_utc_str = end_time_utc.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

            closest_conference = find_closest_meeting(conferences, start_time_utc_str, end_time_utc_str)

            if closest_conference:
                closest_uuid = closest_conference['uuid']
                print(f"Closest Conference UUID: {closest_uuid}")

                meeting_data_from_db["closest_conference_uuid"] = closest_uuid
            meeting_data_from_db = convert_objectid_to_str(meeting_data_from_db)

            if "meetings" in meeting_data_from_db:
                for uuid, details in meeting_data_from_db["meetings"].items():
                    if details["status"] == "processing":
                        details["processing"] = True

            print("Final Meeting Data with Closest Conference UUID:")
            print(json.dumps(meeting_data_from_db, indent=4, ensure_ascii=False))

            return meeting_data_from_db
        else:
            return {"status_code": 204, "message": "Meeting details not found."}
    else:
        return {"status_code": 404, "message": "Lecture ID not found in zoom_meetings.json."}



schedule_file_path = "services/schedule_service/exclude_settings.json"


class UpdateExcludeRequest(BaseModel):
    schedule_id: str
    action: str

class UpdateUserScheduleRequest(BaseModel):
    schedule_id: str
    action: str

# Модель для логирования email пользователя
class EmailRequest(BaseModel):
    email: str

@app.get("/api/schedule/get_schedules")
async def get_schedules(request: Request, db: Session = Depends(get_db)):
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Token missing")
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token is invalid")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token is invalid")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        with open(schedule_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        for schedule in data.get("schedules", []):
            if 'name' not in schedule:
                schedule['name'] = "Unnamed"
        return {
            "schedules": data.get("schedules", []),
            "global_exclude": data.get("global_exclude", []),
            "users_exclude": data.get("users_exclude", {}),
            "all_lists": data.get("all_lists", [])
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Schedule file not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error decoding JSON")

@app.post("/api/schedule/log_user_email")
async def log_user_email(request: Request, db: Session = Depends(get_db)):
    """
    Получить расписания, которые добавил пользователь.
    """
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Token missing")

    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token is invalid")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_id = str(user.id)
    try:
        with open(schedule_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        user_schedules = data.get('users_exclude', {}).get(user_id, [])
        return {"user_schedules": user_schedules}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Schedule file not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error decoding JSON")

@app.post("/api/schedule_service/update_schedule_exclude")
async def update_schedule_exclude(request: UpdateExcludeRequest):
    """
    Обновление статуса включения или исключения расписания.
    """
    try:
        with open(schedule_file_path, 'r+', encoding='utf-8') as file:
            data = json.load(file)
            schedule_id = request.schedule_id
            action = request.action

            if action == "add":
                if schedule_id not in data["global_exclude"]:
                    data["global_exclude"].append(schedule_id)
            elif action == "remove":
                if schedule_id in data["global_exclude"]:
                    data["global_exclude"].remove(schedule_id)
            else:
                raise HTTPException(status_code=400, detail="Invalid action")

            file.seek(0)
            json.dump(data, file, ensure_ascii=False, indent=4)
            file.truncate()

            return {"global_exclude": data["global_exclude"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/schedule_service/update_user_schedule")
async def update_user_schedule(
    request: Request,
    update_request: UpdateUserScheduleRequest,
    db: Session = Depends(get_db)
):
    """
    Обновление расписаний пользователя.
    """
    # Получаем токен из запроса
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Token missing")
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token is invalid")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_id = str(user.id)
    schedule_id = update_request.schedule_id
    action = update_request.action

    try:
        with open(schedule_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        if action == 'add':
            if user_id in data["users_exclude"]:
                if schedule_id not in data["users_exclude"][user_id]:
                    data["users_exclude"][user_id].append(schedule_id)
            else:
                data["users_exclude"][user_id] = [schedule_id]
        elif action == 'remove':
            if user_id in data["users_exclude"]:
                if schedule_id in data["users_exclude"][user_id]:
                    data["users_exclude"][user_id].remove(schedule_id)

        with open(schedule_file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

        return {"message": "Status updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


#####################################
# Работа с видеофайлами - воспроизведение, обрезка, отмена обрезки
#####################################

def get_mongo_collections():
    """Инициализация подключения к MongoDB и GridFS коллекциям."""
    client = MongoClient(f"mongodb://{mongodb_adress[0]}:{mongodb_adress[1]}")
    db = client['zoom_files']
    screen_fs = GridFS(db, collection='shared_screen_with_speaker_view')
    audio_fs = GridFS(db, collection='audio_only')
    chat_fs = GridFS(db, collection='chat_file')
    return screen_fs, audio_fs, chat_fs


@app.get("/api/get-recording")
async def get_recording(recording_id: str, conference_uuid: str, range: str = None):
    # Подключение к базе данных
    client = MongoClient(f"mongodb://{mongodb_adress[0]}:{mongodb_adress[1]}")
    db = client['mds_workspace']
    conference_videos = db.conference_videos

    # Поиск документа и проверка на trim
    document = conference_videos.find_one({f"meetings.{conference_uuid}": {"$exists": True}})
    if document:
        uuid_content = document["meetings"].get(conference_uuid, {})
        recordings = uuid_content.get("recordings", [])
        for recording in recordings:
            if recording.get("recording_id") == recording_id and recording.get("trim", False):
                recording_id = f"{recording_id}_trimmed"
                break

    # Ищем файл записи в MongoDB (zoom_files) и получаем путь к файлу
    client = MongoClient(f"mongodb://{mongodb_adress[0]}:{mongodb_adress[1]}")
    zoom_files_db = client['zoom_files']
    file_record = zoom_files_db['shared_screen_with_speaker_view.files'].find_one({"recording_id": recording_id})

    if not file_record:
        file_record = zoom_files_db['audio_only.files'].find_one({"recording_id": recording_id})

    if not file_record:
        file_record = zoom_files_db['chat_file.files'].find_one({"recording_id": recording_id})

    if not file_record:
        raise HTTPException(status_code=404, detail="Recording not found")

    relative_file_path = file_record.get("file_path")
    if not relative_file_path:
        raise HTTPException(status_code=404, detail="File path not found in the record")

    base_directory = os.path.abspath(os.path.dirname(__file__))
    absolute_file_path = os.path.join(base_directory, relative_file_path)

    # Проверка существования файла по абсолютному пути
    if not os.path.exists(absolute_file_path):
        raise HTTPException(status_code=404, detail="File not found on server")

    # Путь для сжатого видео
    compressed_file_path = os.path.join(base_directory, "downloads", "compressed", f"compressed_{recording_id}.mp4")

    # Если сжатое видео отсутствует, делаем запрос на сервер сжатия
    if not os.path.exists(compressed_file_path):
        try:
            with open(absolute_file_path, "rb") as video_file:
                response = requests.post("http://localhost:8005/compress-video/", files={"file": video_file})

            if response.status_code == 200:
                # Сохраняем сжатое видео
                os.makedirs(os.path.dirname(compressed_file_path), exist_ok=True)
                with open(compressed_file_path, "wb") as f:
                    f.write(response.content)
            else:
                print("Сервис сжатия вернул ошибку, отправляем оригинальное видео.")
        except requests.exceptions.RequestException:
            print("Сервис сжатия недоступен, отправляем оригинальное видео.")

    # Выбираем файл для отправки: сжатое или оригинальное
    file_path_to_serve = compressed_file_path if os.path.exists(compressed_file_path) else absolute_file_path
    file_size = os.path.getsize(file_path_to_serve)
    start, end = 0, file_size - 1

    if range:
        range_str = range.replace("bytes=", "")
        range_parts = range_str.split("-")
        if range_parts[0]:
            start = int(range_parts[0])
        if range_parts[1]:
            end = int(range_parts[1])

    chunk_size = end - start + 1

    # Функция для создания итератора файла
    def file_iterator(file_path, start, chunk_size):
        with open(file_path, 'rb') as file:
            file.seek(start)
            while chunk_size > 0:
                chunk = file.read(min(8192, chunk_size))
                if not chunk:
                    break
                yield chunk
                chunk_size -= len(chunk)

    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(chunk_size),
        "Content-Type": "video/mp4",
    }
    return StreamingResponse(file_iterator(file_path_to_serve, start, chunk_size), headers=headers, status_code=206)


def get_mongo_collections():
    client = MongoClient(f"mongodb://{mongodb_adress[0]}:{mongodb_adress[1]}")
    db = client['zoom_files']
    screen_fs = GridFS(db, collection='shared_screen_with_speaker_view')
    audio_fs = GridFS(db, collection='audio_only')
    chat_fs = GridFS(db, collection='chat_file')
    return screen_fs, audio_fs, chat_fs

def get_file_chunk(file_collection, file_id, start: int = 0, end: int = None):
    file_obj = file_collection.get(file_id)
    if end is None:
        end = file_obj.length
    file_obj.seek(start)
    chunk = file_obj.read(end - start)
    return chunk, end

def get_mongo_collections():
    client = MongoClient(f"mongodb://{mongodb_adress[0]}:{mongodb_adress[1]}")
    db = client['zoom_files']
    screen_fs = GridFS(db, collection='shared_screen_with_speaker_view')
    audio_fs = GridFS(db, collection='audio_only')
    chat_fs = GridFS(db, collection='chat_file')
    return screen_fs, audio_fs, chat_fs


def trim_video_and_save_info(recording_id, uuid, start_time, end_time, document, client):
    """Функция для обрезки видео и обновления базы данных."""
    db = client['mds_workspace']
    conference_videos = db.conference_videos
    zoom_files_db = client['zoom_files']

    # Поиск пути к файлу в коллекции MongoDB (zoom_files)
    file_record = zoom_files_db['shared_screen_with_speaker_view.files'].find_one({"recording_id": recording_id})
    if not file_record:
        file_record = zoom_files_db['audio_only.files'].find_one({"recording_id": recording_id})
    if not file_record:
        file_record = zoom_files_db['chat_file.files'].find_one({"recording_id": recording_id})

    if not file_record:
        # Сброс флага в случае ошибки
        conference_videos.update_one(
            {"_id": document["_id"], f"meetings.{uuid}.recordings.recording_id": recording_id},
            {"$set": {f"meetings.{uuid}.recordings.$.trimming_in_progress": False}}
        )
        raise HTTPException(status_code=404, detail="Recording not found in metadata")

    # Получаем относительный путь к файлу
    relative_file_path = file_record.get("file_path")
    if not relative_file_path:
        # Сброс флага в случае ошибки
        conference_videos.update_one(
            {"_id": document["_id"], f"meetings.{uuid}.recordings.recording_id": recording_id},
            {"$set": {f"meetings.{uuid}.recordings.$.trimming_in_progress": False}}
        )
        raise HTTPException(status_code=404, detail="File path not found in the record")

    # Преобразование относительного пути в абсолютный
    base_directory = os.path.abspath(os.path.dirname(__file__))  # Корневая директория приложения
    absolute_file_path = os.path.join(base_directory, relative_file_path)

    # Проверка существования файла по абсолютному пути
    if not os.path.exists(absolute_file_path):
        # Сброс флага в случае ошибки
        conference_videos.update_one(
            {"_id": document["_id"], f"meetings.{uuid}.recordings.recording_id": recording_id},
            {"$set": {f"meetings.{uuid}.recordings.$.trimming_in_progress": False}}
        )
        raise HTTPException(status_code=404, detail="File not found on server")

    # Проверка существования выходного файла перед обрезкой
    output_filename = f"{os.path.splitext(absolute_file_path)[0]}_trimmed.mp4"
    if os.path.exists(output_filename):
        print(f"Existing trimmed file found, removing: {output_filename}")
        os.remove(output_filename)

    try:
        print("Starting video trim with ffmpeg...")
        (
            ffmpeg
            .input(absolute_file_path, ss=start_time, to=end_time)
            .output(output_filename, codec="copy")
            .run()
        )
        print("Video trimmed successfully.")
    except ffmpeg.Error as e:

        conference_videos.update_one(
            {"_id": document["_id"], f"meetings.{uuid}.recordings.recording_id": recording_id},
            {"$set": {f"meetings.{uuid}.recordings.$.trimming_in_progress": False}}
        )
        raise HTTPException(status_code=500, detail=f"Error trimming video: {str(e)}")

    trimmed_file_path = os.path.abspath(output_filename)
    zoom_files_db['shared_screen_with_speaker_view.files'].update_one(
        {"recording_id": recording_id + "_trimmed"},
        {
            "$set": {
                "filename": output_filename,
                "file_path": trimmed_file_path,
                "meeting_uuid": uuid,
                "recording_type": file_record.get("recording_type", "unknown")
            }
        },
        upsert=True
    )

    conference_videos.update_one(
        {"_id": document["_id"], f"meetings.{uuid}.recordings.recording_id": recording_id},
        {"$set": {f"meetings.{uuid}.recordings.$.trimming_in_progress": False,
                  f"meetings.{uuid}.recordings.$.trim": True}}
    )

    print("Видео успешно обрезано и сохранено, статус обновлен в базе данных.")
    return {"message": "Видео обрезано и сохранено на сервере", "output_file": output_filename}


@app.post("/api/log-trim-info")
async def trim_and_save_video(request: Request):
    try:
        data = await request.json()
        recording_id = data.get('recording_id')
        uuid = data.get('uuid')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        print(f"Received data: {recording_id}, {uuid}, {start_time}, {end_time}")

        if not recording_id or not uuid:
            raise HTTPException(status_code=400, detail="Recording ID and UUID are required")


        client = MongoClient(f"mongodb://{mongodb_adress[0]}:{mongodb_adress[1]}")
        db = client['mds_workspace']
        conference_videos = db.conference_videos

        document = conference_videos.find_one_and_update(
            {f"meetings.{uuid}.recordings.recording_id": recording_id,
             f"meetings.{uuid}.recordings.trimming_in_progress": {"$ne": True}},
            {"$set": {f"meetings.{uuid}.recordings.$.trimming_in_progress": True}},
            return_document=True
        )

        if not document:
            raise HTTPException(status_code=409,
                                detail="Trimming is already in progress for this recording or recording not found.")

        result = await asyncio.to_thread(trim_video_and_save_info, recording_id, uuid, start_time, end_time, document,
                                         client)
        return result

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.post("/api/cancel-trim")
async def cancel_trim(request: Request):
    try:
        data = await request.json()
        recording_id = data.get('recording_id')
        uuid = data.get('uuid')

        client = MongoClient(f"mongodb://{mongodb_adress[0]}:{mongodb_adress[1]}")
        db = client['mds_workspace']
        conference_videos = db.conference_videos
        zoom_files_db = client['zoom_files']

        document = conference_videos.find_one({f"meetings.{uuid}": {"$exists": True}})
        if document:
            uuid_content = document["meetings"].get(uuid, {})
            for recording in uuid_content.get("recordings", []):
                if recording.get("recording_id") == recording_id:
                    if recording.get("trimming_in_progress", False):
                        raise HTTPException(status_code=409, detail="Cannot cancel trim while trimming is in progress.")

                    recording.pop("trim", None)
                    conference_videos.update_one(
                        {"_id": document["_id"]},
                        {"$set": {f"meetings.{uuid}.recordings": uuid_content["recordings"]}}
                    )
                    print(f"Обрезка отменена для записи с recording_id: {recording_id}.")
                    trimmed_record = zoom_files_db['shared_screen_with_speaker_view.files'].find_one({"recording_id": recording_id + "_trimmed"})
                    if not trimmed_record:
                        trimmed_record = zoom_files_db['audio_only.files'].find_one({"recording_id": recording_id + "_trimmed"})
                    if not trimmed_record:
                        trimmed_record = zoom_files_db['chat_file.files'].find_one({"recording_id": recording_id + "_trimmed"})

                    if trimmed_record:
                        trimmed_file_path = trimmed_record.get("file_path")
                        if trimmed_file_path and os.path.exists(trimmed_file_path):
                            os.remove(trimmed_file_path)
                            print(f"Обрезанное видео с ID {recording_id}_trimmed удалено с сервера.")

                        zoom_files_db['shared_screen_with_speaker_view.files'].delete_one({"_id": trimmed_record["_id"]})
                        print(f"Запись об обрезанном видео удалена из базы данных.")

                    return {"message": "Обрезка отменена и обрезанное видео удалено."}

        raise HTTPException(status_code=404, detail="Recording ID not found.")

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
