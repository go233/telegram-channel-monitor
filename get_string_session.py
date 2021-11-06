import os

from dotenv import load_dotenv

from telethon.sync import TelegramClient
from telethon.sessions import StringSession

load_dotenv()

proxy = {}
if os.getenv("PROXY_ADDR"):
    proxy = {
        'proxy_type': 'socks5',
        'addr': os.getenv("PROXY_ADDR"),
        'port': int(os.getenv("PROXY_PORT"))
    }


with TelegramClient(StringSession(), os.getenv("API_ID"), os.getenv("API_HASH"), proxy=proxy) as client:
    print(client.session.save())