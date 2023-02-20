from .model import GitHubSub
from configs.config import Config
from typing import Optional
from datetime import datetime, timedelta
from services.log import logger
from utils.http_utils import AsyncHttpx
import random


async def get_github_api(sub_type, sub_url, etag=None, token=None):
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers['Authorization'] = 'token %s' % token
    elif etag:
        headers['if-none-match'] = '{}'.format(etag)
    if sub_type == "user":
        user_url_sub = "https://api.github.com/users/{}/events".format(sub_url)
        return await AsyncHttpx.get(user_url_sub, headers=headers, timeout=5)
    else:
        repository_url_sub = "https://api.github.com/repos/{}/events".format(sub_url)
        return await AsyncHttpx.get(repository_url_sub, headers=headers, timeout=5)


async def add_user_sub(sub_type: str, sub_url: str, sub_user: str) -> str:
    """
    添加用户订阅
    :param sub_type:订阅类型
    :param sub_url:订阅地址
    :param sub_user: 订阅用户 id # 7384933:private or 7384933:2342344(group)
    :return:
    """

    if sub_type == "repository":
        sub_url.replace("\\", "/")
        if "/" in sub_url:
            sub_url_list = sub_url.split('/')
            if len(sub_url_list) != 2:
                return f"订阅参数错误，格式为：owner/repo"
        else:
            return f"订阅参数错误，格式为：owner/repo"
    try:
        response = await get_github_api(sub_type, sub_url)
        if response.status_code == 403:
            return f"你无权访问该仓库{sub_url}"
        elif response.status_code == 404:
            return f"用户{sub_url}不存在！请重新发送或取消"
    except:
        return f"请求超时"
    try:
        if await GitHubSub.add_github_sub(
                sub_type,
                sub_user,
                sub_url=sub_url):
            user = (await GitHubSub.get_sub(sub_url)).sub_url
            return f"已成功订阅{user}"
        else:
            return "添加订阅失败..."
    except Exception as e:
        logger.error(f"订阅用户：{user} 发生了错误 {type(e)}：{e}")
    return "添加订阅失败..."


async def get_sub_status(sub_type: str, sub_url: str, etag=None):
    """
    获取订阅状态
    :param sub_type: 订阅类型
    :param sub_url: 订阅地址
    :param etag: 检测标签
    """
    try:
        token = Config.get_config("github_sub", "GITHUB_TOKEN")
        response = await get_github_api(sub_type, sub_url, etag, token)
    except:
        return None
    if response.status_code == 304:
        return None
    elif response.status_code == 200:
        sub = await GitHubSub.get_sub(sub_url)
        old_time = sub.update_time
        json_response = response.json()
        if not token:
            new_etag = response.headers['ETag']
            if etag == None or etag != str(new_etag):
                await GitHubSub.update_sub_info(sub_url, etag=str(new_etag))
        if isinstance(json_response, dict):
            if "message" in json_response.keys():
                if "API rate limit exceeded" in json_response["message"]:
                    logger.error("GitHub API 超出速率限制")
                    if not Config.get_config("github_sub", "GITHUB_TOKEN"):
                        logger.error("请设置 GitHub 用户名和 OAuth Token 以提高限制")
                elif json_response["message"] == "Not Found":
                    logger.error(f"无法找到{sub_url}")
        print(old_time)
        print(datetime.strptime(json_response[0]['created_at'], '%Y-%m-%dT%H:%M:%SZ') + timedelta(hours=8))
        json_response = [i for i in json_response if i['type'] != 'CreateEvent' and
                         old_time < datetime.strptime(i['created_at'], '%Y-%m-%dT%H:%M:%SZ') + timedelta(hours=8)]
        if json_response:
            event_time = datetime.strptime(json_response[0]['created_at'], '%Y-%m-%dT%H:%M:%SZ') + timedelta(hours=8)
            await GitHubSub.update_sub_info(sub_url, update_time=event_time)
            msg_list = []
            for newest_json in json_response:
                msg = generate_plain(newest_json)
                if msg:
                    if sub_type == "user":
                        star_str = "用户"
                    else:
                        star_str = "仓库"
                    msg = f"{star_str} : {sub_url}\n" + msg + f"----------\n获取时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    msg_list.append(msg)
            if len(msg_list) == 1:
                return msg_list[0]
            elif len(msg_list) >= 2:
                return msg_list

    return None


def generate_plain(event: dict):
    actor = event['actor']['display_login']
    event_time = (datetime.strptime(event['created_at'], '%Y-%m-%dT%H:%M:%SZ') + timedelta(hours=8)) \
        .strftime('%Y-%m-%d %H:%M:%S')
    resp = None
    if event['type'] == 'IssuesEvent':
        if Config.get_config("github_sub", "GITHUB_ISSUE"):
            return None
        if event['payload']['action'] == 'opened':
            title = event['payload']['issue']['title']
            number = event['payload']['issue']['number']
            body = event['payload']['issue']['body']
            if body:
                if len(body) > 100:
                    body = body[:100] + "......"
                body = body + "\n"
            link = event['payload']['issue']['html_url']
            resp = (f"----------\n"
                    f"[新 Issue]\n"
                    f"#{number} {title}\n"
                    f"{body}\n"
                    f"\n"
                    f"发布人：{actor}\n"
                    f"时间：{event_time}\n"
                    f"链接：{link}\n")
    elif event['type'] == 'IssueCommentEvent':
        if Config.get_config("github_sub", "GITHUB_ISSUE"):
            return None
        if event['payload']['action'] == 'created':
            title = event['payload']['issue']['title']
            number = event['payload']['issue']['number']
            body = event['payload']['comment']['body']
            if body:
                if len(body) > 100:
                    body = body[:100] + "......"
                body = body + "\n"
            link = event['payload']['comment']['html_url']
            resp = (f"----------\n"
                    f"[新 Comment]\n"
                    f"#{number} {title}\n"
                    f"{body}"
                    f"\n"
                    f"发布人：{actor}\n"
                    f"时间：{event_time}\n"
                    f"链接：{link}\n")
    elif event['type'] == 'PullRequestEvent':
        if event['payload']['action'] == 'opened':
            title = event['payload']['pull_request']['title']
            number = event['payload']['pull_request']['number']
            body = event['payload']['pull_request']['body']
            if body:
                if len(body) > 100:
                    body = body[:100] + "......"
                body = body + "\n"
            head = event['payload']['pull_request']['head']['label']
            base = event['payload']['pull_request']['base']['label']
            commits = event['payload']['pull_request']['commits']
            link = event['payload']['pull_request']['html_url']
            resp = (f"----------\n"
                    f"[新 PR]\n"
                    f"#{number} {title}\n"
                    f"{body}"
                    f"\n"
                    f"{head} → {base}\n"
                    f"提交数：{commits}\n"
                    f"发布人：{actor}\n"
                    f"时间：{event_time}\n"
                    f"链接：{link}\n")
    elif event['type'] == 'PushEvent':
        commits = []
        link = event['repo']['name']
        for commit in event['payload']['commits']:
            commits.append(f"· [{commit['author']['name']}] {commit['message']}")
        resp = (f"----------\n"
                f"[新 Push]\n"
                + "\n".join(commits) +
                f"\n"
                f"提交数：{len(commits)}\n"
                f"发布人：{actor}\n"
                f"时间：{event_time}\n"
                f"链接：https://github.com/{link}\n")
    elif event['type'] == 'CommitCommentEvent':
        body = event['payload']['comment']['body']
        if body:
            if len(body) > 100:
                body = body[:100] + "......"
            body = body + "\n"
        link = event['payload']['comment']['html_url']
        resp = (f"----------\n"
                f"[新 Comment]\n"
                f"{body}"
                f"\n"
                f"发布人：{actor}\n"
                f"时间：{event_time}\n"
                f"链接：{link}\n")

    elif event['type'] == 'ReleaseEvent':
        body = event['payload']['release']['body']
        if body:
            if len(body) > 200:
                body = body[:200] + "......"
            body = body + "\n"
        link = event['payload']['release']['html_url']
        name = event['payload']['release']['name']
        resp = (f"----------\n"
                f"[新 Release]\n"
                f"版本：{name}\n\n"
                f"{body}"
                f"\n"
                f"发布人：{actor}\n"
                f"时间：{event_time}\n"
                f"链接：{link}\n")
    return resp if resp else None


class SubManager:
    def __init__(self):
        self.user_data = []
        self.repository_data = []
        self.current_index = -1

    async def reload_sub_data(self):
        """
        重载数据
        """
        if not self.user_data or not self.repository_data:
            (
                _user_data,
                _repository_data,
            ) = await GitHubSub.get_all_sub_data()
            if not self.user_data:
                self.user_data = _user_data
            if not self.repository_data:
                self.repository_data = _repository_data

    async def random_sub_data(self) -> Optional[GitHubSub]:
        """
        随机获取一条数据
        :return:
        """
        sub = None
        if not self.user_data and not self.repository_data:
            return sub
        self.current_index += 1
        if self.current_index == 0:
            if self.user_data:
                sub = random.choice(self.user_data)
                self.user_data.remove(sub)
        elif self.current_index == 1:
            if self.repository_data:
                sub = random.choice(self.repository_data)
                self.repository_data.remove(sub)
        else:
            self.current_index = -1
        if sub:
            return sub
        await self.reload_sub_data()
        return await self.random_sub_data()
