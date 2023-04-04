'''
Author: MobiusT
Date: 2023-03-26 00:08:12
LastEditors: MobiusT
LastEditTime: 2023-04-04 16:14:33
'''
from nonebot import on_keyword
from utils.message_builder import record, image
from services.log import logger
from nonebot.typing import T_State
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, GroupMessageEvent
import random
import os

__zx_plugin_name__ = "识宝骂我"
__plugin_usage__ = """
usage：
    识宝多骂我一点，球球了
    指令：
        识宝
""".strip()
__plugin_des__ = "识宝请狠狠的骂我一次！"
__plugin_cmd__ = ["识宝骂我"]
__plugin_type__ = ("崩坏三相关",)
__plugin_version__ = 0.2
__plugin_author__ = "mobius"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": __plugin_cmd__,
}
__plugin_cd_limit__ = {
    "cd": 3,
    "rst": "就...就算求我骂你也得慢慢来..."
}
#语音保存路径
RECORD_PATH = os.path.join(os.path.dirname(__file__), "record")
#图片保存路径
IMAGE_PATH = os.path.join(os.path.dirname(__file__), "image")
dg_voice = on_keyword({"识宝骂我"}, priority=5)


@dg_voice.handle()
async def _(bot: Bot, event: MessageEvent, state: T_State):
    if len(str((event.get_message()))) > 1:
        #随机选择可选语音图片
        voice = random.choice(os.listdir(RECORD_PATH))
        result = record(voice, RECORD_PATH)
        await dg_voice.send(result)
        await dg_voice.send(image(f'{voice.split("_")[1]}.jpg', IMAGE_PATH))
        logger.info(
            f"(USER {event.user_id}, GROUP "
            f"{event.group_id if isinstance(event, GroupMessageEvent) else 'private'}) 发送识宝骂人:"
            + result
        )
