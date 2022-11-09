from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, Message, MessageSegment
from services.log import logger
from nonebot.params import CommandArg
from utils.message_builder import at
from configs.config import Config
from ..modules.database import DB
from ..modules.image_handle import DrawIndex
from ..modules.query import InfoError, GetInfo
from ..utils.handle_id import handle_id


__zx_plugin_name__ = "崩坏三卡片"
__plugin_usage__ = """
usage：
    获取崩坏三账号摘要信息
    指令：
        崩坏三卡片                #已绑定uid时使用
        崩坏三卡片[uid][服务器]    #初次使用命令/查询别的玩家的卡片
        崩坏三卡片[uid]           #查询已经绑定过uid的玩家的卡片
        崩坏三卡片[@]             #查询at的玩家绑定的角色卡片
        崩坏三卡片米游社/mys/MYS[米游社id] #查询该米游社id的角色卡片
        
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

@card.handle()
async def _(event: MessageEvent, arg: Message = CommandArg()):
    #读取配置文件
    cookie = Config.get_config("bind_bh3", "COOKIE")
    if not cookie:
        await card.send("需要真寻主人在config.yaml中配置cookie才能使用该功能")
        return

    region_db = DB("uid.sqlite", tablename="uid_region")
    qid_db = DB("uid.sqlite", tablename="qid_uid")
    #获取绑定的角色信息
    try:
        role_id, region_id, qid = handle_id(event, arg)
    except InfoError as e:
        await card.send(Message(f"{at(event.user_id)}出错了：{str(e)}"))
        return
    #查询角色
    spider = GetInfo(server_id=region_id, role_id=role_id)

    try:
        ind = await spider.part()
    except InfoError as e:
        await card.send(Message(f"{at(event.user_id)}出错了：{str(e)}"))
        return
    await card.send(Message(f"{at(event.user_id)}制图中，请稍后"))
    #绘图
    region_db.set_region(role_id, region_id)
    qid_db.set_uid_by_qid(qid, role_id)
    ind = DrawIndex(**ind)
    im = await ind.draw_card(qid)
    img = MessageSegment.image(im)
    await card.finish(img, at_sender=True)
