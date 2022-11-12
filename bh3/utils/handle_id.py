from nonebot.adapters.onebot.v11 import MessageEvent, Message
from nonebot.params import CommandArg
from utils.utils import get_message_at
from ..modules.database import DB
from ..modules.image_handle import ItemTrans
from ..modules.query import InfoError, GetInfo
import re


def handle_id(event: MessageEvent, arg: Message = CommandArg()):
    #获取参数
    msg = arg.extract_plain_text().strip()
    return handle_id_str(event, msg)

def handle_id_str(event: MessageEvent, msg: str):
    #获取at
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
    #获取命令后面跟的角色信息（如有）
    if re.search(r"[mM][yY][sS]|米游社", msg):
        try: 
            spider = GetInfo(mysid=role_id.group())
            region_id, role_id = spider.mys2role(spider.getrole)
        except IndexError as e:
            raise InfoError(str(e))
    #未绑定
    elif role_id is None:
        try:
            role_id = qid_db.get_uid_by_qid(qid)
            region_id = region_db.get_region(role_id)
        except KeyError:
            raise InfoError(
                "未绑定uid，请在原有指令后面输入游戏uid及服务器,只需要输入一次就会记住下次可直接使用\n例如:崩坏三卡片100074751官服"
            )
    #未输入服务器
    elif role_id is not None and region_name is None:
        region_id = region_db.get_region(role_id.group())

        if not region_id:
            raise InfoError(
                f"[{role_id.group()}为首次查询,请输入服务器名称.如:崩坏三卡片114514官服")
    else:
        try:
            region_id = ItemTrans.server2id(region_name.group())
        except InfoError as e:
            raise InfoError(str(e))

        now_region_id = region_db.get_region(role_id.group())

        if now_region_id is not None and now_region_id != region_id:
            raise InfoError(
                f"输入的游戏服务器与uid当前已绑定的服务器不匹配,可联系管理员修改."
            )  # 输入的服务器与数据库中保存的不一致，可手动delete该条数据

    role_id = role_id if isinstance(role_id, str) else role_id.group()
    return role_id, region_id, qid   