import config
import asyncio
from telethon import TelegramClient
from telethon.tl.functions.channels import CreateChannelRequest, EditPhotoRequest
from telethon.tl.functions.messages import ExportChatInviteRequest, EditChatDefaultBannedRightsRequest
from telethon.tl.types import InputPeerChannel, InputChatUploadedPhoto, ChatBannedRights
import os

async def create_chats(names):
    async with TelegramClient(config.session_name, config.api_id, config.api_hash) as client:
        chat_links = {}

        for name in names:
            # Создаем чат
            chat_result = await client(CreateChannelRequest(
                title=name,
                about='',
                megagroup=True
            ))
            chat = chat_result.chats[0]
            print(f"Chat '{name}' created successfully!")

            # Сохраняем идентификаторы сообщений о создании чата
            chat_message_ids = [msg.id for msg in chat_result.updates if hasattr(msg, 'id')]

            # Устанавливаем обложку для чата
            chat_logo_path = os.path.join(os.path.dirname(__file__), 'chat_logo.jpg')
            chat_file = await client.upload_file(chat_logo_path)
            logo_result = await client(EditPhotoRequest(
                channel=InputPeerChannel(channel_id=chat.id, access_hash=chat.access_hash),
                photo=InputChatUploadedPhoto(chat_file)
            ))
            print(f"Chat '{name}' logo set successfully!")

            # Добавляем идентификаторы сообщений о смене логотипа
            chat_message_ids += [msg.id for msg in logo_result.updates if hasattr(msg, 'id')]

            # Разрешаем просмотр истории для новых участников
            await client(EditChatDefaultBannedRightsRequest(
                peer=InputPeerChannel(channel_id=chat.id, access_hash=chat.access_hash),
                banned_rights=ChatBannedRights(until_date=None, view_messages=False)
            ))
            print(f"Chat '{name}' history made visible to new members!")

            # Получаем пригласительную ссылку для чата
            invite = await client(ExportChatInviteRequest(
                peer=InputPeerChannel(channel_id=chat.id, access_hash=chat.access_hash)
            ))
            invite_link = invite.link
            chat_links[name] = invite_link

            # Удаляем уведомительные сообщения о создании чата и обновлении логотипа
            await client.delete_messages(chat, chat_message_ids)
            print(f"Notification messages for '{name}' deleted successfully!")

        # Выводим названия чатов и ссылки на них с визуальным разделением
        for name, link in chat_links.items():
            print(f"\033[94m\033[1m{name}\033[0m")  # Синий цвет для названия чата
            print(f"\033[92m{link}\033[0m")         # Зеленый цвет для ссылки
            print("\033[90m" + "-" * 50 + "\033[0m")  # Серая линия-разделитель

if __name__ == '__main__':
    # Пример использования
    chat_names = ["Название канала"]
    asyncio.run(create_chats(chat_names))