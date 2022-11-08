from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, Message
from services.log import logger
from nonebot.params import CommandArg, Command
from typing import Tuple
from ..modules.database import DB
from ..modules.image_handle import (ItemTrans)
from ..modules.query import InfoError
import json, re, os


__zx_plugin_name__ = "崩坏三绑定"
__plugin_usage__ = """
usage：
    绑定崩坏三uid及服务器
    指令：
        崩坏三绑定[uid][服务器]
        崩坏三服务器列表
        崩坏三解绑
        示例：崩坏三绑定114514官服
""".strip()
__plugin_des__ = "绑定自己的崩坏三uid等"
__plugin_cmd__ = ["崩坏三绑定[uid][服务器]", "崩坏三服务器列表", "崩坏三解绑"]
__plugin_type__ = ("崩坏三相关",)
__plugin_version__ = 0.1
__plugin_author__ = "mobius"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["崩坏三绑定", "崩三绑定", "崩3绑定", "崩坏3绑定"],
}
__plugin_configs__ = {
    "COOKIE": {
        "value": '', 
        "help": "登录https://bbs.mihoyo.com/bh3/ 后F12控制台输入document.cookie获取ck: cookie_token=xxxxxx;account_id=xxxxxx", 
        "default_value": ''
    }
}

bind = on_command(
    "崩坏三绑定", aliases={"崩三绑定", "崩3绑定", "崩坏3绑定", "崩坏三绑定uid", "崩三绑定uid", "崩3绑定uid", "崩坏3绑定uid"}, priority=5, block=True
)
server = on_command("崩坏三服务器列表", aliases={"崩三服务器列表", "崩3服务器列表", "崩坏3服务器列表", "崩坏三服务器", "崩三服务器", "崩3服务器", "崩坏3服务器"}, priority=5, block=True)

@bind.handle()
async def _(event: MessageEvent, cmd: Tuple[str, ...] = Command(), arg: Message = CommandArg()):
    msg = arg.extract_plain_text().strip()
    qid=event.user_id #qq
    role_id = re.search(r"\d+", msg) #uid
    region_name = re.search(r"\D+\d?", msg)  #服务器名
    #检查命令参数
    if not role_id or not region_name:
        await bind.send("请按以下格式绑定：崩坏三绑定114514官服;服务器列表查询：崩坏三服务器列表")
        return
    #查找服务器id
    try:
        region_id = ItemTrans.server2id(region_name.group())
    except InfoError as e:
        await bind.send(str(e))
        return
    #数据库存储
    region_db = DB("uid.sqlite", tablename="uid_region")
    qid_db = DB("uid.sqlite", tablename="qid_uid")
    region_db.set_region(role_id.group(), region_id)
    qid_db.set_uid_by_qid(qid, role_id.group())
    await bind.send("已绑定")

#崩坏三服务器列表
@server.handle()
async def _(event: MessageEvent):
    with open(
        #读取配置文件
        os.path.join(os.path.dirname(__file__), "../region.json"),
        "r",
        encoding="utf8",
    ) as f:
        #反序列化
        region = json.load(f)
        f.close()    
    #拼接字符串
    serverStr=(f'')
    for server_id, alias in region.items():
        serverStr=f'{serverStr}{alias["name"]}服: '
        for aliasServer in alias["alias"]:
            serverStr=f'{serverStr}{aliasServer}, '
        serverStr=f'{serverStr[:-2]}; \n'
    await server.send(serverStr)

