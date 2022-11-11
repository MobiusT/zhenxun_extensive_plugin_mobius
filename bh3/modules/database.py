import json
import os
from pathlib import Path
from typing import Optional

from sqlitedict import SqliteDict


class DB(SqliteDict):
    cache_dir = Path(os.path.dirname(os.path.abspath(__file__))) / "data"

    def __init__(
        self,
        filename=None,
        tablename="unnamed",
        flag="c",
        autocommit=True,
        journal_mode="DELETE",
        encode=json.dumps,
        decode=json.loads,
    ) -> None:
        if not self.cache_dir.exists():
            self.cache_dir.mkdir(exist_ok=True, parents=True)
        filename = self.cache_dir / filename
        super().__init__(
            filename=filename,
            tablename=tablename,
            flag=flag,
            autocommit=autocommit,
            journal_mode=journal_mode,
            encode=encode,
            decode=decode,
        )

    def set_region(self, role_id: str, region: str) -> None:
        data = self.get(role_id, {})
        data.update({"region": region})
        self[role_id] = data

    def get_region(self, role_id: str) -> Optional[str]:
        if self.get(role_id):
            return self[role_id]["region"]
        else:
            return None

    def get_uid_by_qid(self, qid: str) -> str:
        """获取上次查询的uid"""
        return self[qid]["role_id"]

    def set_uid_by_qid(self, qid: str, uid: str) -> None:
        data = self.get(qid, {})
        data.update({"role_id": uid})
        self[qid] = data

    def get_cookie(self, qid: str) -> Optional[str]:
        try:
            return self[qid]["cookie"]
        except KeyError:
            return None

    def set_cookie(self, qid: str, cookie: str) -> None:
        data = self.get(qid, {})
        data.update({"cookie": cookie})
        self[qid] = data
