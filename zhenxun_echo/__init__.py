from utils.utils import get_bot, get_message_at
from nonebot import on_command
from nonebot.adapters.onebot.v11 import GROUP, MessageEvent, Message
from nonebot.params import CommandArg
from services.log import logger
from configs.config import Config
import requests, json

__zx_plugin_name__ = "echo"
__plugin_usage__ = """
usage：
    echo
    指令：
        echo+文字
""".strip()
__plugin_des__ = "echo"
__plugin_cmd__ = ["echo"]
__plugin_type__ = ("常规插件",)
__plugin_version__ = 0.1
__plugin_author__ = "mobius"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["echo"],
}
__plugin_cd_limit__ = {
    "cd": 3,
    "rst": "[at]慢点说！"
}

echo = on_command("echo", priority=5, block=True)


@echo.handle()
async def _(event: MessageEvent, arg: Message = CommandArg()):
    text=arg.extract_plain_text().strip()
    await echo.send(text)
    
