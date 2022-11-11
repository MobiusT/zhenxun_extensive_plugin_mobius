from nonebot import on_command
from utils.utils import scheduler, get_bot
from nonebot.adapters.onebot.v11 import MessageEvent, Message
from nonebot.permission import SUPERUSER
from services.log import logger
from nonebot.params import CommandArg
from ..modules.database import DB
from ..modules.mytyping import config, result
from pathlib import Path
from datetime import datetime
from genshinhelper import Honkai3rd
from genshinhelper.exceptions import GenshinHelperException
import json, os, asyncio

__zx_plugin_name__ = "崩坏三签到"
__plugin_usage__ = """
usage：
    崩坏三签到，cookie极为重要，请谨慎绑定
    ** 如果对拥有者不熟悉，并不建议添加cookie **
    该项目只会对cookie用于”崩坏三签到“，“崩坏三手账”
    指令：
        崩坏三签到       #签到并开启自动签到
        崩坏三签到关闭   #关闭自动签到
    如果未绑定cookie请at真寻并输入 帮助崩坏三绑定。
""".strip()
__plugin_des__ = "崩坏三签到"
__plugin_cmd__ = ["崩坏三签到", "崩坏三全部签到 [_superuser]"]
__plugin_type__ = ("崩坏三相关",)
__plugin_version__ = 0.1
__plugin_author__ = "mobius"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["崩坏三签到", "崩三签到", "崩3签到", "崩坏3签到"],
}


sign = on_command("崩坏三签到", aliases={"崩三签到", "崩3签到", "崩坏3签到"}, priority=5, block=True)
signAll = on_command("崩坏三全部签到", permission=SUPERUSER, aliases={"崩三全部签到", "崩3全部签到", "崩坏3全部签到"}, priority=5, block=True)



@signAll.handle()
async def _(event: MessageEvent, arg: Message = CommandArg()):
    await sign.send("开始手动全部签到", at_sender=True)
    cnt, total = await schedule_sign()
    await sign.finish(f"执行完成，状态刷新{cnt}条，共{total}条", at_sender=True)


@scheduler.scheduled_job("cron", hour=6, minute=5)
async def task():
    cnt, total = await schedule_sign()
    logger.info(f"崩坏三自动签到执行完成，状态刷新{cnt}条，共{total}条")


@sign.handle()
async def switch_autosign(event: MessageEvent, arg: Message = CommandArg()):
    """自动签到开关"""
    qid = str(event.user_id) #qq
    cmd = arg.extract_plain_text().strip()
    sign_data = load_data()
    #关闭签到
    if cmd in ["off", "关闭"]:
        if qid not in sign_data:
            await sign.finish("当前未开启崩坏三自动签到", at_sender=True)
        sign_data.pop(qid)
        save_data(sign_data)
        await sign.finish("崩坏三自动签到已关闭", at_sender=True)
    #签到
    hk3 = check_cookie(qid)
    if isinstance(hk3, str):
        await sign.finish(hk3, at_sender=True)
    result = autosign(hk3, qid)
    result += "\n自动签到已开启"
    await sign.finish(result, at_sender=True)

#自动签到
def autosign(hk3: Honkai3rd, qid: str):
    sign_data = load_data()
    today = datetime.today().day
    try:
        result_list = hk3.sign()
    except Exception as e:
        sign_data.update({qid: {"date": today, "status": False, "result": None}})
        return f"{e}\n自动签到失败."
    ret_list = f"〓米游社崩坏3签到〓\n####{datetime.date(datetime.today())}####\n"
    for n, res in enumerate(result_list):
        res = result(**res)
        ret = f"🎉No.{n + 1}\n{res.region_name}-{res.nickname}\n今日奖励:{res.reward_name}*{res.reward_cnt}\n本月累签:{res.total_sign_day}天\n签到结果:"
        if res.status == "OK":
            ret += f"OK✨"
        else:
            ret += f"舰长,你今天已经签到过了哦👻"
        ret += "\n###############\n"
        ret_list += ret
    #更新签到结果    
    sign_data.update({qid: {"date": today, "status": True, "result": ret_list}})
    save_data(sign_data)
    return ret_list.strip()

#签到文件
SIGN_PATH = Path(os.path.dirname(os.path.abspath(__file__))) / "sign_on.json"

#反序列化签到文件
def load_data():
    if not os.path.exists(SIGN_PATH):
        with open(SIGN_PATH, "w", encoding="utf8") as f:
            json.dump({}, f)
            return {}
    with open(SIGN_PATH, "r", encoding="utf8") as f:
        data: dict = json.load(f)
        return data

#序列化签到文件
def save_data(data):
    with open(SIGN_PATH, "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

#检查ck
def check_cookie(qid: str):
    db = DB("uid.sqlite", tablename="qid_uid")
    cookie = db.get_cookie(qid)
    if not cookie:
        return f"自动签到需要绑定cookie,at真寻并发送'帮助崩坏三绑定'查看如何绑定."
    hk3 = Honkai3rd(cookie=cookie)
    try:
        role_info = hk3.roles_info
    except GenshinHelperException as e:
        return f"{e}\ncookie不可用,请重新绑定."
    if not role_info:
        return f"未找到崩坏3角色信息,请确认cookie对应账号是否已绑定崩坏3角色."
    return hk3

#定时签到
async def schedule_sign():
    today = datetime.today().day
    sign_data = load_data()
    cnt = 0
    sum = len(sign_data)    
    for qid in sign_data:
        await asyncio.sleep(5)
        #判断今天是否未签到
        if sign_data[qid].get("date") != today or not sign_data[qid].get("status"):
            hk3 = check_cookie(qid)
            if isinstance(hk3, Honkai3rd):
                rs = autosign(hk3, qid)
                #推送签到结果      
                bot = get_bot()          
                if bot:
                    await bot.send_private_msg(user_id=int(qid), message=Message(rs))
                    logger.info(rs)
                cnt += 1
    return cnt, sum
