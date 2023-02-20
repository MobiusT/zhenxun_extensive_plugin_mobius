import re

from services.log import logger
from tortoise import fields
from services.db_context import Model
from datetime import datetime
from typing import Optional, List


class GitHubSub(Model):
    class Meta:
        table = "github_sub"

    id = fields.IntField(pk=True, generated=True, auto_increment=True) # 自增id
    sub_type = fields.CharField(max_length=255, null =False)
    # 订阅用户
    sub_users = fields.CharField(max_length=255, null =False)
    # 地址
    sub_url = fields.CharField(max_length=255, null = True)
    update_time = fields.DatetimeField(null = True)
    # etag
    etag = fields.CharField(max_length=255, null = True)

    @classmethod
    async def add_github_sub(
            cls,
            sub_type: str,
            sub_user: str,
            *,
            sub_url: Optional[str] = None,
    ) -> bool:
        """
        说明：
            添加订阅
        参数：
            :param sub_type: 订阅类型
            :param sub_user: 订阅此条目的用户
            :param sub_url: 订阅地址
        """
        try:
            sub_user = sub_user if sub_user[-1] == "," else f"{sub_user},"
            if query := await cls.get_or_none(sub_url = sub_url):
                if sub_user not in query.sub_users:
                        query.sub_users = query.sub_users + sub_user                        
                        await query.save(update_fields=["sub_users", ])
            else:
                print(sub_url)
                print(sub_type)
                print(sub_user)
                sub = await cls.create(
                        sub_url=sub_url, sub_type=sub_type, sub_users=sub_user
                    )
                sub.sub_url=sub_url if sub_url else sub.sub_url
                sub.update_time=datetime.now().replace(microsecond=0)
                await sub.save(update_fields=["sub_url", "update_time", ])
            return True
        except Exception as e:
            logger.info(f"github_sub 添加订阅错误 {type(e)}: {e}")
        return False

    @classmethod
    async def delete_github_sub(cls, sub_url: str, sub_user: str) -> bool:
        """
        说明：
            删除订阅
        参数：
            :param sub_url: 订阅地址
            :param sub_user: 删除此条目的用户
        """
        try:
            query = await cls.get_or_none(sub_url = sub_url,sub_users__contains=sub_user)
            if not query:
                return False
            strinfo = re.compile(f"\d*:{sub_user},")
            query.sub_users = strinfo.sub('', query.sub_users)
            await query.save(update_fields=["sub_users", ])
            if not query.sub_users.strip():
                await query.delete()
            return True
        except Exception as e:
            logger.info(f"github_sub 删除订阅错误 {type(e)}: {e}")
        return False

    @classmethod
    async def get_sub(cls, sub_url: str) -> Optional["GitHubSub"]:
        """
        说明：
            获取订阅对象
        参数：
            :param sub_url: 订阅地址
        """
        return await cls.filter(sub_url = sub_url).first()

    @classmethod
    async def get_sub_data(cls, id_: str) -> List["GitHubSub"]:
        """
        获取 id_ 订阅的所有内容
        :param id_: id
        """
        query = cls.filter(sub_users__contains=id_)
        return await query.all()

    @classmethod
    async def update_sub_info(
            cls,
            sub_url: Optional[str] = None,
            *,
            update_time: Optional[datetime] = None,
            etag: Optional[str] = None,
    ) -> bool:
        """
        说明：
            更新订阅信息
        参数：
            :param sub_url: 订阅地址
            :update_time: 更新时间
            :etag: 更新标签
        """
        try:
            sub = await cls.filter(sub_url == sub_url).first()
            if sub:
                sub.update_time=update_time if update_time is not None else sub.update_time
                sub.etag = etag if etag is not None else sub.etag
                sub.save(update_fields=["sub_url", "update_time", ])
                return True
        except Exception as e:
            logger.info(f"github_sub 更新订阅错误 {type(e)}: {e}")
        return False

    @classmethod
    async def get_all_sub_data(
            cls,
    ) -> "List[GitHubSub], List[GitHubSub], List[GitHubSub]":
        """
        说明：
            分类获取所有数据
        """
        user_data = []
        repository_data = []
        query = await cls.all()
        for x in query:
            if x.sub_type == "user":
                user_data.append(x)
            if x.sub_type == "repository":
                repository_data.append(x)
        return user_data, repository_data
