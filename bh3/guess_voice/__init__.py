import json, os, random, re, zipfile, traceback
from nonebot import on_command
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import MessageSegment, MessageEvent, Message, GroupMessageEvent, GROUP
from nonebot.params import CommandArg
from nonebot_plugin_htmlrender import text_to_pic
from services.log import logger
from utils.http_utils import AsyncHttpx
from nonebot.exception import FinishedException
from .game import GameSession

__zx_plugin_name__ = "崩坏三猜语音"
__plugin_usage__ = """
usage：
    崩坏三猜语音
    指令：
        崩坏三猜语音：正常舰桥、战斗等语音
        崩坏三猜语音2/困难：简短的语气或拟声词
        崩坏三猜语音答案
        崩坏三语音[name]：随机发送指定女武神一段语音
        崩坏三语音列表[name]：查看指定女武神所有语音
        崩坏三语音[name][id]：发送指定女武神的指定语音
    
    帮助崩坏三猜语音-super 获取超级用户帮助
""".strip()
__plugin_superuser_usage__ = """
usage：
    崩坏三猜语音[超级用户功能]
    指令：
        崩坏三语音新增答案[标准答案]:[答案别称] 猜语音答案时如果发现正确的女武神名称未能匹配答案时可以使用。如崩坏三语音新增答案丽塔(标准答案):缭乱星棘(别称)
        更新崩坏三语音列表 更新检索asset/record下语音列表
        下载崩坏三语音 仅支持全量语音下载，如需增量语音，请前往原作者视频处获取。
    
    record文件结构：
        无论是将完全解压后的文件夹原样放到assets/record还是把子文件夹甚至语音文件直接丢进去都是可以识别的
        结构没有特殊要求，只要放到assets/record文件夹里即可

    声明：
        崩坏三语音素材来自于[@YSJS有所建树](https://space.bilibili.com/402667766)的B站视频：[B站首个《崩坏3》常用角色语音素材库公布！可供下载使用。](https://www.bilibili.com/video/BV16J41157du)
        本仓库素材仅供真寻崩坏三插件使用，不提供解压密码，不收费；禁止商用！
        如需使用资源，请前往原作者视频处自行免费下载。   
""".strip()
__plugin_des__ = "崩坏三猜语音"
__plugin_cmd__ = ["崩坏三猜语音", "崩坏三猜语音答案", "崩坏三语音", "崩坏三语音新增答案 [_superuser]", "更新崩坏三语音列表 [_superuser]", "下载崩坏三语音 [_superuser]"]
__plugin_type__ = ("崩坏三相关",)
__plugin_version__ = 0.2
__plugin_author__ = "mobius"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["崩坏三猜语音", "崩三猜语音", "崩3猜语音", "崩坏3猜语音"],
}


guess = on_command("崩坏三猜语音", aliases={"崩三猜语音", "崩3猜语音", "崩坏3猜语音", "猜语音"}, priority=5, permission=GROUP, block=True)
answer = on_command("崩坏三猜语音答案", aliases={"崩三猜语音答案", "崩3猜语音答案", "崩坏3猜语音答案", "猜语音答案"}, priority=6, permission=GROUP, block=True)
getVoice = on_command("崩坏三语音", aliases={"崩三语音", "崩3语音", "崩坏3语音"}, priority=6, permission=GROUP, block=True)
addAnswer = on_command("崩坏三语音新增答案", aliases={"崩三语音新增答案", "崩3语音新增答案", "崩坏3语音新增答案"}, priority=5, permission=SUPERUSER, block=True)
undateVoice = on_command("更新崩坏三语音列表", aliases={"更新崩三语音列表", "更新崩3语音列表", "更新崩坏3语音列表"}, priority=5, permission=SUPERUSER, block=True)
downloadRecord = on_command("下载崩坏三语音", aliases={"下载崩三语音", "下载崩3语音", "下载崩坏3语音"}, priority=5, permission=SUPERUSER, block=True)

def split_voice_by_chara(v_list: list):
    """对语音列表进行分类"""
    ret = {
        "normal": {},  # 正常语音
        "hard": {}   # 语气&拟声词
    }
    for voice in v_list:
        op_dict = ret["hard"] if "拟声词" in voice["voice_path"] else ret["normal"]
        chara = re.split("-|\(", voice["voice_name"])[0].strip()
        if re.search(r"《|【", chara):
            continue
        if not op_dict.get(chara):
            op_dict[chara] = []
        op_dict[chara].append(voice)
    return ret


def gen_voice_list(origin_path=None):
    """递归生成语音列表"""
    voice_dir = os.path.join(os.path.dirname(__file__), "../assets/record")
    if origin_path is None:
        origin_path = voice_dir
    ret_list = []
    for item in os.listdir(origin_path):
        item_path = os.path.join(origin_path, item)
        if os.path.isdir(item_path):
            ret_list.extend(gen_voice_list(item_path))
        elif item.endswith("mp3"):
            voice_path = os.path.relpath(item_path, voice_dir)
            ret_list.append({"voice_name": item, "voice_path": voice_path})
        else:
            continue
    return ret_list

#崩坏三猜语音
@guess.handle()
async def guess_voice(event: GroupMessageEvent, arg: Message = CommandArg()):
    msg = arg.extract_plain_text().strip()
    #判断难度
    if re.search(r"2|困难", msg):
        difficulty = "hard"
    else:
        difficulty = "normal"
    game = GameSession(event.group_id)
    ret = await game.start(difficulty=difficulty)
    await guess.send(ret)

#崩坏三猜语音答案
@answer.handle()
async def check_answer(event: GroupMessageEvent, arg: Message = CommandArg()):
    game = GameSession(event.group_id)
    #游戏未开始返回
    if not game.is_start:
        return
    msg = arg.extract_plain_text().strip()
    #回答是双人时进行符号替换
    msg = msg.lower().replace(",", "和").replace("，", "和")
    await game.check_answer(msg, event.user_id)

#崩坏三语音
@getVoice.handle()
async def send_voice(event: GroupMessageEvent, arg: Message = CommandArg()):
    msg = arg.extract_plain_text().strip()
    a_list = GameSession.__load__("answer.json")
    assert isinstance(a_list, dict)
    listCmd=re.compile(r"^列表")#命令头
    idCmd = re.compile(r"\d+$")#(语音id)
    #命令包含列表
    if listCmd.search(msg):
        #获取要查询的女武神名
        msg=listCmd.sub('', msg)  
        for k, v in a_list.items():
            #获取女武神答案对应标准名称
            if msg in v:
                try:
                    #获取名称对应的所有语音（普通难度）
                    v_list = GameSession.__load__()["normal"][k]
                except KeyError:
                    await getVoice.finish(f"语音列表未生成或有错误，请先发送‘更新崩坏三语音列表’来更新")
                text=""
                #遍历语音名称
                for i in range(len(v_list)):
                    text+=f'{i}   {(v_list[i]["voice_name"])[:-4]}\n'
                #生成图片返回
                pic = await text_to_pic(text=text)
                await getVoice.finish(MessageSegment.image(pic))
        await getVoice.send(f"没找到【{msg}】的语音，请检查输入。", at_sender=True)
    #发送指定id的语音
    elif idCmd.search(msg):
        id=idCmd.search(msg)
        #去除id，获得女武神名称
        name=idCmd.sub('', msg)
        for k, v in a_list.items():
            #获取女武神答案对应标准名称
            if name in v:
                try:
                    #获取名称对应的所有语音（普通难度）
                    v_list = GameSession.__load__()["normal"][k]
                    #获取对应id语音
                    voice = v_list[int(id.group())]
                except KeyError:
                    await getVoice.finish(f"语音列表未生成或有错误，请先发送‘更新崩坏三语音列表’来更新")                
                #发送语音
                voice_path = f"file:///{os.path.join(os.path.dirname(os.path.dirname(__file__)),'assets/record',voice['voice_path'])}"
                await getVoice.finish(MessageSegment.record(voice_path))
        await getVoice.finish(f"没找到【{msg}】的语音，请检查输入。", at_sender=True)
    #指定女武神随机语音
    else:
        for k, v in a_list.items():
            #获取女武神答案对应标准名称
            if msg in v:
                try:
                    #获取名称对应的所有语音（普通难度）
                    v_list = GameSession.__load__()["normal"][k]
                except KeyError:
                    await getVoice.finish(f"语音列表未生成或有错误，请先发送‘更新崩坏三语音列表’来更新")
                #获取随机语音并发送
                voice = random.choice(v_list)
                voice_path = f"file:///{os.path.join(os.path.dirname(os.path.dirname(__file__)),'assets/record',voice['voice_path'])}"
                await getVoice.finish(MessageSegment.record(voice_path))
        await getVoice.send(f"没找到【{msg}】的语音，请检查输入。", at_sender=True)

#崩坏三语音新增答案
@addAnswer.handle()
async def add_answer(event: MessageEvent, arg: Message = CommandArg()):
    msg=arg.extract_plain_text().strip()
    if not msg:
        await addAnswer.finish(f"未输入答案", at_sender=True)
    msgArr=msg.replace("：", ":").split(":")
    #答案格式判断
    if len(msgArr) != 2:
        await addAnswer.finish(f"答案有误，输入参考：崩坏三语音新增答案丽塔(标准答案):缭乱星棘(别称)", at_sender=True)
    origin = msgArr[0].strip()
    new = msgArr[1].strip()
    data = GameSession.__load__("answer.json")
    if origin not in data:
        await addAnswer.finish(f"{origin}不存在。")
    if new in data[origin]:
        await addAnswer.finish(f"答案已存在。")
    #新增答案
    data[origin].append(new)
    #保存答案
    with open(
        os.path.join(os.path.dirname(__file__), "answer.json"), "w", encoding="utf8"
    ) as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    await addAnswer.finish("添加完成。")

#更新崩坏三语音列表
@undateVoice.handle()
async def update_voice_list():
    data = gen_voice_list()
    data_dict = split_voice_by_chara(data)
    with open(
        os.path.join(os.path.dirname(__file__), "record.json"), "w", encoding="utf8"
    ) as f:
        json.dump(data_dict, f, indent=4, ensure_ascii=False)
    num_normal = sum(len(data_dict["normal"][v]) for v in data_dict["normal"])
    num_hard = sum(len(data_dict["hard"][v]) for v in data_dict["hard"])
    await undateVoice.finish(f"崩坏3语音列表更新完成，当前共有语音{num_hard+num_normal}条，其中普通{num_normal}条，困难{num_hard}条")

#下载链接
record_url = "https://gitee.com/mobiusT/zhenxun_extensive_plugin_mobius_resource/raw/main/record.zip"
record_url = "https://ghproxy.com/https://github.com/MobiusT/zhenxun_extensive_plugin_mobius_resource/raw/main/record.zip"
"""
崩坏三语音素材来自于[@YSJS有所建树](https://space.bilibili.com/402667766)的B站视频：[B站首个《崩坏3》常用角色语音素材库公布！可供下载使用。](https://www.bilibili.com/video/BV16J41157du)

本仓库素材仅供真寻崩坏三插件使用，不提供解压密码，不收费；禁止商用！
如需使用资源，请前往原作者视频处自行免费下载。

【关于文件加密措施再次升级的告知】
前段时间我们多次在第三方的素材网上发现了本文件，并被标上了几元到几十元不等的售价。这点让我们很气愤，这些素材是提供给同人创作者进行创作的文件，免费提供给你们使用，有些人却来我这里“进货”，将我们辛辛苦苦收集提取的素材用于倒卖、销售。你们知道吗？这份素材的原始版权依然是米哈游的，你们倒卖的行为已经涉及到了商业，如果米哈游开始追究，倒卖者和发布者都有相关的责任。为了不必要的麻烦，我们从4.2版本的素材包开始将升级加密机制，将通过算法获取一串随机数以提高素材的获取门槛。或许会麻烦了点，但是我相信，如果是真爱的人这点麻烦是无所谓的。因为麻烦，多多少少也能拦住一些“进货商”。希望这能有效吧。

【2022年3月10日新增告知】
近期发现有人将本文件搬运至其他平台抹去了所有外包中的作者信息，声称是当事人“本人收集”并开通付费获取的业务，目前经过交涉已将此事处理完毕。为防此类事件再次发生，从5.6版本的素材包起将在不影响使用的前提下对包内部分文件进行防盗处理，以此判定是否为*换皮包*。如果您在其他平台发现有人提供与本包类似的文件，请在群内私信UP主告知并发送样本，经确认后我们将对违规搬运的用户进行处理，感谢您的理解。（“*换皮包*”定义详见下文）

{“*换皮包*”是指下载该文件的用户解压后删除了所有原作者保留的声明信息，并自行打包后转手再次供应给他人的行为，目的可能是为了给自己引流或盈利，具体行为包括但不限于：将本文件删除声明信息后搬运至其他平台或群聊，将本文件删除声明信息后发布至各类网盘，将本文件删除声明信息后设置如“点赞”“关注”“转发”“拉人”等引流行为后获取的规则等……}

总结：
1.文件只能用于同人创作，不能商用！
2.文件只能下载者使用，不要随便发给不认识的人，如需发送，请发送全文件。【包括外包的相关说明和主文件包】
3.绝对严禁标价出售或者提供给用于商业的平台！【如付费下载的语音包服务，会员制的素材网等】
4.请规范转载！如发现换皮转手后导致违规的，将由违规者自行承担一切后果！
■请认真阅读后再获取解压码，如违规使用产生的一切后果由违规者自行承担！■

"""
record_pwd = "BV16J41157du"
#下载崩坏三语音列表
@downloadRecord.handle()
async def _():
    #下载目录
    file_path=os.path.join(os.path.dirname(__file__), "../assets/record/")
    # 创建插件目录
    if not os.path.exists(file_path):
        os.makedirs(file_path)
        # 设置权限755
        os.chmod(file_path, 0o0755)
        logger.info(f"创建插件目录{file_path}")
    #下载文件名
    zipfile_name=os.path.join(file_path, "record.zip")
    # 删除旧文件
    if os.path.exists(zipfile_name):
        os.unlink(zipfile_name)
        logger.info(f"删除旧文件{zipfile_name}")
    data=None
    try:   
        #下载压缩包    
        data=await AsyncHttpx.get(record_url)
        #写压缩包
        with open(zipfile_name,'wb') as f:
            f.write(data.read())
        #解压压缩包
        try:
            with zipfile.ZipFile(zipfile_name, 'r') as f:
                f.extractall(file_path, pwd=record_pwd.encode("utf-8"))
        except Exception as e:
            msg = f"解压{zipfile_name}失败，请手动处理：\n{e}"
            logger.error(f'{msg}\n{traceback.format_exc()}')
            await downloadRecord.finish(msg)
        #检查解压文件夹
        unzip_folder=os.path.join(file_path, "record")
        if not os.path.exists(unzip_folder):
            msg = f"下载资源失败，解压{zipfile_name}文件后未能发现文件夹{unzip_folder}"
            logger.error(msg)
            await downloadRecord.finish(msg)
        #删除压缩包
        try:
            os.unlink(zipfile_name)
        except Exception as e:
            msg = f"删除压缩包{zipfile_name}失败，请手动处理：\n{e}\n{traceback.format_exc()}"
            logger.warning(msg)
        #更新语音列表
        await update_voice_list()
        await downloadRecord.finish(f"下载语音资源成功")
    except FinishedException:
        return
    except Exception as e:       
        msg = f"下载语音资源失败：\n{e}\n{traceback.format_exc()}"
        logger.error(f'{msg}\n{traceback.format_exc()}')
        await downloadRecord.finish(msg)

if __name__ == "__main__":
    data = gen_voice_list()
    with open(
        os.path.join(os.path.dirname(__file__), "record.json"), "w", encoding="utf8"
    ) as f:
        json.dump(split_voice_by_chara(data), f, indent=4, ensure_ascii=False)
