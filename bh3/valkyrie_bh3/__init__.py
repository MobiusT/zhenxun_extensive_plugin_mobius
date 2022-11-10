from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, Message, MessageSegment
from services.log import logger
from nonebot.params import CommandArg
from utils.message_builder import at
from configs.config import Config
from ..modules.database import DB
from ..modules.image_handle import DrawCharacter
from ..modules.mytyping import Index
from ..modules.query import InfoError, GetInfo
from ..utils.handle_id import handle_id


__zx_plugin_name__ = "崩坏三女武神"
__plugin_usage__ = """
usage：
    获取崩坏三账号女武神信息
    指令：
        崩坏三女武神                #已绑定uid时使用
        崩坏三女武神[uid][服务器]    #初次使用命令/查询别的玩家的女武神
        崩坏三女武神[uid]           #查询已经绑定过uid的玩家的女武神
        崩坏三女武神[@]             #查询at的玩家绑定的角色女武神
        崩坏三女武神米游社/mys/MYS[米游社id] #查询该米游社id的角色女武神
        
""".strip()
__plugin_des__ = "获取崩坏三账号女武神信息"
__plugin_cmd__ = ["崩坏三女武神"]
__plugin_type__ = ("崩坏三相关",)
__plugin_version__ = 0.1
__plugin_author__ = "mobius"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["崩坏三女武神", "崩三女武神", "崩3女武神", "崩坏3女武神"],
}
__plugin_block_limit__ = {
    "rst": "[at]你正在查询！"
}
__plugin_cd_limit__ = {
    "cd": 60,
    "rst": "[at]你刚查过，别查了！"
}
valkyrie = on_command(
    "崩坏三女武神", aliases={"崩三女武神", "崩3女武神", "崩坏3女武神"}, priority=5, block=True
)

@valkyrie.handle()
async def _(event: MessageEvent, arg: Message = CommandArg()):
    #读取配置文件
    cookie = Config.get_config("bind_bh3", "COOKIE")
    if not cookie:
        await valkyrie.send("需要真寻主人在config.yaml中配置cookie才能使用该功能")
        return

    region_db = DB("uid.sqlite", tablename="uid_region")
    qid_db = DB("uid.sqlite", tablename="qid_uid")
    #获取绑定的角色信息
    try:
        role_id, region_id, qid = handle_id(event, arg)
    except InfoError as e:
        await valkyrie.send(Message(f"{at(event.user_id)}出错了：{str(e)}"))
        return
    #查询角色
    spider = GetInfo(server_id=region_id, role_id=role_id)

    try:
        _, data = await spider.fetch(spider.valkyrie)
        _, index_data = await spider.fetch(spider.index)
    except InfoError as e:
        await valkyrie.send(Message(f"{at(event.user_id)}出错了：{str(e)}"))
        return
    await valkyrie.send(Message(f"{at(event.user_id)}制图中，女武神制图耗时较长，请耐心等待"))
    #绘图
    region_db.set_region(role_id, region_id)
    qid_db.set_uid_by_qid(qid, role_id)
    index = Index(**index_data["data"])
    dr = DrawCharacter(**data["data"])
    im = await dr.draw_chara(index, qid)
    img = MessageSegment.image(im)
    await valkyrie.finish(img, at_sender=True)
