import config
import asyncio
import json
from telethon import TelegramClient
import os

async def get_channels():
    async with TelegramClient(config.session_name, config.api_id, config.api_hash) as client:
        channels = []
        async for dialog in client.iter_dialogs():
            if dialog.is_channel and not dialog.is_group:
                channels.append({"id": dialog.id, "name": dialog.name})
                print(f"Channel name: {dialog.name}, Channel ID: {dialog.id}")
        return channels

def update_json_file(channels):
    json_file_path = 'linking_channels.json'

    # Чтение существующего файла
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {"global_exclude": [], "users_include": {}, "couples": {}}
    except json.JSONDecodeError:
        data = {"global_exclude": [], "users_include": {}, "couples": {}}

    # Обновление данных
    for channel in channels:
        channel_id = str(channel["id"])
        if channel_id not in data["couples"]:
            data["couples"][channel_id] = {"name": channel["name"], "tags": []}

    # Запись обновленных данных в файл
    with open(json_file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

async def main():
    channels = await get_channels()
    update_json_file(channels)

if __name__ == '__main__':
    asyncio.run(main())
