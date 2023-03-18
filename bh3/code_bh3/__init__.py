'''
Author: MobiusT
Date: 2023-02-25 21:07:51
LastEditors: MobiusT
LastEditTime: 2023-03-18 19:12:55
'''
from nonebot.typing import T_State
from nonebot.adapters.onebot.v11 import Bot,  Message, MessageSegment
from nonebot.plugin import on_command
from nonebot.adapters.onebot.v11.event import MessageEvent, GroupMessageEvent

from .data_source import getCodes, get_week_code


__zx_plugin_name__ = "崩坏三兑换码"
__plugin_usage__ = """
usage：
    获取崩坏三前瞻直播及周福利礼包兑换码
    指令：
        [崩坏三]兑换码
        
""".strip()
__plugin_des__ = "查询崩坏三前瞻直播及周福利礼包兑换码"
__plugin_cmd__ = ["崩坏三兑换码"]
__plugin_type__ = ("崩坏三相关",)
__plugin_version__ = 0.1
__plugin_author__ = "mobius"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["崩坏三兑换码", "崩三兑换码", "崩3兑换码", "崩坏3兑换码"],
}

code = on_command(
    "崩坏三兑换码", aliases={"崩三兑换码", "崩3兑换码", "崩坏3兑换码", "兑换码"}, priority=5)

@code.handle()
async def _(bot: Bot, event: MessageEvent, state: T_State):
    if str(state["_prefix"]["command_arg"]):
        await code.finish()
    codes = await getCodes(bot)
    week_code = await get_week_code()
    if week_code:
        week_code = week_code.split("\n")
        codes.append(
            MessageSegment.node_custom(
                user_id=bot.self_id,
                nickname="周福利礼包: " + week_code[1].split("：")[0],
                content=Message(MessageSegment.text(week_code[1].split("：")[1])),
            )
        )
        codes.append(
            MessageSegment.node_custom(
                user_id=bot.self_id,
                nickname=week_code[2],
                content=Message(MessageSegment.text(week_code[3])),
            )
        )
    if isinstance(event, GroupMessageEvent):
        await bot.send_group_forward_msg(group_id=event.group_id, messages=codes)
    else:
        await bot.send_private_forward_msg(user_id=event.user_id, messages=codes)
