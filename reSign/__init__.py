import os
import time
from datetime import datetime, timedelta

from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER

from configs.path_config import IMAGE_PATH
from models.sign_group_user import SignGroupUser
from services.log import logger
from utils.message_builder import at
from utils.utils import get_message_at

__zx_plugin_name__ = "签退 [Superuser]"
__plugin_usage__ = """
usage：
    签退对应人员，可以重新签到
    指令：
        签退@人员
""".strip()
__plugin_des__ = "签退对应人员，可以重新签到"
__plugin_cmd__ = ["签退[at] [_superuser]"]
__plugin_type__ = ("常规插件",)
__plugin_version__ = 0.3
__plugin_author__ = "mobius"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["签退", "resign", "reSign"],
}

reSign = on_command("签退", aliases={"reSign", "resign"}, permission=SUPERUSER, priority=15, block=True)

SIGN_TODAY_CARD_PATH = IMAGE_PATH / 'sign' / 'today_card'


@reSign.handle()
async def _(event: GroupMessageEvent, arg: Message = CommandArg()):
    if arg.extract_plain_text().strip():
        logger.info("预期外的签退命令，退出执行")
        return
    ats = get_message_at(event.json())
    ats = [event.user_id] if len(ats) == 0 else list(set(ats))
    mes = ''
    for qq in ats:
        try:
            user = await SignGroupUser.get_or_none(group_id=event.group_id, user_qq=qq)
            if not user or user.checkin_time_last.date() < datetime.now().date():
                mes += f'{at(qq)}今日未签到; '
                continue
            user.checkin_count -= 1
            user.checkin_time_last += timedelta(days=-1)
            await user.save()
            today_card = f'{SIGN_TODAY_CARD_PATH}/{qq}_{event.group_id}_sign_{time.strftime("%Y-%m-%d", time.localtime(time.time()))}.png'
            my_card = f'{SIGN_TODAY_CARD_PATH}/{qq}_{event.group_id}_view_{time.strftime("%Y-%m-%d", time.localtime(time.time()))}.png'
            try:
                os.remove(today_card)
                os.remove(my_card)
            except Exception as e:
                logger.warning('删除签到缓存图片失败', e=e)
            mes = f'{mes}{at(qq)}签退成功; '
        except Exception as e:
            import traceback
            logger.error(f'{qq}签退失败：{e}\n{traceback.format_exc()}')
            mes += f'{at(qq)}签退失败; '
    await reSign.send(Message(mes))
