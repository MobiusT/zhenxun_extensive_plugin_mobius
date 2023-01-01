import nonebot, logging

logging.basicConfig()
logging.getLogger("sqlitedict.SqliteMultithread").setLevel(logging.ERROR) 
nonebot.load_plugins("zhenxun_extensive_plugin_mobius/bh3")

