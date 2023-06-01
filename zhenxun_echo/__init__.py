import re

from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, Message

__zx_plugin_name__ = "echo"
__plugin_usage__ = """
usage：
    echo
    指令：
        echo+想要机器人发送的内容
        回复想要机器人发送的消息+echo
""".strip()
__plugin_des__ = "echo"
__plugin_cmd__ = ["echo"]
__plugin_type__ = ("常规插件",)
__plugin_version__ = 0.2
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
async def _(event: MessageEvent):
    if event.reply:
        await echo.finish(event.reply.message)
    if msg := re.sub(r"^echo", '', event.raw_message):  # 去掉命令后回复
        await echo.send(Message(msg))
