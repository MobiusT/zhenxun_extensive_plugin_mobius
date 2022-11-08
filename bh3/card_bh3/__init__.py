from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, Message, MessageSegment
from services.log import logger
from nonebot.params import CommandArg, Command
from utils.message_builder import at
from utils.utils import get_message_at
from ..utils.image_utils import load_image, image_build
from typing import Tuple
from configs.config import Config
from ..modules.database import DB
from ..modules.image_handle import (DrawCharacter, DrawFinance, DrawIndex,
                                   ItemTrans)
from ..modules.query import InfoError, GetInfo
import json, re, os


__zx_plugin_name__ = "崩坏三卡片"
__plugin_usage__ = """
usage：
    获取崩坏三账号摘要信息
    指令：
        崩坏三卡片
""".strip()
__plugin_des__ = "获取崩坏三账号摘要信息"
__plugin_cmd__ = ["崩坏三卡片"]
__plugin_type__ = ("崩坏三相关",)
__plugin_version__ = 0.1
__plugin_author__ = "mobius"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["崩坏三卡片", "崩三卡片", "崩3卡片", "崩坏3卡片"],
}

card = on_command(
    "崩坏三卡片", aliases={"崩三卡片", "崩3卡片", "崩坏3卡片"}, priority=5, block=True
)

IMAGE_PATH = os.path.join(os.path.dirname(__file__), "image")

@card.handle()
async def _(event: MessageEvent, arg: Message = CommandArg()):
    cookie = Config.get_config("bind_bh3", "COOKIE")
    if not cookie:
        await card.send("需要真寻主人在config.yaml中配置cookie才能使用该功能")
        return

    region_db = DB("uid.sqlite", tablename="uid_region")
    qid_db = DB("uid.sqlite", tablename="qid_uid")
    try:
        role_id, region_id, qid = handle_id(event, arg)
    except InfoError as e:
        await card.send(Message(f"{at(qid)}出错了：{str(e)}"))
        return

    spider = GetInfo(server_id=region_id, role_id=role_id)

    try:
        ind = await spider.part()
    except InfoError as e:
        await card.send(Message(f"{at(qid)}出错了：{str(e)}"))
        return
    await card.send(Message(f"{at(qid)}制图中，请稍后"))

    region_db.set_region(role_id, region_id)
    qid_db.set_uid_by_qid(qid, role_id)
    ind = DrawIndex(**ind)
    im = await ind.draw_card(qid)
    img = MessageSegment.image(im)
    await card.finish(img, at_sender=True)

def handle_id(event: MessageEvent, arg: Message = CommandArg()):
    msg = arg.extract_plain_text().strip()

    ats =  get_message_at(event.json())
    if len(ats)==0 :
        ats=[event.user_id]
    else:
        ats=list(set(ats))
    qid=ats[0]
  
    role_id = re.search(r"\d+", msg)
    region_name = re.search(r"\D+\d?", msg)

    region_db = DB("uid.sqlite", tablename="uid_region")
    qid_db = DB("uid.sqlite", tablename="qid_uid")

    if re.search(r"[mM][yY][sS]|米游社", msg):
        spider = GetInfo(mysid=role_id.group())
        region_id, role_id = spider.mys2role(spider.getrole)

    elif role_id is None:
        try:
            role_id = qid_db.get_uid_by_qid(qid)
            region_id = region_db.get_region(role_id)
        except KeyError:
            #TODO
            raise InfoError(
                "[此命令可能无效]请在原有指令后面输入游戏uid及服务器,只需要输入一次就会记住下次直接使用bh#获取就好\n例如:bh#100074751官服"
            )

    elif role_id is not None and region_name is None:
        region_id = region_db.get_region(role_id.group())

        if not region_id:
            raise InfoError(
                #TODO
                f"[此命令可能无效]{role_id.group()}为首次查询,请输入服务器名称.如:bh#100074751官服")

    else:
        try:
            region_id = ItemTrans.server2id(region_name.group())
        except InfoError as e:
            raise InfoError(str(e))

        now_region_id = region_db.get_region(role_id.group())

        if now_region_id is not None and now_region_id != region_id:
            raise InfoError(
                f"服务器信息与uid不匹配,可联系管理员修改."
            )  # 输入的服务器与数据库中保存的不一致，可手动delete该条数据

    role_id = role_id if isinstance(role_id, str) else role_id.group()
    return role_id, region_id, qid