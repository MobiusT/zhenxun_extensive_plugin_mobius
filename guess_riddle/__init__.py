'''
Author: MobiusT
Date: 2023-01-20 18:51:43
LastEditors: MobiusT
LastEditTime: 2023-01-20 19:24:17
'''
from nonebot import on_command
from nonebot.adapters.onebot.v11 import GROUP, Bot, GroupMessageEvent, Message
from nonebot.params import CommandArg
from nonebot.log import logger
from utils.http_utils import AsyncHttpx
from models.bag_user import BagUser
import json



__zx_plugin_name__ = "猜谜语"
__plugin_usage__ = """
usage：
    猜谜语
    指令：
        猜谜语/猜谜 开始游戏
        解谜语/解谜[答案] 提交答案
        结束猜谜语 结束游戏
""".strip()
__plugin_des__ = "猜谜语"
__plugin_cmd__ = [
    "猜谜语",
    "解谜语",
    "结束猜谜语",
]
__plugin_type__ = ("群内小游戏",)
__plugin_version__ = 0.1
__plugin_author__ = "Mobius"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": __plugin_cmd__,
}

start = on_command("猜谜语", aliases={"猜谜"}, permission=GROUP, priority=5, block=True)

submit = on_command("解谜语", aliases={"解谜", "解密"}, permission=GROUP, priority=5, block=True)

stop_game = on_command("结束猜谜语", aliases={"结束猜谜"}, permission=GROUP, priority=5, block=True)
answer = {}
question = {}


@start.handle()
async def _(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    global answer, question
    msg = arg.extract_plain_text().strip()
    if msg:
        return
    if event.group_id in answer:
        if answer[event.group_id]:
            await bot.send(event, "上一局游戏还未结束!")
    else:
        question[event.group_id], answer[event.group_id] = await random_question()
        await bot.send(event, f"{question[event.group_id]}\n发送'解谜'+答案 进行解答。")


@submit.handle()
async def _(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    global answer
    if event.group_id in answer:
        if answer[event.group_id]:
            msg = arg.extract_plain_text().strip()
            bounce = 100
            if msg not in answer[event.group_id]:
                await bot.send(event,
                               "答案不对!",
                               at_sender=True)
            else:
                await BagUser.add_gold(event.user_id, event.group_id, bounce)
                await bot.send(event,
                               f"恭喜你回答正确,奖励你{bounce}金币!",
                               at_sender=True)
                del answer[event.group_id]
        else:
            await bot.send(event, "现在没有开局哦,请输入猜谜语来开始游戏!")
    else:
        await bot.send(event, "现在没有开局哦,请输入猜谜语来开始游戏!")


@stop_game.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    global answer
    if event.group_id in answer:
        if answer[event.group_id]:
            answer_list = ''.join(answer[event.group_id])
            await submit.send(f"参考答案:\n{answer_list}\n本轮游戏已结束!")
            del answer[event.group_id]
    else:
        await submit.send("当前没有正在进行的猜谜语游戏哦!")

async def random_question():
    res = await AsyncHttpx.get(f"https://v.api.aa1.cn/api/api-miyu/index.php", timeout=30)
    res.encoding = "utf8"
    data = json.loads(res.text)
    if data["code"] != "1":
        logger.error(f"生成谜语出错！{data}")
        raise Exception("生成谜语出错！")
    logger.info(f"生成谜语: {data}")
    return f'{data["ts"]}:{data["mt"]}', data["md"]
