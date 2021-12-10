import logging
import base64
import telethon.tl.types
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import PeerUser, PeerChat, PeerChannel
from dotenv import load_dotenv
import os
import requests
import json
import time


load_dotenv()

logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s', level=logging.INFO)

logger = logging.getLogger('channelMonitor')


"""
-> 这是一个Telegram机器人项目

-> 实现的功能：爬取Telegram中频道的图片
-> 注意：由于机器人无法加入其他人的频道，所以扒频道的图只能交给主体账户来进行（不会影响主账户的登录）
"""

# file save path
save_path = os.getenv("SAVE_PATH")

##
# For Python >= 3.6 : install python-socks[asyncio]
# For Python <= 3.5 : install PySocks
# proxy
# 如果需要通过代理连接到telegram的话: aiohttp_socks (Python version>=3.6), PySocks (<=3.5)
proxy = {}
if os.getenv("PROXY_ADDR"):
    proxy = {
        'proxy_type': 'socks5',
        'addr': os.getenv("PROXY_ADDR"),
        'port': int(os.getenv("PROXY_PORT"))
    }

# 要监视下载的频道,名字（键名）无实际代码作用，不要重复就行
try:
    channel = json.loads(os.getenv("CHANNEL").replace(r'\n', '\n'))
except Exception as e:
    logger.error(f"load channel error:{e}")

ext_to_image_prefix = {
    ".jpeg": "data:image/jpeg;base64,",
    ".png": "data:image/png;base64,",
    ".jpg": "data:image/jpeg;base64,",
    ".webp": "data:image/webp;base64,"
}
# 接受监视的媒体格式(tg里面直接发送gif最后是mp4格式！)
accept_file_format = ["image/jpeg", "image/gif", "image/png", "image/webp"]

try:
    # bot登陆：留作将来开发控制程序
    # bot = TelegramClient('transferBot', api_id, api_hash, proxy=(proxy_type, proxy_addr, proxy_port)).start(
    #     bot_token=bot_token).start()
    # 用户登陆
    client = TelegramClient(StringSession(os.getenv("STRING_SESSION")), int(os.getenv("API_ID")), os.getenv("API_HASH"),
                            proxy=proxy)
    # client.session.set_dc(2, '149.154.167.50', 443)
    client.start()
except Exception as e:
    logger.error(f"Exception while starting the client - {e}")
else:
    logger.info("Client started")

# 列表推导式 获取频道对象列表
channel_list = [PeerChannel(channel[channel_name]) for channel_name in channel]


# 过滤出监视下载的频道，如果有媒体消息就下载
@client.on(events.NewMessage(from_users=channel_list))
async def event_handler(event):
    # 获取对话
    # chat = await event.get_chat()
    # 获取message内容
    message = event.message
    logger.debug("发现消息")
    # 判断是否有媒体
    if message.media is not None:
        logger.debug("发现媒体")
        await download_image(message)


# 下载媒体的具体方法
async def download_image(message):
    # 如果是网页
    is_webpage = isinstance(message.media, telethon.tl.types.MessageMediaWebPage)
    # 如果媒体是照片则直接下载
    is_photo = isinstance(message.media, telethon.tl.types.MessageMediaPhoto)
    # 如果媒体是文件则检查是否是可接受的文件格式，这里用的否定表达，不好读！建议跳过或者自己写一个
    is_doc = isinstance(message.media, telethon.tl.types.MessageMediaDocument)
    if not (is_photo or is_webpage):
        if is_doc:
            is_accept_media = message.media.document.mime_type in accept_file_format
            if not is_accept_media:
                logger.debug("不可接受", message.media.document.mime_type)
                return

    # 这里由于download_media()可以自动命名
    # 所以，判断重复有点难搞，不过频道应该不怎么发重复内容
    # 那就这样吧!不写了
    # if os.path.exists(filename):
    #     print("文件已存在")
    #     return
    the_message_peer_id = get_user_id(message)
    if not the_message_peer_id:
        return
    user_id = str(abs(the_message_peer_id))
    msg = message.message
    if user_id=='1214996122' and  msg and '🔞NSFW' in msg:
        return
    new_save_path = save_path + os.sep + user_id +os.sep + time.strftime("%Y-%m-%d")
    if not os.path.exists(new_save_path):
        os.makedirs(new_save_path, exist_ok=True)
    # 这个方法下载成功后会返回文件的保存名
    filename = await client.download_media(message, new_save_path)
    if filename is None:
        logger.debug("下载失败")
        return
    logger.debug(filename)
    logger.debug("下载完成")
    logger.debug(message)

    # 下面注释的代码不知道什么原因无法在文件不存在的情况下新建文件
    # async with async_open(save_path + "1.txt", "a") as f:
    #     await f.write(filename + "\n")
    send_img_hosting(filename, msg, user_id)


def get_user_id(message):
    if isinstance(message.peer_id, PeerUser):
        return message.peer_id.user_id
    elif isinstance(message.peer_id, PeerChannel):
        return message.peer_id.channel_id
    elif isinstance(message.peer_id, PeerChat):
        return message.peer_id.chat_id
    else:
        return None


def send_img_hosting(path, msg, user_id):
    _, file_ext = os.path.splitext(path)
    image_base_64 = ext_to_image_prefix[file_ext] + get_base64_encoded_image(path)
    image_size = os.stat(path).st_size
    if image_size <= int(os.getenv("FILTER_IMG_SIZE")):
        post_image(image_base_64, msg, user_id)


def get_base64_encoded_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')


def post_image(image_base_64, msg, user_id):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36",
        "Content-Type": "application/json; charset=utf-8"
    }
    path = "tg/" + user_id
    data = json.dumps({"path": path, "image": image_base_64})
    image_hosting_url = os.getenv("IMAGE_HOSTING")
    res = requests.post(url=image_hosting_url, data=data, headers=headers, timeout=30)
    if res.status_code == 200:
        res_json = json.loads(res.text)
        if res_json['success'] and res_json['data']['url'] != '':
            if msg:
                res_json['data']['msg'] = msg
            notifications(res_json['data'])


def notifications(data):
    notifications_url = os.getenv("NOTIFICATIONS")
    if not notifications_url:
        return
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36",
        "Content-Type": "application/json; charset=utf-8"
    }
    requests.post(url=notifications_url, data=json.dumps(data), headers=headers, timeout=30)


async def bot_main():
    pass


# 展示登陆的信息
def show_my_inf(me):
    logger.info("-----****************-----")
    logger.info("Name: %s", me.username)
    logger.info("ID: %s", me.id)
    logger.info("-----login successful-----")


async def client_main():
    logger.info("-client-main-")
    me = await client.get_me()
    show_my_inf(me)
    # 这个方法是一直连着直到断开，我没有写断开的代码，所以程序应该会一直运行
    await client.run_until_disconnected()


with client:
    client.loop.run_until_complete(client_main())
