import json
from datetime import datetime, timezone, timedelta
from re import findall
from time import time
from typing import Dict, List, Union

from httpx import AsyncClient
from nonebot.adapters.onebot.v11 import Bot, Message, MessageSegment
from nonebot.log import logger

TZ = timezone(timedelta(hours=8))


async def get_data(url_type, data: Dict = None) -> Dict:
    """米哈游接口请求"""

    if data is None:
        data = {}
    url = {
        "actId": "https://bbs-api.mihoyo.com/painter/api/user_instant/list?offset=0&size=20&uid=288909600",  # 崩坏星穹铁道
        "index": "https://api-takumi.mihoyo.com/event/miyolive/index",
        "code": "https://api-takumi-static.mihoyo.com/event/miyolive/refreshCode"
    }
    async with AsyncClient() as client:
        try:
            if url_type == "index":
                res = await client.get(
                    url[url_type], headers={"x-rpc-act_id": data.get("actId", "")}
                )
            elif url_type == "code":
                res = await client.get(
                    url[url_type],
                    params={
                        "version": data.get("version", ""),
                        "time": f"{int(time())}",
                    },
                    headers={"x-rpc-act_id": data.get("actId", "")},
                )
            else:
                res = await client.get(url[url_type])
            return res.json()
        except Exception as e:
            logger.opt(exception=e).error(f"{url_type} 接口请求错误")
            return {"error": f"[{e.__class__.__name__}] {url_type} 接口请求错误"}


async def get_actid() -> str:
    """获取 ``act_id``"""

    ret = await get_data("actId")
    if ret.get("error") or ret.get("retcode") != 0:
        return ""

    act_id = ""
    keywords = ["特别节目"]
    for p in ret["data"]["list"]:
        post = p.get("post", {}).get("post", {})
        if not post:
            continue
        if any(word not in post["subject"] for word in keywords):
            continue
        shit = json.loads(post["structured_content"])
        for segment in shit:
            link = segment.get("attributes", {}).get("link", "")
            if matched := findall(r"act_id=(.*?)&", link):
                act_id = matched[0]
        if act_id:
            break
    return act_id


async def get_live_data(act_id: str) -> Dict:
    """获取直播数据，尤其是 ``code_ver``"""

    ret = await get_data("index", {"actId": act_id})
    if ret.get("error") or ret.get("retcode") != 0:
        return {"error": ret.get("error") or ret.get("message") or "前瞻直播数据异常"}
    live_data_raw = ret["data"]["live"]
    live_template = json.loads(ret["data"]["template"])
    live_data = {
        "code_ver": live_data_raw["code_ver"],
        "title": live_data_raw["title"].replace("特别节目", ""),
        "header": live_template["kvDesktop"],
        "room": live_template["liveConfig"][0]["desktop"],
    }
    if live_data_raw["is_end"]:
        live_data["review"] = live_template["reviewUrl"]["args"]["post_id"]
    else:
        now = datetime.fromtimestamp(time(), TZ)
        start = datetime.strptime(live_data_raw["start"], "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=TZ
        )
        if now < start:
            live_data["start"] = live_data_raw["start"]

    return live_data


async def get_codes(version: str, act_id: str) -> Union[Dict, List[Dict]]:
    """获取兑换码"""
    ret = await get_data("code", {"version": version, "actId": act_id})
    if ret.get("error") or ret.get("retcode") != 0:
        return {"error": ret.get("error") or "兑换码数据异常"}

    codes_data = []
    for code_info in ret["data"]["code_list"]:
        gifts = findall(
            r">\s*([\u4e00-\u9fa5]+|\*\d+)\s*\*<",
            code_info["title"].replace("&nbsp;", " "),
        )
        codes_data.append(
            {
                "items": "+".join(g for g in gifts if not g[-1].isdigit()),
                "code": code_info["code"],
            }
        )

    return codes_data


async def get_msg(bot: Bot) -> List[MessageSegment]:
    """生成最新前瞻直播兑换码合并转发消息"""

    act_id = await get_actid()
    if not act_id:
        return [
            MessageSegment.node_custom(
                user_id=int(bot.self_id),
                nickname="星穹铁道前瞻直播",
                content=Message(MessageSegment.text("暂无前瞻直播资讯！")),
            )
        ]

    live_data = await get_live_data(act_id)
    if live_data.get("error"):
        return [
            MessageSegment.node_custom(
                user_id=int(bot.self_id),
                nickname="星穹铁道前瞻直播",
                content=Message(MessageSegment.text(live_data["error"])),
            )
        ]
    elif live_data.get("start"):
        return [
            MessageSegment.node_custom(
                user_id=int(bot.self_id),
                nickname=live_data["title"],
                content=Message(MessageSegment.image(live_data["header"])),
            ),
            MessageSegment.node_custom(
                user_id=int(bot.self_id),
                nickname=live_data["start"],
                content=Message(MessageSegment.text(live_data["room"])),
            ),
        ]

    codes_data = await get_codes(live_data["code_ver"], act_id)
    if isinstance(codes_data, Dict):
        return [
            MessageSegment.node_custom(
                user_id=int(bot.self_id),
                nickname=live_data["title"],
                content=Message(MessageSegment.text(codes_data["error"])),
            )
        ]
    codes_msg = [
        MessageSegment.node_custom(
            user_id=int(bot.self_id),
            nickname=live_data["title"],
            content=Message(
                MessageSegment.text(
                    f"当前发布了 {len(codes_data)} 个兑换码，请在有效期内及时兑换哦~"
                    + "\n\n* 官方接口数据有 2 分钟左右延迟，请耐心等待下~"
                )
            ),
        ),
        *[
            MessageSegment.node_custom(
                user_id=int(bot.self_id),
                nickname=code["items"] or live_data["title"],
                content=Message(MessageSegment.text(code["code"])),
            )
            for code in codes_data
        ],
    ]
    if live_data.get("review"):
        codes_msg.append(
            MessageSegment.node_custom(
                user_id=int(bot.self_id),
                nickname=live_data["title"],
                content=Message(
                    MessageSegment.text(
                        "直播已经结束，查看回放：\n\n"
                        + f"https://www.miyoushe.com/ys/article/{live_data['review']}"
                    )
                ),
            )
        )
    return codes_msg
