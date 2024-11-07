# run.py
import asyncio

import uvicorn
from config import this_port
from telegram_bot import start_bot

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=this_port,
        reload=True
    )
    asyncio.run(start_bot())
