from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, Message, MessageSegment, GroupMessageEvent
from services.log import logger
from nonebot.params import CommandArg
from utils.message_builder import image
from ..modules.database import DB
from ..modules.image_handle import (ItemTrans, DrawFinance)
from ..modules.query import InfoError, Finance
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
        示例：崩坏三绑定114514官服
            崩坏三ckcookie_token=xxxxxxxxx;account_id=xxxxxxxxxxxxx
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
        "help": "登录https://bbs.mihoyo.com/bh3/ 后F12控制台输入document.cookie获取ck: cookie_token=xxxxxx;account_id=xxxxxx", 
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
async def _(event: MessageEvent, arg: Message = CommandArg()):
    qid_db = DB("uid.sqlite", tablename="qid_uid")
    qid = event.user_id
    #验证uid绑定状态
    try:
        qid_db.get_uid_by_qid(qid)
    except:
        await ck.finish("请先绑定uid，如崩坏三绑定114514官服")

    try:
        #获取参数
        msg = arg.extract_plain_text().strip()
        if not msg:
            img=image('ck.png', os.path.join(os.path.dirname(__file__)))
            await ck.finish(Message(img+"""私聊发送！！
            1.以无痕模式打开浏览器（Edge请新建InPrivate窗口）
            2.打开http://bbs.mihoyo.com/bh3/并登陆
            3.按下F12打开开发人员工具（不同浏览器按钮可能不同，可以设置里查找），打开控制台
            4.在下方空白处输入以下命令：
            var cookie=document.cookie;var ask=confirm('Cookie:'+cookie+'\\n\\nDo you want to copy the cookie to the clipboard?');if(ask==true){copy(cookie);msg=cookie}else{msg='Cancel'}
            5.按确定即可自动复制，手动复制也可以
            6.私聊真寻发送：崩坏三ck 刚刚复制的cookie
               如果遇到真寻不回复可能是ck里部分字符组合触发了真寻黑名单词汇拦截，可以只复制需要的ck内容，例：崩坏三ck cookie_token=xxxxxxxxx;account_id=xxxxxxxxxxxxx
            7.在不点击登出的情况下关闭无痕浏览器
                    """))
        #检查是否是私聊
        if isinstance(event, GroupMessageEvent):
            if msg is "cookie_token=xxxxxxxxx;account_id=xxxxxxxxxxxxx":
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
        print(cookie)
        #反序列化
        cookie_json = json.loads(cookie)
        print(cookie_json)
        if 'cookie_token' not in cookie_json:
            await bind.finish("请发送正确完整的cookie（需包含cookie_token）！")
        if 'account_id' not in cookie_json:
            await bind.finish("请发送正确完整的cookie！（需包含account_id）")
        spider = Finance(qid=qid, cookieraw=cookie_json["account_id"] + "," + cookie_json["cookie_token"])
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
