from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, Message, MessageSegment, GroupMessageEvent
from services.log import logger
from nonebot.params import CommandArg
from configs.config import Config
from utils.http_utils import AsyncHttpx
from utils.message_builder import image, at
from utils.utils import scheduler, get_bot
from plugins.genshin.query_user._models import Genshin
from ..modules.database import DB
from ..modules.image_handle import (ItemTrans, DrawFinance)
from ..modules.query import InfoError, Finance, NotBindError
from string import ascii_letters, digits
from io import BytesIO
import json, re, os, random, qrcode, base64


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
        崩坏三ck扫码         # 使用米游社扫码绑定崩三ck（不可用扫码器）
        示例：崩坏三绑定114514官服
            崩坏三cklogin_ticket==xxxxxxxxxxxxxxx
    如果不明白怎么获取cookie请输入“崩坏三ck”。
""".strip()
__plugin_des__ = "绑定自己的崩坏三uid等"
__plugin_cmd__ = ["崩坏三绑定[uid][服务器]", "崩坏三服务器列表", "崩坏三ck"]
__plugin_type__ = ("崩坏三相关",)
__plugin_version__ = 0.2
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

qrcode_data_map = {}

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
        if "扫码" == msg:
            if str(event.user_id) in qrcode_data_map:
                await ck.finish('请扫描上一次的二维码')
            qrcode_data = await get_qrcode_data()
            qrcode_data_map[str(event.user_id)] = qrcode_data
            qrcode_img = generate_qrcode(qrcode_data['url'])
            qrcode_data_map[str(event.user_id)]['qrcode_img'] = qrcode_img            
            qrcode_data_map[str(event.user_id)]['user_id'] = str(event.user_id)
            msg_data = await ck.send(MessageSegment.image(qrcode_img) + 
                f'\n请在3分钟内使用米游社扫码并确认进行绑定。\n注意：\n1.扫码即代表你同意将Cookie信息授权给真寻及{event.sender.card}\n2.扫码时会提示登录崩坏三，实际不会顶号\n3.其他人请不要乱扫，否则会将你的账号绑到TA身上！',
                at_sender=True)
            qrcode_data_map[str(event.user_id)]['msg_id'] = msg_data['message_id']
            if isinstance(event, GroupMessageEvent):
                qrcode_data_map[str(event.user_id)]['group_id'] = event.group_id
            # 添加定时任务
            scheduler.add_job(
                func=check_qrcode,  
                trigger="cron", 
                second='*/10',
                misfire_grace_time=10,
                args=(qrcode_data_map[str(event.user_id)], ck_flag, ),
                id=f'bh3_check_qrcode_{event.user_id}'
            )
            return
        elif "同步" == msg:
            #获取原神uid
            genshin_user = await Genshin.get_or_none(user_qq = event.user_id)
            login_ticket = genshin_user.login_ticket if genshin_user else None
            cookie = genshin_user.cookie if genshin_user else None
            if not login_ticket:
                if not cookie:
                    raise InfoError(f'尚未绑定原神cookie，请先绑定原神cookie或发送 崩坏三ck 绑定崩坏三ck')
                else:
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
            if not ck_flag:
                #检查是否是私聊
                if isinstance(event, GroupMessageEvent):
                    await ck.finish("请立即撤回你的消息并私聊发送！")
                msg = f"当前未配置查询ck，请在真寻配置文件config.yaml的bind_bh3.COOKIE下配置如下内容，然后重启真寻。\ncookie_token={cookie_json['cookie_token']};account_id={cookie_json['account_id']}"
                await bind.finish(msg)
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

# 获取二维码连接
async def get_qrcode_data():
    device_id = ''.join(random.choices((ascii_letters + digits), k=64))
    app_id = '1' # 崩坏三
    data = {'app_id': app_id,
            'device': device_id}
    res = await AsyncHttpx.post('https://hk4e-sdk.mihoyo.com/hk4e_cn/combo/panda/qrcode/fetch?',json=data)
    url = res.json()['data']['url']
    ticket = url.split('ticket=')[1]
    return {'app_id': app_id, 'ticket': ticket, 'device': device_id, 'url': url}

# 生成二维码
def generate_qrcode(url):
    qr = qrcode.QRCode(version=1,
                       error_correction=qrcode.constants.ERROR_CORRECT_L,
                       box_size=10,
                       border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    bio = BytesIO()
    img.save(bio)
    return f'base64://{base64.b64encode(bio.getvalue()).decode()}'

# 校验登录结果
async def check_login(qrcode_data: dict):
    data = {'app_id': qrcode_data['app_id'],
            'ticket': qrcode_data['ticket'],
            'device': qrcode_data['device']}
    res = await AsyncHttpx.post('https://hk4e-sdk.mihoyo.com/hk4e_cn/combo/panda/qrcode/query?', json=data)
    return res.json()

# 获取token
async def get_cookie_token(game_token: dict):
    res = await AsyncHttpx.get(
        f"https://api-takumi.mihoyo.com/auth/api/getCookieAccountInfoByGameToken?game_token={game_token['token']}&account_id={game_token['uid']}")
    cookie_token_data = res.json()
    return cookie_token_data['data']['uid'], cookie_token_data['data']['cookie_token']

# 检查登录状态
async def check_qrcode(qrcode_data: dict, ck_flag = True):
    send_msg = None
    try:
        status_data = await check_login(qrcode_data)
        if status_data['retcode'] != 0:
            send_msg = '绑定二维码已过期，请重新发送扫码绑定指令'
            qrcode_data_map.pop(qrcode_data["user_id"])
            scheduler.remove_job(f'bh3_check_qrcode_{qrcode_data["user_id"]}',)
        # 校验通过
        elif status_data['data']['stat'] == 'Confirmed':
            qrcode_data_map.pop(qrcode_data["user_id"])
            scheduler.remove_job(f'bh3_check_qrcode_{qrcode_data["user_id"]}',)
            game_token = json.loads(status_data['data']['payload']['raw'])
            if "token" not in game_token.keys():
                send_msg = f"请勿使用扫码器，请使用米游社扫码"
                return
            #获取token
            account_id, cookie_token = await get_cookie_token(game_token)
            if not ck_flag:
                send_msg = f"当前未配置查询ck，请在真寻配置文件config.yaml的bind_bh3.COOKIE下配置如下内容，然后重启真寻。\ncookie_token={cookie_token};account_id={account_id}"
                return
            spider = Finance(qid=qrcode_data["user_id"], cookieraw=account_id + "," + cookie_token)
            try:
                #绑定ck
                fi = await spider.get_finance()
            except InfoError as e:
                send_msg = str(e)
                return
            fid = DrawFinance(**fi)
            im = fid.draw()
            img = MessageSegment.image(im)
            send_msg = "已绑定"+img
    except Exception as e:
        import traceback
        logger.error("崩三ck扫码检查出错：" + traceback.format_exc())
        send_msg = type(e) + str(e)
        scheduler.remove_job(f'bh3_check_qrcode_{qrcode_data["user_id"]}',)
    finally:
        # 反馈绑定结果
        if send_msg:
            bot = get_bot()
            if bot:
                if ck_flag and "group_id" in qrcode_data.keys():
                    await bot.send_group_msg(group_id=qrcode_data["group_id"], message=at(qrcode_data["user_id"]) + send_msg)
                else:
                    await bot.send_private_msg(user_id=qrcode_data["user_id"], message=send_msg)