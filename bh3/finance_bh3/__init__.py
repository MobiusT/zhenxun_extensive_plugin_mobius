from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, Message, MessageSegment
from services.log import logger
from nonebot.params import CommandArg
from ..modules.image_handle import DrawFinance
from ..modules.query import InfoError, Finance


__zx_plugin_name__ = "崩坏三手账"
__plugin_usage__ = """
usage：
    查看崩坏三手账，需要cookie，cookie极为重要，请谨慎绑定
    ** 如果对拥有者不熟悉，并不建议添加cookie **
    指令：
        崩坏三手账
    如果未绑定cookie请at真寻并输入 帮助崩坏三绑定。
""".strip()
__plugin_des__ = "查看崩坏三手账"
__plugin_cmd__ = ["崩坏三手账"]
__plugin_type__ = ("崩坏三相关",)
__plugin_version__ = 0.1
__plugin_author__ = "mobius"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["崩坏三手账", "崩三手账", "崩3手账", "崩坏3手账"],
}
__plugin_block_limit__ = {
    "rst": "[at]你正在查询！"
}
__plugin_cd_limit__ = {
    "cd": 60,
    "rst": "[at]你刚查过，别查了！"
}
finance = on_command("崩坏三手账", aliases={"崩三手账", "崩3手账", "崩坏3手账"}, priority=5, block=True)

#崩坏三手账
@finance.handle()
async def _(event: MessageEvent, arg: Message = CommandArg()):
    qid = event.user_id
    try:
        spider = Finance(str(qid))
    except InfoError as e:
        await finance.finish(str(e))
    try:
        fi = await spider.get_finance()
    except InfoError as e:
        await finance.finish(str(e))
    fid = DrawFinance(**fi)
    im = fid.draw()
    img = MessageSegment.image(im)
    await finance.finish(img, at_sender=True)
