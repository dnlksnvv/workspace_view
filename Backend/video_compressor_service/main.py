from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import os
import subprocess
import uuid

app = FastAPI()

# Директория для хранения временных сжатых файлов
COMPRESSED_DIR = "compressed_videos"
os.makedirs(COMPRESSED_DIR, exist_ok=True)

def cleanup_files(*file_paths):
    """Удаляет временные файлы после завершения запроса."""
    for file_path in file_paths:
        if os.path.exists(file_path):
            os.remove(file_path)

@app.post("/compress-video/")
async def compress_video(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    video_id = str(uuid.uuid4())
    input_path = f"{COMPRESSED_DIR}/{video_id}_input.mp4"
    output_path = f"{COMPRESSED_DIR}/{video_id}_compressed.mp4"

    # Сохраняем загруженный файл
    with open(input_path, "wb") as buffer:
        buffer.write(await file.read())

    ffmpeg_cmd = [
        "ffmpeg", "-i", input_path,
        "-vf", "scale=640:360",  # Устанавливаем разрешение (можно изменить)
        "-r", "15",  # Частота кадров, например 15
        "-b:a", "32k",  # Битрейт для аудио
        "-vcodec", "libx264",  # Использование кодека H.264 на процессоре
        "-preset", "fast",  # Быстрый пресет для ускорения сжатия
        "-crf", "30",  # Уровень сжатия по качеству
        output_path
    ]

    try:
        subprocess.run(ffmpeg_cmd, check=True)
    except subprocess.CalledProcessError:
        os.remove(input_path)  # Удаление исходного файла в случае ошибки
        raise HTTPException(status_code=500, detail="Video compression failed")

    # Добавляем задачу для очистки файлов после завершения запроса
    background_tasks.add_task(cleanup_files, input_path, output_path)

    return FileResponse(output_path, media_type="video/mp4", filename="compressed_video.mp4")