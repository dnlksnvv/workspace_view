import config
import asyncio
from telethon import TelegramClient
from telethon.tl.functions.channels import CreateChannelRequest, EditPhotoRequest, DeleteMessagesRequest
from telethon.tl.functions.messages import ExportChatInviteRequest
from telethon.tl.types import InputPeerChannel, InputChatUploadedPhoto

import os

async def create_channel_and_chat(name):
    async with TelegramClient(config.session_name, config.api_id, config.api_hash) as client:
        channel_result = await client(CreateChannelRequest(
            title=name,
            about='',
            megagroup=False
        ))
        channel = channel_result.chats[0]
        channel_message_ids = [msg.id for msg in channel_result.updates if hasattr(msg, 'id')]
        print("Channel created successfully!")

        channel_logo_path = os.path.join(os.path.dirname(__file__), 'channel_logo.jpg')
        channel_file = await client.upload_file(channel_logo_path)
        logo_result = await client(EditPhotoRequest(
            channel=InputPeerChannel(channel_id=channel.id, access_hash=channel.access_hash),
            photo=InputChatUploadedPhoto(channel_file)
        ))
        channel_message_ids += [msg.id for msg in logo_result.updates if hasattr(msg, 'id')]
        print("Channel logo set successfully!")

        chat_result = await client(CreateChannelRequest(
            title=name + ' Chat',
            about='',
            megagroup=True
        ))
        chat = chat_result.chats[0]
        chat_message_ids = [msg.id for msg in chat_result.updates if hasattr(msg, 'id')]
        print("Chat created successfully!")

        chat_logo_path = os.path.join(os.path.dirname(__file__), 'chat_logo.jpg')
        chat_file = await client.upload_file(chat_logo_path)
        logo_result = await client(EditPhotoRequest(
            channel=InputPeerChannel(channel_id=chat.id, access_hash=chat.access_hash),
            photo=InputChatUploadedPhoto(chat_file)
        ))
        chat_message_ids += [msg.id for msg in logo_result.updates if hasattr(msg, 'id')]
        print("Chat logo set successfully!")

        invite = await client(ExportChatInviteRequest(
            peer=InputPeerChannel(channel_id=chat.id, access_hash=chat.access_hash)
        ))
        invite_link = invite.link


        message = await client.send_message(channel, f"ЧАТ: {invite_link}")
        print("Invite link sent to the channel successfully!")
        channel_invite = await client(ExportChatInviteRequest(
            peer=InputPeerChannel(channel_id=channel.id, access_hash=channel.access_hash)
        ))
        channel_invite_link = channel_invite.link

        await client(DeleteMessagesRequest(channel, channel_message_ids))
        await client(DeleteMessagesRequest(chat, chat_message_ids))

        red_text = '\033[91m'
        red_border = '\033[91m\033[1m'
        reset = '\033[0m'

        # Выводим ссылки и ID в красной рамке
        print(f'{red_border}{"=" * 50}{reset}')
        print(f'{red_text}ОБЯЗАТЕЛЬНО: ПРИВЯЖИ ЧАТ К КАНАЛУ И ДОБАВЬ ПРИГЛАСИТЕЛЬНУЮ ССЫЛКУ В РЕЕСТР И НАБОРЫ{reset}')
        print(f'{red_text}КАНАЛ invite link: {channel_invite_link}{reset}')
        print(f'{red_text}Channel ID: {channel.id}{reset}')
        print(f'{red_border}{" " * 50}{reset}')
        print(f'{red_text}ЧАТ invite link: {invite_link}{reset}')
        print(f'{red_text}Chat ID: {chat.id}{reset}')
        print(f'{red_border}{"=" * 50}{reset}')



if __name__ == '__main__':
    asyncio.run(create_channel_and_chat("Юрист по ВЭД - 11 поток"))
