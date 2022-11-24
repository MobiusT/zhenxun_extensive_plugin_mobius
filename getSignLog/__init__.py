from utils.utils import get_bot, scheduler
from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageEvent, MessageSegment
from services.log import logger
from utils.manager import group_manager
from configs.config import Config
from nonebot_plugin_htmlrender import text_to_pic
import os


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
__plugin_configs__ = {
    "PUSHQQ": {
        "value": '', 
        "help": "需要推送的qq，多个qq用逗号分隔，超级用户无需填写，会自动推送", 
        "default_value": ''
    },
}

getSignLog = on_command("查日志", priority=15, block=True)

#日志输出位置，通过getResult.sh输出
LOG_PATH =  os.path.join(os.path.dirname(__file__), "log/sign.log")

@getSignLog.handle()
async def _(event: MessageEvent,):
    logFile = open(LOG_PATH,'r')
    try:
        logStr = logFile.read()
        pic = await text_to_pic(text=logStr)#日志转图片，依赖nonebot_plugin_htmlrender
        await getSignLog.send(MessageSegment.image(pic))
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
        logFile = open(LOG_PATH,'r')
        try:
            logStr = logFile.read()
            pic = await text_to_pic(text=logStr)#日志转图片，依赖nonebot_plugin_htmlrender
            qidList:list = (Config.get_config("getSignLog", "PUSHQQ")).split(',')
            for superuser in bot.config.superusers:
                qidList.append(superuser)
            qidList=list(set(qidList))
            for qid in qidList:
                try:
                    await bot.send_private_msg(user_id=int(qid), message=MessageSegment.image(pic))  
                except:
                    logger.error(f"{qid}签到日志推送出错")          
        finally:
            logFile.close()

