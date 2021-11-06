import os

from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv()

proxy = {}
if os.getenv("PROXY_ADDR"):
    proxy = {
        'proxy_type': 'socks5',
        'addr': os.getenv("PROXY_ADDR"),
        'port': int(os.getenv("PROXY_PORT"))
    }



try:
    client = TelegramClient(StringSession(os.getenv("STRING_SESSION")), os.getenv("API_ID"), os.getenv("API_HASH"), proxy=proxy)
    client.start()
except Exception as e:
    print(f"Exception while starting the client - {e}")
else:
    print("Client started")


async def main():
    try:
        ret_value = await client.send_message(1330252288, 'Hi,wang')
    except Exception as e:
        print(f"Exception while sending the message - {e}")
    else:
        print(f"Message sent. Return Value {ret_value}")


with client:
    client.loop.run_until_complete(main())