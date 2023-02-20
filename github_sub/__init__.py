import asyncio

from nonebot import on_command
from nonebot.typing import T_State
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message
from nonebot.adapters.onebot.v11.permission import GROUP
from nonebot.adapters.onebot.v11 import (
    Bot,
    MessageEvent,
)
from .data_source import (
    add_user_sub,
    SubManager,
    get_sub_status

)
from models.level_user import LevelUser
from configs.config import Config, NICKNAME
from utils.utils import scheduler, get_bot
from typing import Optional
from services.log import logger
from nonebot import Driver
from nonebot.params import CommandArg
import nonebot
from .model import GitHubSub

__zx_plugin_name__ = "github订阅"
__plugin_usage__ = """
usage：
    github新Comment，PR，Issue等提醒
    指令：
        添加github ['用户'/'仓库'] [用户名/{owner/repo}]
        删除github [用户名/{owner/repo}]
        查看github
        示例：添加github订阅用户 HibiKier
        示例：添加gb订阅仓库 HibiKier/zhenxun_bot
        示例：添加github用户 yajiwa
        示例：删除gb订阅 yajiwa
""".strip()
__plugin_des__ = "github订阅推送"
__plugin_cmd__ = ["添加github ['用户'/'仓库'] [用户名/{owner/repo}]", "删除github [用户名/{owner/repo}]", "查看github"]
__plugin_version__ = 0.4
__plugin_author__ = "yajiwa"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["github订阅", "gb订阅", "添加github", "删除github", "查看github"],
}
__plugin_configs__ = {
    "GROUP_GITHUB_SUB_LEVEL": {
        "value": 5,
        "help": "群内github订阅需要管理的权限",
        "default_value": 5,
    },
}

Config.add_plugin_config(
    "github_sub",
    "GITHUB_TOKEN",
    None,
    help_="登陆github获取https://github.com/settings/tokens/new"
)
Config.add_plugin_config(
    "github_sub",
    "GITHUB_ISSUE",
    True,
    help_="是否不推送Issue"
)

add_sub = on_command("添加github订阅", aliases={"添加github", "添加gb订阅"}, priority=5, permission=GROUP, block=True)
del_sub = on_command("删除github订阅", aliases={"删除github", "删除gb订阅"}, priority=5, permission=GROUP, block=True)
show_sub_info = on_command("查看github订阅", aliases={"查看github", "查看gb", "查看gb订阅"}, priority=5, block=True)

driver: Driver = nonebot.get_driver()

sub_manager: Optional[SubManager] = None


@driver.on_startup
async def _():
    global sub_manager
    sub_manager = SubManager()


@add_sub.handle()
async def _(event: MessageEvent, state: T_State, arg: Message = CommandArg()):
    msg = arg.extract_plain_text().strip().split()
    if len(msg) < 2:
        await add_sub.finish("参数不完全，请查看订阅帮助...")
    sub_type = msg[0]
    sub_url = msg[-1]
    sub_url = (sub_url.strip('/')).strip()
    if isinstance(event, GroupMessageEvent):
        if not await LevelUser.check_level(
                event.user_id,
                event.group_id,
                Config.get_config("github_sub", "GROUP_GITHUB_SUB_LEVEL"),
        ):
            await add_sub.finish(
                f"您的权限不足，群内订阅的需要 {Config.get_config('github_sub', 'GROUP_GITHUB_SUB_LEVEL')} 级权限..",
                at_sender=True,
            )
        sub_user = f"{event.user_id}:{event.group_id}"
    else:
        sub_user = f"{event.user_id}"
    state["sub_type"] = sub_type
    state["sub_user"] = sub_user
    if sub_type == "用户" or "仓库":
        if sub_type == "用户":
            sub_type_str = "user"
        else:
            sub_type_str = "repository"

        await add_sub.send(await add_user_sub(sub_type_str, sub_url, sub_user))
    else:
        await add_sub.finish("参数错误，第一参数必须为：用户/仓库！")


@del_sub.handle()
async def _(event: MessageEvent, arg: Message = CommandArg()):
    msg = arg.extract_plain_text().strip()
    if not msg:
        await del_sub.finish("请输入需要删除的用户或仓库", at_sender=True)
    if isinstance(event, GroupMessageEvent):
        id_ = f"{event.group_id}"
    else:
        id_ = f"{event.user_id}"
    if await GitHubSub.delete_github_sub(msg, id_):
        await del_sub.send(f"删除github订阅：{msg} 成功...")
        logger.info(
            f"(USER {event.user_id}, GROUP "
            f"{event.group_id if isinstance(event, GroupMessageEvent) else 'private'})"
            f" 删除订阅 {id_}"
        )
    else:
        await del_sub.send(f"删除订阅：{msg} 失败...")


@show_sub_info.handle()
async def _(event: MessageEvent):
    if isinstance(event, GroupMessageEvent):
        id_ = f"{event.group_id}"
    else:
        id_ = f"{event.user_id}"
    data = await GitHubSub.get_sub_data(id_)
    user_rst = ""
    repository_rst = ""
    num_user = 1
    num_repository = 1
    for x in data:
        if x.sub_type == "user":
            user_rst += (
                f"\t{num_user}. {x.sub_url}\n"
            )
            num_user += 1
        if x.sub_type == "repository":
            repository_rst += f"\t{num_repository}. {x.sub_url}\n"
            num_repository += 1
    user_rst = "当前订阅的github用户：\n" + user_rst if user_rst else user_rst
    repository_rst = "当前订阅的github仓库：\n" + repository_rst if repository_rst else repository_rst

    if not user_rst and not repository_rst:
        user_rst = (
            "该群目前没有任何订阅..." if isinstance(event, GroupMessageEvent) else "您目前没有任何订阅..."
        )
    await show_sub_info.send(user_rst + repository_rst)


# 推送
@scheduler.scheduled_job(
    "interval",
    seconds=1 * 30,
)
async def _():
    bot = get_bot()
    sub = None
    if bot:
        try:
            await sub_manager.reload_sub_data()
            sub = await sub_manager.random_sub_data()
            if sub:
                logger.info(f"github开始检测：{sub.sub_url}")
                rst = await get_sub_status(sub.sub_type, sub.sub_url, etag=sub.etag)
                if isinstance(rst, list):
                    await send_sub_msg_list(rst, sub, bot)
                else:
                    await send_sub_msg(rst, sub, bot)
        except Exception as e:
            import traceback
            logger.info(traceback.format_exc())
            logger.error(f"github订阅推送发生错误 sub_url：{sub.sub_url if sub else 0} {type(e)}：{e}")


async def send_sub_msg(rst: str, sub: GitHubSub, bot: Bot):
    """
    推送信息
    :param rst: 回复
    :param sub: GitHubSub
    :param bot: Bot
    """
    if rst:
        for x in sub.sub_users.split(",")[:-1]:
            try:
                if ":" in x:
                    await bot.send_group_msg(
                        group_id=int(x.split(":")[1]), message=Message(rst)
                    )
                else:
                    await bot.send_private_msg(user_id=int(x), message=Message(rst))
            except Exception as e:
                import traceback
                logger.info(traceback.format_exc())
                logger.error(f"github订阅推送发生错误 sub_url：{sub.sub_url} {type(e)}：{e}")


async def send_sub_msg_list(rst_list: list, sub: GitHubSub, bot: Bot ):
    """
    推送信息
    :param rst_list: 回复列表
    :param sub: GitHubSub
    :param bot: Bot
    """
    if rst_list:
        for x in sub.sub_users.split(",")[:-1]:
            try:
                mes_list = []
                for img in rst_list:
                    data = {
                        "type": "node",
                        "data": {"name": f"{NICKNAME}", "uin": f"{bot.self_id}", "content": img},
                    }
                    mes_list.append(data)
                if ":" in x:
                    await bot.send_group_forward_msg(
                        group_id=int(x.split(":")[1]), messages=mes_list)
                else:
                    await bot.send_group_forward_msg(user_id=int(x), messages=mes_list)
            except Exception as e:
                import traceback
                logger.info(traceback.format_exc())
                logger.error(f"github订阅推送发生错误 sub_url：{sub.sub_url} {type(e)}：{e}")
