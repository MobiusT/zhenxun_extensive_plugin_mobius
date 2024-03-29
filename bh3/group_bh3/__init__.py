import json
import os
from shutil import copy
from typing import Tuple, Any

from nonebot import on_regex, on_command
from nonebot.adapters.onebot.v11 import MessageEvent, Message, MessageSegment
from nonebot.params import RegexGroup
from nonebot.permission import SUPERUSER

from configs.config import Config
from utils.http_utils import AsyncHttpx
from utils.message_builder import at
from utils.utils import get_message_at, get_message_text
from ..modules.database import DB
from ..modules.image_handle import DrawGroupCharacter
from ..modules.mytyping import Index
from ..modules.query import InfoError, GetInfo
from ..utils.handle_id import handle_id_str

__zx_plugin_name__ = "崩坏三阵容"
__plugin_usage__ = """
usage：
    获取崩坏三账号阵容信息
    指令：
        崩坏三XXX阵容                #已绑定uid时使用
        崩坏三XXX阵容[uid][服务器]    #初次使用命令/查询别的玩家的女武神
        崩坏三XXX阵容[uid]           #查询已经绑定过uid的玩家的女武神
        崩坏三XXX阵容[@]             #查询at的玩家绑定的角色女武神
        崩坏三XXX阵容米游社/mys/MYS[米游社id] #查询该米游社id的角色女武神
    例：崩坏三天识卡阵容
        
""".strip()
__plugin_superuser_usage__ = f"""{__plugin_usage__}

    超级用户指令：    
        崩坏三阵容更新      #更新阵容简称
""".strip()
__plugin_des__ = "获取崩坏三账号阵容信息"
__plugin_cmd__ = ["崩坏三阵容"]
__plugin_type__ = ("崩坏三相关",)
__plugin_version__ = 0.2
__plugin_author__ = "mobius"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["崩坏三阵容", "崩三阵容", "崩3阵容", "崩坏3阵容"],
}
__plugin_block_limit__ = {
    "rst": "[at]你正在查询！"
}
__plugin_cd_limit__ = {
    "limit_type": "group",
    "rst": "正在查询中，请等待当前请求完成...",
}
group = on_regex(r"^(崩坏三|崩三|崩坏3|崩3)(.{1,3})阵容(.{0,30})$", priority=5, block=True)

updateGroup = on_command("崩坏三阵容更新", aliases={"崩三阵容更新", "崩3阵容更新", "崩坏3阵容更新"},
                         priority=5, permission=SUPERUSER, block=True)


@group.handle()
async def _(event: MessageEvent, reg_group: Tuple[Any, ...] = RegexGroup()):
    # 读取配置文件
    cookie = Config.get_config("bind_bh3", "COOKIE")
    if not cookie:
        await group.finish("需要真寻主人在config.yaml中配置cookie才能使用该功能")
    group_name = get_message_text(Message(reg_group[1])).strip()
    # 特殊适配律三家
    if group_name == "虚三家":
        group_name = "终始真"
    elif group_name == "律三家":
        group_name = "炎雷理"
    group_json = await get_group_json()
    group_list = []
    for name in group_name:
        if isinstance(group_json[name], str):
            group_list.append(group_json[name])
        elif isinstance(group_json[name], list):
            group_list.extend(iter(group_json[name]))
        else:
            await group.finish("未找到{groupName}中的{name},请联系管理员添加配置")
    ats = get_message_at(event.json())
    arg = str(reg_group[2]) if len(ats) == 0 else ""
    region_db = DB("uid.sqlite", tablename="uid_region")
    qid_db = DB("uid.sqlite", tablename="qid_uid")
    # 获取绑定的角色信息
    try:
        role_id, region_id, qid = handle_id_str(event, arg)
    except InfoError as e:
        return await group.send(Message(f"{at(event.user_id)}出错了：{str(e)}"))
        # 查询角色
    spider = GetInfo(server_id=region_id, role_id=role_id)
    try:
        _, data = await spider.fetch(spider.valkyrie)
        _, index_data = await spider.fetch(spider.index)
    except InfoError as e:
        return await group.send(Message(f"{at(event.user_id)}出错了：{str(e)}"))
    # 绘图
    region_db.set_region(role_id, region_id)
    qid_db.set_uid_by_qid(qid, role_id)
    index = Index(**index_data["data"])
    dr = DrawGroupCharacter(**data["data"])
    im = await dr.draw_chara(index, qid, group_list)
    img = MessageSegment.image(im)
    await group.finish(img, at_sender=True)


# 崩坏三阵容更新
@updateGroup.handle()
async def _():
    data_remote = await get_group_from_git()
    data_local = await get_group_json()
    for key in data_remote.keys():
        if key in data_local.keys():
            # 跳过相同阵容
            if data_local[key] == data_remote[key] and isinstance(data_local[key], str):
                continue
            if isinstance(data_local[key], str):
                data_local[key] = [data_local[key]]
            if isinstance(data_remote[key], str):
                data_remote[key] = [data_remote[key]]
                # 合并阵容
            data_local[key] = list(set(data_local[key] + data_remote[key]))
        else:
            # 新增阵容简称
            data_local[key] = data_remote[key]
    # 保存阵容
    with open(
            os.path.join(os.path.dirname(__file__), "./group.json"), "w", encoding="utf8"
    ) as f:
        json.dump(data_local, f, ensure_ascii=False, indent=4)
    await updateGroup.finish("更新完成。")


# 获取本地文件
async def get_group_json():
    group_file = os.path.join(os.path.dirname(__file__), "./group.json")
    if not os.path.exists(group_file):
        copy(os.path.join(os.path.dirname(__file__), "./group_template.json"), group_file)
    with open(group_file, "r", encoding="utf8") as f:
        group_json = json.load(f)
        f.close()
    return group_json


# 获取git文件
async def get_group_from_git():
    url = "https://ghproxy.com/https://raw.githubusercontent.com/" \
          "MobiusT/zhenxun_extensive_plugin_mobius/main/bh3/group_bh3/group_template.json"
    data = await AsyncHttpx.get(url, follow_redirects=True)
    data = json.loads(data.text)
    return data
