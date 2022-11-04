from utils.utils import get_bot, get_message_at
from nonebot import on_command
from nonebot.adapters.onebot.v11 import GROUP, MessageEvent, Message
from nonebot.params import CommandArg
from services.log import logger
from configs.config import Config
import requests, json

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
__plugin_cd_limit__ = {
    "cd": 3,
    "rst": "[at]慢点说！"
}
__plugin_configs__ = {
    "APPID": {
        "value": '', 
        "help": "https://www.mxnzp.com/获取app_id", 
        "default_value": ''
    },
    "APPSECRET": {
        "value": '',
        "help": "https://www.mxnzp.com/获取app_secret", 
        "default_value": ''
    },
}
convert = on_command("簡體", aliases={"簡體字", "簡中"}, priority=15, block=True)


@convert.handle()
async def _(event: MessageEvent, arg: Message = CommandArg()):
    text=arg.extract_plain_text().strip()
    app_id = Config.get_config("traditional2simplified", "APPID")
    app_secret = Config.get_config("traditional2simplified", "APPSECRET")
    if not app_id:
        msg='未配置app_id, 请前往https://www.mxnzp.com/获取'
        logger.error(msg)
        await convert.send(msg)
        return
    elif not app_secret:
        msg='未配置app_secret, 请前往https://www.mxnzp.com/获取'
        logger.error(msg)
        await convert.send(msg)
        return
    try:
        rs = requests.get(f'https://www.mxnzp.com/api/convert/zh?content={text}&type=2&app_id={app_id}&app_secret={app_secret}')
        rs_obj = json.loads(rs.text)
        msg=rs_obj["data"]["convertContent"]
        await convert.send(msg)
    except Exception as e:
        msg=f'转换出错{type(e)}：{e}'
        logger.error(msg)
        await convert.send(msg)
   

