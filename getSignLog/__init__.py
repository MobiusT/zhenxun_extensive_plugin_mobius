from utils.utils import get_bot, scheduler
from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageEvent
from services.log import logger
from utils.manager import group_manager
from configs.config import Config
from utils.message_builder import image
import os
import io
from nonebot_plugin_htmlrender import text_to_pic
from PIL import Image

__zx_plugin_name__ = "定时获取签到日志 [Superuser]"
__plugin_usage__ = """
usage：
    每日获取genshinhelper日志并推送
    指令：
        查日志
""".strip()
__plugin_des__ = "每日获取genshinhelper日志并推送"
__plugin_cmd__ = ["查日志 [_superuser]"]
__plugin_type__ = ("常规插件",)
__plugin_version__ = 0.1
__plugin_author__ = "mobius"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["查日志", "getLog"],
}
__plugin_task__ = {"getSignLog": "获取签到日志"}

Config.add_plugin_config(
    "_task",
    "DEFAULT_GETSIGNLOG",
    False,
    help_="被动 定时获取签到日志 进群默认开关状态",
    default_value=False,
)

getSignLog = on_command("查日志", priority=15, block=True)

#日志输出位置，通过getResult.sh输出
LOG_PATH =  os.path.join(os.path.dirname(__file__), "log/sign.log")
#日志转图片保存位置
IMAGE_PATH =  os.path.join(os.path.dirname(__file__), "image")

@getSignLog.handle()
async def _(event: MessageEvent,):
    logFile = open(LOG_PATH,'r')
    try:
        logStr = logFile.read()
        pic = await text_to_pic(text=logStr)#日志转图片，依赖nonebot_plugin_htmlrender
        img = Image.open(io.BytesIO(pic))
        img.save(IMAGE_PATH + "/text2pic.png", format="PNG")
        await getSignLog.send(image('text2pic.png', IMAGE_PATH))
        logger.info(
            f"(USER {event.user_id}, GROUP {event.group_id if isinstance(event, GroupMessageEvent) else 'private'})"
            f" 发送签到日志"
        )
    finally:
        logFile.close()


@scheduler.scheduled_job(#定时任务，每日6时6分
    "cron",
    hour=6,
    minute=6,
)
async def _():
    # 每日查看
    bot = get_bot()
    if bot:
        gl = await bot.get_group_list()
        gl = [g["group_id"] for g in gl]
        logFile = open(LOG_PATH,'r')
        try:
            logStr = logFile.read()
            pic = await text_to_pic(text=logStr)#日志转图片，依赖nonebot_plugin_htmlrender
            img = Image.open(io.BytesIO(pic))
            img.save(IMAGE_PATH + "/text2pic.png", format="PNG")
            for gid in gl:
                if await group_manager.check_group_task_status(gid, "getSignLog"):
                    await bot.send_group_msg(group_id=int(gid), message=image('text2pic.png', IMAGE_PATH))                
        finally:
            logFile.close()

