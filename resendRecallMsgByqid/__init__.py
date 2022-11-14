import json, os
from pathlib import Path
from nonebot import get_bot
from nonebot.log import logger
from nonebot import on_command, on_notice
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, Message, GroupMessageEvent, GroupRecallNoticeEvent
from nonebot.params import CommandArg
from utils.utils import get_message_at


__zx_plugin_name__ = "禁止发烧"
__plugin_usage__ = """
usage：
    禁止发烧[at]/[qq]  加入禁止发烧列表
    允许发烧[at]/[qq]  移除禁止发烧列表

    群内指定qq撤回消息时自动将撤回的消息发送至群内
""".strip()
__plugin_des__ = "群内指定qq撤回消息时自动将撤回的消息发送至群内"
__plugin_settings__ = {
    "limit_superuser": False,
    "cmd": ["禁止发烧"],
}
__plugin_type__ = ("常规插件",)
__plugin_version__ = 0.1
__plugin_author__ = "mobius"

groupRecall = on_notice(priority=1, block=False)
listenList = on_command("禁止发烧", priority=5, permission=SUPERUSER, block=True)
unListenList = on_command("允许发烧", priority=5, permission=SUPERUSER, block=True)
jsonFile = Path(os.path.dirname(os.path.abspath(__file__))) / "recall.json"

# 检测撤回消息
@groupRecall.handle()
async def if_withdraw_handle(bot: Bot, event: GroupRecallNoticeEvent): 
    if event.notice_type == "group_recall":
        # 获取撤回消息的消息id
        recall_message_id = event.message_id
        # 获取撤回消息的消息内容
        recall_message_content = await bot.get_msg(message_id=recall_message_id)
        print(recall_message_content["message"])
        #q群
        gid=event.group_id
        #撤回者qq
        qid=event.user_id
        data: dict = load_data()    
        try:
            dataList: list = data[gid]     
            if str(qid) in dataList:  
                qidUser = await bot.get_group_member_info(group_id=event.group_id, user_id=qid)
                #撤回者qq名称
                qidName = qidUser["card"] or qidUser["nickname"]
                #拼装转发聊天记录
                mes_list = []
                data = {
                    "type": "node",
                    "data": {
                        "name": qidName,
                        "uin": f"{qid}",
                        "content": recall_message_content["message"],
                    },
                }
                mes_list.append(data)   
                #发送消息
                await bot.send_group_forward_msg(group_id=gid, messages=mes_list)
        except:
            logger.info("无禁止发烧名单")               
       


@listenList.handle()
async def _(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    #获取参数
    qid = arg.extract_plain_text().strip()
    qidList=[]
    if qid:
        try:
            qidUser = await bot.get_group_member_info(group_id=event.group_id, user_id=qid)

            qidList.append(qid)
        except Exception:
            await listenList.send(f"{qid}不是可用的qq号")
    #获取at
    ats =  get_message_at(event.json())
    if not len(ats)==0 :
        for qidAts in ats:
            qidList.append(str(qidAts))
    qidList=list(set(qidList))
    gid=str(event.group_id)
    data: dict = load_data()    
    msg=""
    try:
        dataList = data[gid]    
    except:
        dataList=[]
    for q in qidList:
        if q in dataList:
            await listenList.send(f"{q}已经在禁止发烧列表中")
        else:
            dataList.append(q)
            msg +=f"{q},"
    data.update({gid: dataList})
    save_data(data)
    if msg:
        await listenList.send(msg[:-1]+"已添加")

@unListenList.handle()
async def _(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    #获取参数
    qid = arg.extract_plain_text().strip()
    qidList=[]
    if qid:
        try:
            qidUser = await bot.get_group_member_info(group_id=event.group_id, user_id=qid)
            print(str(qidUser))
            qidList.append(qid)
        except Exception:
            await listenList.send(f"{qid}不是可用的qq号")
    #获取at
    ats =  get_message_at(event.json())
    if not len(ats)==0 :
        for qidAts in ats:
            qidList.append(str(qidAts))
    qidList=list(set(qidList))
    gid=str(event.group_id)
    data: dict = load_data()    
    msg=""
    try:
        dataList: list = data[gid]            
    except:
        await listenList.finish(f"{gid}中无禁止发烧成员")
    for q in qidList:
        if q in dataList:
            dataList.remove(q)
            msg +=f"{q},"
        else:
            await listenList.send(f"{q}不在禁止发烧列表中")           
    data.update({gid: dataList})
    save_data(data)
    if msg:
        await listenList.send(msg[:-1]+"已删除")

#反序列化文件
def load_data():
    if not os.path.exists(jsonFile):
        with open(jsonFile, "w", encoding="utf8") as f:
            json.dump({}, f)
            data: dict ={}
            return data
    with open(jsonFile, "r", encoding="utf8") as f:
        data: dict = json.load(f)
        return data

#序列化文件
def save_data(data):
    with open(jsonFile, "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
