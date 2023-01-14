'''
Author: MobiusT
Date: 2023-01-14 19:08:36
LastEditors: MobiusT
LastEditTime: 2023-01-14 19:10:52
'''
import nonebot, logging
from pathlib import Path

logging.basicConfig()
logging.getLogger("sqlitedict.SqliteMultithread").setLevel(logging.ERROR)
nonebot.load_plugins(str(Path(__file__).parent.resolve()))
