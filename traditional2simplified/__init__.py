import hashlib
import json
import os
import re
import time

import httpx
import nonebot
from nonebot import on_command, Driver
from nonebot.adapters.onebot.v11 import MessageEvent, Message
from nonebot.message import event_preprocessor
from nonebot.params import CommandArg

from configs.config import Config
from services.log import logger

__zx_plugin_name__ = "繁中转简中"
__plugin_usage__ = """
usage：
    繁中转简中
    指令：
        簡體/簡體字/簡中+想要轉換的文字     #以对应的简体字执行命令
        輸出簡體/簡體字/簡中+想要轉換的文字  #回复转换结果

        更新映射  #更新map.json映射关系
        
        在插件目录下新建map.json写入转换关系：{"需要调整的字": "解析出错的结果需要显示的结果"}  
        例{"德": "得的"， "斯": "死四"}            
        原文为 德斯  且转换结果为 得死 时，返回 的四
""".strip()
__plugin_des__ = "繁中转简中"
__plugin_cmd__ = ["簡體"]
__plugin_type__ = ("常规插件",)
__plugin_version__ = 0.2
__plugin_author__ = "mobius"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["簡體", "簡體字", "簡中"],
}
__plugin_configs__ = {
    "APPID": {
        "value": '',
        "help": "https://api.fanyi.baidu.com/获取app_id",
        "default_value": ''
    },
    "APPSECRET": {
        "value": '',
        "help": "https://api.fanyi.baidu.com/获取app_secret",
        "default_value": ''
    },
}
convert = on_command("輸出簡體", aliases={"輸出簡體字", "輸出簡中", "輸出簡"}, priority=15, block=True)
update_map = on_command("更新映射", priority=15, block=True)
MAPJSOM = {}

driver: Driver = nonebot.get_driver()


@driver.on_startup
async def _():
    global MAPJSOM
    MAPJSOM = load_data()


# 消息拦截
@event_preprocessor
async def handle(event: MessageEvent):
    msgs = event.get_message()
    if len(msgs) < 1 or msgs[0].type != "text":
        return
    msg = str(msgs[0]).lstrip()
    if not msg:
        return
    try:
        cmd_str = re.compile(r"^(簡體字|簡體|簡中|簡)")  # 去掉命令头
        if cmd_str.search(msg):
            msg = cmd_str.sub('', msg)
            try:
                # 调用api
                msg = await convert_str(msg)
                event.message[0].data["text"] = msg
                logger.info(f"繁中转简中: {msg}")
            except Exception as e:
                logger.error(str(e))
                return
    except:
        return


@convert.handle()
async def _(arg: Message = CommandArg()):
    # 获取需要翻译的文字
    text = arg.extract_plain_text().strip()
    if not text:
        return
    try:
        # 调用api
        msg = await convert_str(text)
        await convert.send(msg)
    except Exception as e:
        logger.error(str(e))
        await convert.finish(str(e))


@update_map.handle()
async def _():
    global MAPJSOM
    if MAPJSOM := load_data():
        await update_map.finish("更新完成")
    await update_map.finish("更新失败，map.json文件不存在或无法解析。")


async def convert_str(text: str) -> str:
    global MAPJSOM
    # 读取密钥配置
    app_id = Config.get_config("traditional2simplified", "APPID")
    app_secret = Config.get_config("traditional2simplified", "APPSECRET")
    await check_config(app_id, app_secret)
    try:
        _map = await get_map(text)
        # 调用api
        msg = await translate(text, app_id, app_secret, "cht", "zh")
        if _map:
            for key in _map:
                for index in _map[key]:
                    if msg[index:index + 1] == MAPJSOM[key][:1]:
                        msg = msg[:index] + MAPJSOM[key][1:] + msg[index + 1:]
        return msg
    except Exception as e:
        msg = f'转换出错{type(e)}：{e}'
        logger.error(msg)
        raise Exception(msg) from e


async def get_map(text):
    global MAPJSOM
    _map = {}
    if MAPJSOM:
        for key in MAPJSOM:
            if positions := get_index(text, key):
                _map[key] = positions
    return _map


async def check_config(app_id, app_secret):
    if not app_id:
        msg = '未配置app_id, 请前往https://api.fanyi.baidu.com/获取'
        logger.error(msg)
        raise Exception(msg)
    elif not app_secret:
        msg = '未配置app_secret, 请前往https://api.fanyi.baidu.com/获取'
        logger.error(msg)
        raise Exception(msg)


def get_index(msg: str, key: str):
    # 查找字符"o"的位置
    pos = msg.find(key)
    # 获取字符"o"在字符串中出现的所有位置
    positions = []
    while pos != -1:
        positions.append(pos)
        pos = msg.find(key, pos + 1)
    return positions


async def translate(text: str, appid: str, apikey: str, lang_from: str = "auto", lang_to: str = "zh") -> str:
    salt = str(round(time.time() * 1000))
    sign_raw = appid + text + salt + apikey
    sign = hashlib.md5(sign_raw.encode("utf8")).hexdigest()
    params = {
        "q": text,
        "from": lang_from,
        "to": lang_to,
        "appid": appid,
        "salt": salt,
        "sign": sign,
    }
    url = "https://fanyi-api.baidu.com/api/trans/vip/translate"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        result = resp.json()
    try:
        return result["trans_result"][0]["dst"]
    except Exception:
        return str(result)


# 反序列化排行文件
def load_data():
    _file = os.path.join(os.path.dirname(__file__), "./map.json")
    if not os.path.exists(_file):
        return {}
    with open(_file, "r", encoding="utf8") as f:
        try:
            data: dict = json.load(f)
            return data
        except:
            logger.warning("map文件无法解析")
            return {}
