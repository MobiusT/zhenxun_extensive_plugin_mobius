'''
Author: MobiusT
Date: 2023-02-13 20:00:21
LastEditors: MobiusT
LastEditTime: 2023-02-19 14:50:02
'''
from utils.utils import get_message_at
from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message
from services.log import logger
from services.db_context import TestSQL
from utils.message_builder import at
from configs.path_config import IMAGE_PATH
from nonebot.permission import SUPERUSER
import os
import time

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
__plugin_version__ = 0.1
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
async def _(event: GroupMessageEvent,):
    ats =  get_message_at(event.json())
    if len(ats)==0 :
        ats=[event.user_id]
    else:
        ats=list(set(ats))
    mes=''
    for qq in ats :
        sql = f'update sign_group_users set checkin_count = (checkin_count-1) , checkin_time_last = (checkin_time_last+ interval \'-1 Day\') where group_id=\'{event.group_id}\' and user_qq = (\'{qq}\')'
        row = await TestSQL.raw(sql)
        if row == 0 :
            mes=mes+f'{at(qq)}签退失败;'
        else :
            todayCard=f'{SIGN_TODAY_CARD_PATH}/{qq}_{event.group_id}_sign_{time.strftime("%Y-%m-%d",time.localtime(time.time()))}.png'
            try:
                os.remove(todayCard)
            except BaseException as e:
                logger.error(f'删除签到图片{todayCard}失败',e)
            mes=mes+f'{at(qq)}签退成功;'

    await reSign.send(Message(mes))
   

