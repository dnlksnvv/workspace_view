# run.py

import uvicorn
from config import this_port

if __name__ == "__main__":
    uvicorn.run(
        "main:app",  # Указываем основной файл и приложение FastAPI
        host="0.0.0.0",  # Открываем сервер на всех интерфейсах
        port=this_port,  # Используем порт из конфигурации
        reload=True  # Включаем автоматическую перезагрузку при изменении кода
    )