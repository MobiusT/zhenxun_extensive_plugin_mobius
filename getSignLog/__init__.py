import os

from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageEvent, MessageSegment
from nonebot_plugin_htmlrender import text_to_pic

from configs.config import Config
from services.log import logger
from utils.manager import group_manager
from utils.utils import get_bot, scheduler

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
__plugin_task__ = {"getSignLog": "获取签到日志"}

Config.add_plugin_config(
    "_task",
    "DEFAULT_GETSIGNLOG",
    False,
    help_="被动 定时获取签到日志 进群默认开关状态",
    default_value=False,
)

getSignLog = on_command("查日志", priority=15, block=True)

# 日志输出位置，通过getResult.sh输出
LOG_PATH = os.path.join(os.path.dirname(__file__), "log/sign.log")


@getSignLog.handle()
async def _(event: MessageEvent, ):
    log_file = open(LOG_PATH, 'r')
    try:
        log_str = log_file.read()
        pic = await text_to_pic(text=log_str)  # 日志转图片，依赖nonebot_plugin_htmlrender
        await getSignLog.send(MessageSegment.image(pic))
        logger.info(
            f"(USER {event.user_id}, GROUP {event.group_id if isinstance(event, GroupMessageEvent) else 'private'})"
            f" 发送签到日志"
        )
    finally:
        log_file.close()


@scheduler.scheduled_job(  # 定时任务，每日6时6分
    "cron",
    hour=6,
    minute=6,
)
async def _():
    if bot := get_bot():
        return
    gl = await bot.get_group_list()
    gl = [g["group_id"] for g in gl]
    log_file = open(LOG_PATH, 'r')
    try:
        # 推送群
        log_str = log_file.read()
        pic = await text_to_pic(text=log_str)  # 日志转图片，依赖nonebot_plugin_htmlrender
        for gid in gl:
            if group_manager.check_group_task_status(gid, "getSignLog"):
                await bot.send_group_msg(group_id=int(gid), message=MessageSegment.image(pic))
        # 推送qq列表
        qid_list: list = (Config.get_config("getSignLog", "PUSHQQ")).split(',')
        qid_list.extend(iter(bot.config.superusers))
        qid_list = list(set(qid_list))
        for qid in qid_list:
            try:
                await bot.send_private_msg(user_id=int(qid), message=MessageSegment.image(pic))
            except:
                logger.error(f"{qid}签到日志推送出错")
    finally:
        log_file.close()
