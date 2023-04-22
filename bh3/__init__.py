from pathlib import Path

import logging
import nonebot

logging.basicConfig()
logging.getLogger("sqlitedict.SqliteMultithread").setLevel(logging.ERROR)
nonebot.load_plugins(str(Path(__file__).parent.resolve()))
