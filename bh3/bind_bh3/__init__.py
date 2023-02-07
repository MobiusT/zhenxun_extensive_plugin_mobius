from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, Message, MessageSegment, GroupMessageEvent
from services.log import logger
from nonebot.params import CommandArg
from configs.config import Config
from utils.http_utils import AsyncHttpx
from utils.message_builder import image
from plugins.genshin.query_user._models import Genshin
from ..modules.database import DB
from ..modules.image_handle import (ItemTrans, DrawFinance)
from ..modules.query import InfoError, Finance, NotBindError
import json, re, os


__zx_plugin_name__ = "崩坏三绑定"
__plugin_usage__ = """
usage：
    绑定崩坏三uid及服务器等数据，cookie极为重要，请谨慎绑定
    ** 如果对拥有者不熟悉，并不建议添加cookie **
    该项目只会对cookie用于”崩坏三签到“，“崩坏三手账”
    指令：
        崩坏三绑定[uid][服务器]
        崩坏三服务器列表
        崩坏三ck[cookie]     # 该绑定请私聊
        崩坏三ck同步         # 该命令要求先绑定原神cookie，通过绑定的原神cookie绑定崩三ck
        示例：崩坏三绑定114514官服
            崩坏三cklogin_ticket==xxxxxxxxxxxxxxx
    如果不明白怎么获取cookie请输入“崩坏三ck”。
""".strip()
__plugin_des__ = "绑定自己的崩坏三uid等"
__plugin_cmd__ = ["崩坏三绑定[uid][服务器]", "崩坏三服务器列表", "崩坏三ck"]
__plugin_type__ = ("崩坏三相关",)
__plugin_version__ = 0.1
__plugin_author__ = "mobius"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["崩坏三绑定", "崩三绑定", "崩3绑定", "崩坏3绑定", "崩坏三服务器列表"],
}
__plugin_configs__ = {
    "COOKIE": {
        "value": '', 
        "help": "超级用户私聊真寻【崩三ck】按提示步骤获取login_ticket，根据真寻返回的内容进行配置，示例: cookie_token=xxxxxx;account_id=xxxxxx", 
        "default_value": ''
    }
}

bind = on_command(
    "崩坏三绑定", aliases={"崩三绑定", "崩3绑定", "崩坏3绑定", "崩坏三绑定uid", "崩三绑定uid", "崩3绑定uid", "崩坏3绑定uid"}, priority=5, block=True
)
server = on_command("崩坏三服务器列表", aliases={"崩三服务器列表", "崩3服务器列表", "崩坏3服务器列表", "崩坏三服务器", "崩三服务器", "崩3服务器", "崩坏3服务器"}, priority=5, block=True)
ck = on_command(
    "崩坏三ck", aliases={"崩三ck", "崩3ck", "崩坏3ck"}, priority=5, block=True
)
@bind.handle()
async def _(event: MessageEvent, arg: Message = CommandArg()):
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


#崩坏三ck
@ck.handle()
async def _(bot: Bot, event: MessageEvent, arg: Message = CommandArg()):
    #获取参数
    msg = arg.extract_plain_text().strip()
    if not msg:
        img=image('ck.png', os.path.join(os.path.dirname(__file__)))
        await ck.finish(Message(img + NotBindError.msg))
    ck_flag = True
    #读取配置文件
    cookie = Config.get_config("bind_bh3", "COOKIE")
    if (not cookie) and (str(event.user_id) in bot.config.superusers):
        ck_flag = False
    if ck_flag:
        qid_db = DB("uid.sqlite", tablename="qid_uid")
        qid = event.user_id
        #验证uid绑定状态
        try:
            qid_db.get_uid_by_qid(qid)
        except:
            await ck.finish("请先绑定uid，如崩坏三绑定114514官服")
    try:
        #同步真寻原神ck
        login_ticket = None
        account_id = None
        cookie_token = None
        cookie_json = None
        if "同步" == msg:
            #获取原神uid
            genshin_user = await Genshin.get_user_by_qq(event.user_id)
            login_ticket = genshin_user.login_ticket
            if not login_ticket:
                if not genshin_user.cookie:
                    raise InfoError(f'尚未绑定原神cookie，请先绑定原神cookie或发送 崩坏三ck 绑定崩坏三ck')
                else:
                    cookie = genshin_user.cookie
                    # 用: 代替=, ,代替;
                    cookie = '{"' + cookie.replace('=', '": "').replace("; ", '","').replace(";", '","') + '"}'
                    #反序列化
                    cookie_json = json.loads(cookie)

        else:
            #检查是否是私聊
            if isinstance(event, GroupMessageEvent):
                if msg in ["cookie_token=xxxxxxxxx;account_id=xxxxxxxxxxxxx", "login_ticket==xxxxxxxxxxxxxxx"]:
                    await ck.finish("这是绑定崩坏三cookie的实例，实际绑定的时候务必私聊！务必私聊！务必私聊！")
                await ck.finish("请立即撤回你的消息并私聊发送！")
            #格式调整，删除首尾引号
            if msg.startswith('"') or msg.startswith("'"):
                msg = msg[1:]
            if msg.endswith('"') or msg.endswith("'"):
                msg = msg[:-1]
            cookie = msg
            # 用: 代替=, ,代替;
            cookie = '{"' + cookie.replace('=', '": "').replace("; ", '","').replace(";", '","') + '"}'
            #反序列化
            cookie_json = json.loads(cookie)
            account_id = "" 
            cookie_token = ""
        #新增判断是否ck中包含login_ticket，如有则通过login_ticket获取需要的ck
            if 'login_ticket' in cookie_json:
                login_ticket = cookie_json['login_ticket']
        if login_ticket:
            logger.info("使用login_ticket获取ck")
            bbs_Cookie_url = f"https://webapi.account.mihoyo.com/Api/cookie_accountinfo_by_loginticket?login_ticket={login_ticket}"
            res = await AsyncHttpx.get(url=bbs_Cookie_url)
            res.encoding = "utf-8"
            data = json.loads(res.text)
            if "成功" in data["data"]["msg"]:
                account_id = str(data["data"]["cookie_info"]["account_id"])
                cookie_token = str(data["data"]["cookie_info"]["cookie_token"])
                if not ck_flag:
                    #检查是否是私聊
                    if isinstance(event, GroupMessageEvent):
                        await ck.finish("请立即撤回你的消息并私聊发送！")
                    msg = f"当前未配置查询ck，请在真寻配置文件config.yaml的bind_bh3.COOKIE下配置如下内容，然后重启真寻。\ncookie_token={cookie_token};account_id={account_id}"
                    await bind.finish(msg)
            elif data["data"]["msg"] == "登录信息已失效，请重新登录":
                raise InfoError(f'登录信息失效，请重新获取最新cookie进行绑定')
        else:
            if 'cookie_token' not in cookie_json:
                await bind.finish("请发送正确完整的cookie（需包含cookie_token）！")
            if 'account_id' not in cookie_json:
                await bind.finish("请发送正确完整的cookie！（需包含account_id）")
            account_id = cookie_json["account_id"]
            cookie_token = cookie_json["cookie_token"]
        spider = Finance(qid=qid, cookieraw=account_id + "," + cookie_token)
    except InfoError as e:
        await ck.finish(str(e))
    try:
        fi = await spider.get_finance()
    except InfoError as e:
        await ck.finish(str(e))
    fid = DrawFinance(**fi)
    im = fid.draw()
    img = MessageSegment.image(im)
    await ck.finish("已绑定"+img, at_sender=True)
