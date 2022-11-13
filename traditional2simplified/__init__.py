from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, Message
from nonebot.params import CommandArg
from services.log import logger
from configs.config import Config
import requests, json, time, hashlib, httpx

__zx_plugin_name__ = "繁中转简中"
__plugin_usage__ = """
usage：
    繁中转简中
    指令：
        簡體/簡體字/簡中+想要轉換的文字
""".strip()
__plugin_des__ = "繁中转简中"
__plugin_cmd__ = ["簡體"]
__plugin_type__ = ("常规插件",)
__plugin_version__ = 0.1
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
        "help": "http://api.fanyi.baidu.com/获取app_id", 
        "default_value": ''
    },
    "APPSECRET": {
        "value": '',
        "help": "http://api.fanyi.baidu.com/获取app_secret", 
        "default_value": ''
    },
}
convert = on_command("簡體", aliases={"簡體字", "簡中"}, priority=15, block=True)


@convert.handle()
async def _(event: MessageEvent, arg: Message = CommandArg()):
    #获取需要翻译的文字
    text=arg.extract_plain_text().strip()
    #读取密钥配置
    app_id = Config.get_config("traditional2simplified", "APPID")
    app_secret = Config.get_config("traditional2simplified", "APPSECRET")
    if not app_id:
        msg='未配置app_id, 请前往http://api.fanyi.baidu.com/获取'
        logger.error(msg)
        await convert.finish(msg)
    elif not app_secret:
        msg='未配置app_secret, 请前往http://api.fanyi.baidu.com/获取'
        logger.error(msg)
        await convert.finish(msg)
    try:
        #调用api
        msg = await translate(text, app_id, app_secret, "cht", "zh")      
        await convert.send(msg)
    except Exception as e:
        msg=f'转换出错{type(e)}：{e}'
        logger.error(msg)
        await convert.send(msg)

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

