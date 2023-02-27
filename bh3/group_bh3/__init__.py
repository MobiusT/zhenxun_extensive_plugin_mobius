from nonebot import on_regex
from nonebot.adapters.onebot.v11 import MessageEvent, Message, MessageSegment
from services.log import logger
from utils.message_builder import at
from utils.utils import get_message_at, get_message_text
from configs.config import Config
from ..modules.database import DB
from ..modules.image_handle import DrawGroupCharacter
from ..modules.mytyping import Index
from ..modules.query import InfoError, GetInfo
from ..utils.handle_id import handle_id_str
from typing import Tuple, Any
from nonebot.params import RegexGroup
import os, json



__zx_plugin_name__ = "崩坏三阵容"
__plugin_usage__ = """
usage：
    获取崩坏三账号阵容信息
    指令：
        崩坏三XXX阵容                #已绑定uid时使用
        崩坏三XXX阵容[uid][服务器]    #初次使用命令/查询别的玩家的女武神
        崩坏三XXX阵容[uid]           #查询已经绑定过uid的玩家的女武神
        崩坏三XXX阵容[@]             #查询at的玩家绑定的角色女武神
        崩坏三XXX阵容米游社/mys/MYS[米游社id] #查询该米游社id的角色女武神
    例：崩坏三天识卡阵容
        
""".strip()
__plugin_des__ = "获取崩坏三账号阵容信息"
__plugin_cmd__ = ["崩坏三阵容"]
__plugin_type__ = ("崩坏三相关",)
__plugin_version__ = 0.1
__plugin_author__ = "mobius"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["崩坏三阵容", "崩三阵容", "崩3阵容", "崩坏3阵容"],
}
__plugin_block_limit__ = {
    "rst": "[at]你正在查询！"
}
__plugin_cd_limit__ = {
    "limit_type": "group",
    "rst": "正在查询中，请等待当前请求完成...",
}
group = on_regex(r"^(崩坏三|崩三|崩坏3|崩3)(.{1,3})阵容(.{0,30})$", priority=5, block=True)

@group.handle()
async def _(event: MessageEvent, reg_group: Tuple[Any, ...] = RegexGroup()):
    #读取配置文件
    cookie = Config.get_config("bind_bh3", "COOKIE")
    if not cookie:
        await group.finish("需要真寻主人在config.yaml中配置cookie才能使用该功能")
    groupName = get_message_text(Message(reg_group[1])).strip()
    #特殊适配律三家
    if groupName == "虚三家":
        groupName = "终始真"
    elif groupName == "律三家":
        groupName = "炎雷理"
    groupJson=getGroupJson()
    groupList = []
    for name in groupName:
        if isinstance(groupJson[name], str):
            groupList.append(groupJson[name])
        elif isinstance(groupJson[name], list):
            for groupJsonName in groupJson[name]:
                groupList.append(groupJsonName)
        else:
            await group.finish("未找到{groupName}中的{name},请联系管理员添加配置")
    ats =  get_message_at(event.json())
    if len(ats)==0 :
        arg = str(reg_group[2])
    else:
        arg=""  
    region_db = DB("uid.sqlite", tablename="uid_region")
    qid_db = DB("uid.sqlite", tablename="qid_uid")
    #获取绑定的角色信息
    try:
        role_id, region_id, qid = handle_id_str(event, arg)
    except InfoError as e:
        await group.finish(Message(f"{at(event.user_id)}出错了：{str(e)}"))
        #查询角色
    spider = GetInfo(server_id=region_id, role_id=role_id)
    try:
        _, data = await spider.fetch(spider.valkyrie)
        _, index_data = await spider.fetch(spider.index)
    except InfoError as e:
        await group.finish(Message(f"{at(event.user_id)}出错了：{str(e)}"))
    #绘图
    region_db.set_region(role_id, region_id)
    qid_db.set_uid_by_qid(qid, role_id)
    index = Index(**index_data["data"])
    dr = DrawGroupCharacter(**data["data"])
    im = await dr.draw_chara(index, qid, groupList)
    img = MessageSegment.image(im)
    await group.finish(img, at_sender=True)

def getGroupJson():
    with open(
        os.path.join(os.path.dirname(__file__), "./group.json"),
        "r",
        encoding="utf8",
    ) as f:
        groupJson = json.load(f)
        f.close()
    return groupJson