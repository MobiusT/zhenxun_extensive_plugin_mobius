import json
from re import findall
from typing import Dict, List
from time import time, strftime, localtime

from httpx import AsyncClient
from nonebot.log import logger
from nonebot.adapters.onebot.v11 import Bot, Message, MessageSegment


async def getData(type, data: Dict = {}) -> Dict:
    """米哈游接口请求"""

    url = {
        "index": f"https://api-takumi.mihoyo.com/event/bbslive/index?act_id={data.get('actId', '')}", 
        "mi18n": f"https://webstatic.mihoyo.com/admin/mi18n/bbs_cn/{data.get('mi18n', '')}/{data.get('mi18n', '')}-zh-cn.json",  
        "code": f"https://webstatic.mihoyo.com/bbslive/code/{data.get('actId', '')}.json?version=1&time={int(time())}", 
        "actId": "https://bbs-api.mihoyo.com/painter/api/user_instant/list?offset=0&size=20&uid=73565430",  # 爱酱小跟班
    }
    async with AsyncClient() as client:
        try:
            res = await client.get(url[type])
            return res.json()
        except Exception as e:
            logger.opt(exception=e).error(f"{type} 接口请求错误")
            return {"error": f"[{e.__class__.__name__}] {type} 接口请求错误"}


async def getActId() -> str:
    """获取 ``act_id``"""

    ret = await getData("actId")
    if ret.get("error") or ret.get("retcode") != 0:
        return ""

    actId = ""
    keywords = ["《崩坏3》", "特别节目"]
    for p in ret["data"]["list"]:
        post = p.get("post", {}).get("post", {})
        if not post:
            continue
        if not all(word in post["subject"] for word in keywords):
            continue        
        shit = json.loads(post["structured_content"])
        for segment in shit:
            link = segment.get("attributes", {}).get("link", "")
            if "点击前往" in segment.get("insert", "") and link:
                matched = findall(r"act_id=(\d{8}bh3\d{4})", link)
                if matched:
                    actId = matched[0]
        if actId:
            break

    return actId

async def get_week_code() -> str:
    """获取 ``act_id``"""
    ret = await getData("actId")
    if ret.get("error") or ret.get("retcode") != 0:
        return ""

    code = ""
    keywords = ["本周福利礼包掉落"]
    for p in ret["data"]["list"]:
        post = p.get("post", {}).get("post", {})
        if not post:
            continue
        if not all(word in post["content"] for word in keywords):
            continue        
        shit = json.loads(post["structured_content"])
        for segment in shit:
            if isinstance(segment.get("insert", ""), str) and "\n★叮" in segment.get("insert", ""):
                code = f'★{segment.get("insert").split("★")[1]}'
        if code:
            break

    return code


async def getCodes(bot: Bot) -> List[MessageSegment]:
    """生成最新前瞻直播兑换码合并转发消息"""

    actId = await getActId()
    if not actId:
        return [
            MessageSegment.node_custom(
                user_id=bot.self_id,
                nickname="崩环三前瞻直播",
                content=Message(MessageSegment.text("暂无前瞻直播资讯！")),
            )
        ]

    indexRes = await getData("index", {"actId": actId})
    if not indexRes.get("data") or not indexRes["data"].get("mi18n", ""):
        return [
            MessageSegment.node_custom(
                user_id=bot.self_id,
                nickname="崩环三前瞻直播",
                content=Message(
                    MessageSegment.text(indexRes.get("message") or "没有找到 mi18n！")
                ),
            )
        ]
    mi18n = indexRes["data"].get("mi18n", "")

    mi18nRes = await getData("mi18n", {"mi18n": mi18n})
    codeRes = await getData("code", {"actId": actId})
    nickname = mi18nRes.get("act-title", "").replace("特别节目", "直播") or "崩环三前瞻直播"
    if indexRes["data"].get("remain", 0) or not len(codeRes):
        return [
            MessageSegment.node_custom(
                user_id=bot.self_id,
                nickname=nickname,
                content=Message(MessageSegment.image(mi18nRes["pc-kv"])),
            ),
            MessageSegment.node_custom(
                user_id=bot.self_id,
                nickname=nickname,
                content=Message(
                    MessageSegment.text(
                        "预计第一个兑换码发放时间为 "
                        + strftime("%m 月 %d 日 %H:%M", localtime(int(mi18nRes["time1"])))
                        + "\n\n* 官方接口数据有 2 分钟左右延迟，请耐心等待下~"
                    )
                ),
            ),
        ]

    codes = [
        MessageSegment.node_custom(
            user_id=bot.self_id,
            nickname=nickname,
            content=Message(
                MessageSegment.text(
                    f"当前发放了 {len(codeRes)} 个兑换码\n{mi18nRes['exchange-tips']}"
                )
            ),
        )
    ]
    for codeInfo in codeRes:
        gifts = findall(
            r">\s*([\u4e00-\u9fa5]+|\*[0-9]+)\s*<",
            codeInfo["title"].replace("&nbsp;", " "),
        )
        codes.append(
            MessageSegment.node_custom(
                user_id=bot.self_id,
                nickname="+".join(g for g in gifts if not g[-1].isdigit()) or nickname,
                content=Message(MessageSegment.text(codeInfo["code"])),
            )
        )
    return codes
