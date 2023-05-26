from nonebot.adapters.onebot.v11 import Bot
from nonebot.adapters.onebot.v11.event import MessageEvent, GroupMessageEvent
from nonebot.plugin import on_command
from nonebot.typing import T_State

from .data_source import get_msg

__zx_plugin_name__ = "星穹铁道兑换码"
__plugin_usage__ = """
usage：
    获取星穹铁道前瞻直播兑换码
    指令：
        [星穹铁道]兑换码
        
""".strip()
__plugin_des__ = "查询星穹铁道前瞻直播兑换码"
__plugin_cmd__ = ["崩铁兑换码", "星铁兑换码", "星穹铁道兑换码"]
__plugin_type__ = ("崩坏：星穹铁道相关",)
__plugin_version__ = 0.1
__plugin_author__ = "mobius"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": __plugin_cmd__,
}

code = on_command(
    "星穹铁道兑换码", aliases={"崩铁兑换码", "星铁兑换码", "sr兑换码", "兑换码"}, priority=5)


@code.handle()
async def _(bot: Bot, event: MessageEvent, state: T_State):
    if str(state["_prefix"]["command_arg"]):
        await code.finish()
    codes = await get_msg(bot)
    if isinstance(event, GroupMessageEvent):
        await bot.send_group_forward_msg(group_id=event.group_id, messages=codes)
    else:
        await bot.send_private_forward_msg(user_id=event.user_id, messages=codes)
