'''
Author: MobiusT
Date: 2022-12-23 21:09:31
LastEditors: MobiusT
LastEditTime: 2022-12-31 12:48:31
'''
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message, MessageSegment, GroupMessageEvent
from services.log import logger
from models.group_member_info import GroupInfoUser
from nonebot.params import CommandArg
from configs.config import Config
from utils.message_builder import image
from ..modules.database import DB
from ..modules.image_handle import DrawIndex
from ..modules.query import InfoError, GetInfo
from ..modules.util import ItemTrans
from nonebot_plugin_htmlrender import html_to_pic
from datetime import datetime, timedelta
import time, os, re


__zx_plugin_name__ = "崩坏三排行"
__plugin_usage__ = """
usage：
    获取群内上一期终极区战场/深渊排行信息
    指令：
        崩坏三战场排行
        崩坏三深渊排行
        崩坏三战场排行更新
        崩坏三深渊排行更新
        
""".strip()
__plugin_des__ = "获取群内上一期终极区战场/深渊排行信息"
__plugin_cmd__ = ["崩坏三战场排行", "崩坏三深渊排行"]
__plugin_type__ = ("崩坏三相关",)
__plugin_version__ = 0.1
__plugin_author__ = "mobius"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["崩坏三排行", "崩三排行", "崩3排行", "崩坏3排行"],
}
__plugin_block_limit__ = {
    "rst": "[at]你正在查询崩三排行！"
}
__plugin_cd_limit__ = {
    "cd": 30,
    "rst": "[at]你刚查过崩三排行，别查了！"
}
battle_field = on_command(
    "崩坏三战场排行", aliases={"崩三战场排行", "崩3战场排行", "崩坏3战场排行", "战场排行"}, priority=5, block=True
)
battle_field_update = on_command(
    "崩坏三战场排行更新", aliases={"崩三战场排行更新", "崩3战场排行更新", "崩坏3战场排行更新", "战场排行更新", "崩三战场更新", "崩3战场更新", "崩坏3战场更新", "战场更新"}, priority=5, block=True
)

#崩坏三战场排行
@battle_field.handle()
async def _(event: GroupMessageEvent, arg: Message = CommandArg()):
    #读取配置文件
    cookie = Config.get_config("bind_bh3", "COOKIE")
    if not cookie:
        await battle_field.send("需要真寻主人在config.yaml中配置cookie才能使用该功能")
        return   
    #获取群号 
    group_id = event.group_id
    #获取战场排行    
    image_path = os.path.join(os.path.dirname(__file__), f'image/war_{group_id}_{this_monday()}.png')
    if not os.path.exists(image_path):
        await battle_field.send(f'正在更新崩坏三战场排行,耗时较久请耐心等待')  
        await getData(group_id)
    await battle_field.finish(image(image_path))

#崩坏三战场排行更新
battle_field_update.handle()
async def _(event: GroupMessageEvent, arg: Message = CommandArg()):
    #读取配置文件
    cookie = Config.get_config("bind_bh3", "COOKIE")
    if not cookie:
        await battle_field_update.send("需要真寻主人在config.yaml中配置cookie才能使用该功能")
        return
    #获取群号
    group_id = event.group_id
    #删除战场排行 
    image_path = os.path.join(os.path.dirname(__file__), f'image/war_{group_id}_{this_monday()}.png')
    if os.path.exists(image_path):
        try:
            os.unlink(image_path)
        except Exception as e:
            logger.error(f'更新崩坏三战场排行失败,请联系真寻管理员手动处理：{e}')
            await battle_field_update.finish(f'更新崩坏三战场排行失败,请联系真寻管理员手动处理：{e}')
    await battle_field_update.send(f'正在更新崩坏三战场排行,耗时较久请耐心等待')        
    await getData(group_id)
    await battle_field_update.finish(f'崩坏三战场排行已更新，请使用命令 崩坏三战场排行 查看') 

async def getData(group_id: str):      
    qqList = await GroupInfoUser.get_group_member_id_list(group_id)
    region_db = DB("uid.sqlite", tablename="uid_region")
    qid_db = DB("uid.sqlite", tablename="qid_uid")
    #排行榜
    rank=[]
    #崩三账号去重用
    roleIdMap={}
    for qid in qqList:
        try:#获取绑定的角色信息
            role_id = qid_db.get_uid_by_qid(qid)
            region_id = region_db.get_region(role_id)
            role_id = role_id if isinstance(role_id, str) else role_id.group()
            #去重
            if role_id in roleIdMap:
                logger.info(f"群{group_id}成员{qid}所绑定的角色{role_id}重复出现，跳过统计")
                continue
            roleIdMap[role_id]=1
        except KeyError:
            logger.debug(f"群{group_id}成员{qid}未绑定角色")
            continue
        #查询角色
        spider = GetInfo(server_id=region_id, role_id=role_id)
        try:
            ind = await spider.part()
            ind = DrawIndex(**ind)            
        except InfoError as e:
            continue
        #跳过非终级区
        if 4 != ind.index.stats.battle_field_area:
            logger.info(f"群{group_id}成员{qid}非终级区")
            continue
        bfr = ind.battleFieldReport.reports[0]
        #跳过非上周结算
        if str(this_monday())!=str(bfr.time_second.astimezone().date()):
            logger.info(f"群{group_id}成员{qid}上周未打战场")
            continue
        #跳过没全打boss
        if len(bfr.battle_infos)<3:
            logger.info(f"群{group_id}成员{qid}上周未打完全部战场")
            continue
        #boss排序
        (bfr.battle_infos).sort(key=lambda x: x.boss.id)  
        rank.append(ind)
        time.sleep(1)

    #总分
    rank.sort(key=lambda x: x.battleFieldReport.reports[0].score, reverse=True)
    #总模板数据
    paraTotal={}
    #结算时间
    paraTotal["time_second"]=rank[0].battleFieldReport.reports[0].time_second.astimezone().date()
    paraTotal["font"]="""
    @font-face {
	        font-family: HYWenHei-85W;
	        src: url("../assets/font/HYWenHei-85W.ttf");
        }    
		@font-face {
	        font-family: HYWenHei-65W;
	        src: url("../assets/font/HYWenHei-65W.ttf");
        }     
		@font-face {
	        font-family: HYLingXinTiJ;
	        src: url("../assets/font/HYLingXinTiJ.ttf");
        }  
    """
    #boss名称
    for i in range(1,4):
        paraTotal[f"bossName{i}"] = rank[0].battleFieldReport.reports[0].battle_infos[i-1].boss.name
    #总分
    templateRankTotal = open(os.path.join(os.path.dirname(__file__), "template_tank_total.html"), "r", encoding="utf8").read()
    rankNo=1
    finalRankTotal=""
    for i in rank:  
        para={}
        para["rank"] = rankNo
        rankNo += 1
        avatar_url = i.index.role.AvatarUrl
        a_url = ""
        try:
            no = re.search(r"\d{3,}", avatar_url).group()
            a_url = avatar_url.split(no)[0] + no + ".png"
        except:
            try:
                no = re.search(r"[a-zA-Z]{1,}\d{2}", avatar_url).group()
                a_url = avatar_url.split(no)[0] + no + ".png"
            except:
                a_url = "https://upload-bbs.mihoyo.com/game_record/honkai3rd/all/SpriteOutput/AvatarIcon/705.png"
        para["AvatarUrl"]=a_url
        para["nickname"]=i.index.role.nickname
        para["score"]=i.battleFieldReport.reports[0].score
        finalRankTotal += templateRankTotal.format(**para)
    paraTotal["rankTotal"] = finalRankTotal

    #第一个boss
    templateRankBoss = open(os.path.join(os.path.dirname(__file__), "template_rank_boss.html"), "r", encoding="utf8").read()
    for n in range(3):
        finalRankBoss=""
        rank.sort(key=lambda x: x.battleFieldReport.reports[0].battle_infos[n].score, reverse=True)
        logger.debug(f"\n按{rank[0].battleFieldReport.reports[0].battle_infos[n].boss.name}排序")
        for i in rank:
            para={}
            para["nickname"]=i.index.role.nickname
            para["server"]=ItemTrans.id2server(i.index.role.region)
            para["score"]=i.battleFieldReport.reports[0].battle_infos[n].score
            para["star1"]=["b", "a", "s", "ss", "sss"][i.battleFieldReport.reports[0].battle_infos[n].lineup[0].star - 1]
            para["star2"]=["b", "a", "s", "ss", "sss"][i.battleFieldReport.reports[0].battle_infos[n].lineup[1].star - 1]
            para["star3"]=["b", "a", "s", "ss", "sss"][i.battleFieldReport.reports[0].battle_infos[n].lineup[2].star - 1]
            para["star4"]=[1, 2, 2, 3, 3, 3, 4][i.battleFieldReport.reports[0].battle_infos[n].elf.star - 1]
            para["bg1"]=i.battleFieldReport.reports[0].battle_infos[n].lineup[0].avatar_background_path
            para["bg2"]=i.battleFieldReport.reports[0].battle_infos[n].lineup[1].avatar_background_path
            para["bg3"]=i.battleFieldReport.reports[0].battle_infos[n].lineup[2].avatar_background_path 
            para["icon1"]=i.battleFieldReport.reports[0].battle_infos[n].lineup[0].icon_path
            para["icon2"]=i.battleFieldReport.reports[0].battle_infos[n].lineup[1].icon_path
            para["icon3"]=i.battleFieldReport.reports[0].battle_infos[n].lineup[2].icon_path     
            para["elf"]=i.battleFieldReport.reports[0].battle_infos[n].elf.avatar
            para["boss"]=i.battleFieldReport.reports[0].battle_infos[n].boss.avatar
            finalRankBoss += templateRankBoss.format(**para)
        paraTotal[f"rankBoss{n+1}"] = finalRankBoss

    #汇总
    template = open(os.path.join(os.path.dirname(__file__), "template.html"), "r", encoding="utf8").read()
    html=template.format(**paraTotal)
    pic = await html_to_pic(html=html, wait=5, template_path= f"file://{os.path.dirname(__file__)}", no_viewport=True)
    #写文件
    with open(os.path.join(os.path.dirname(__file__), f'image/war_{group_id}_{paraTotal["time_second"]}.png'), "ab") as f:
        f.write(pic)



def this_monday(today = datetime.now()):
    return datetime.strftime(today - timedelta(today.weekday()), "%Y-%m-%d")