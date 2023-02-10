'''
Author: MobiusT
Date: 2022-12-23 21:09:31
LastEditors: MobiusT
LastEditTime: 2023-02-10 21:33:16
'''
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message, MessageSegment, MessageEvent
from nonebot.params import CommandArg
from services.log import logger
from models.group_member_info import GroupInfoUser
from configs.config import Config
from utils.message_builder import image, custom_forward_msg
from utils.utils import get_bot, scheduler
from ..modules.database import DB
from ..modules.image_handle import DrawIndex
from ..modules.query import InfoError, GetInfo
from ..modules.util import ItemTrans
from nonebot_plugin_htmlrender import html_to_pic
from datetime import datetime, timedelta
import time, os, re, json


__zx_plugin_name__ = "崩坏三排行"
__plugin_usage__ = """
usage：
    获取群内上一期终极区战场/深渊排行信息
    指令：
        崩坏三战场排行
        崩坏三深渊排行[全部/all]
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
__plugin_configs__ = {
    "SHOWCOUNTALL": {
        "value": 10,         # 配置值
        "help": "崩三排行，战场总分排行展示数量",            # 配置项说明，为空时则不添加配置项说明注释
        "default_value": 10   # 当value值为空时返回的默认值   
    },
    "SHOWCOUNTBOSS": {
        "value": 5,         # 配置值
        "help": "崩三排行，战场每个boss排行展示数量",            # 配置项说明，为空时则不添加配置项说明注释
        "default_value": 5   # 当value值为空时返回的默认值   
    },
}

battle_field = on_command(
    "崩坏三战场排行", aliases={"崩三战场排行", "崩3战场排行", "崩坏3战场排行", "战场排行"}, priority=5, block=True
)
battle_field_update = on_command(
    "崩坏三战场排行更新", aliases={"崩三战场排行更新", "崩3战场排行更新", "崩坏3战场排行更新", "战场排行更新", "崩三战场更新", "崩3战场更新", "崩坏3战场更新", "战场更新"}, priority=6, block=True
)
abyss = on_command(
    "崩坏三深渊排行", aliases={"崩三深渊排行", "崩3深渊排行", "崩坏3深渊排行", "深渊排行"}, priority=5, block=True
)
abyss_update = on_command(
    "崩坏三深渊排行更新", aliases={"崩三深渊排行更新", "崩3深渊排行更新", "崩坏3深渊排行更新", "深渊排行更新", "崩三深渊更新", "崩3深渊更新", "崩坏3深渊更新", "深渊更新"}, priority=6, block=True
)

#排名记录json文件
RANK_JSON = os.path.join(os.path.dirname(__file__), "./rank.json")
REGION_LIST=["android01", "bb01", "hun01", "hun02", "pc01", "yyb01", "ios01"]

#崩坏三深渊排行
@abyss.handle()
async def _(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    #读取配置文件
    cookie = Config.get_config("bind_bh3", "COOKIE")
    if not cookie:
        await abyss.finish("需要真寻主人在config.yaml中配置cookie才能使用该功能")
    #获取群号 
    group_id = event.group_id
    #获取参数
    msg = arg.extract_plain_text().strip()
    if  msg in ["all", "全部"]:
        msgs=[]
        for r in REGION_LIST:
            image_path = os.path.join(os.path.dirname(__file__), f'image/abyss_{group_id}_{r}_{last_cutoff_day(is_abyss = True)}.png')
            if not os.path.exists(image_path):
                await abyss.send(f'正在更新崩坏三深渊排行,耗时较久请耐心等待')  
                await getAbyssData(group_id)
            msgs.append(image(image_path))
        await bot.send_group_forward_msg(group_id=event.group_id, messages=custom_forward_msg(msgs, bot.self_id))
        return
    qid_db = DB("uid.sqlite", tablename="qid_uid")
    region_db = DB("uid.sqlite", tablename="uid_region")
    try:#获取绑定的角色信息
        role_id = qid_db.get_uid_by_qid(str(event.user_id))
        region_id = region_db.get_region(role_id)
    except KeyError:
        await abyss.finish("请先绑定uid，\n例:崩坏三绑定114514官服")
    
    #获取深渊排行    
    image_path = os.path.join(os.path.dirname(__file__), f'image/abyss_{group_id}_{region_id}_{last_cutoff_day(is_abyss = True)}.png')
    if not os.path.exists(image_path):
        await abyss.send(f'正在更新崩坏三深渊排行,耗时较久请耐心等待')  
        await getAbyssData(group_id)
    await abyss.finish(image(image_path))

#崩坏三深渊排行更新
@abyss_update.handle()
async def _(event: GroupMessageEvent):
    #读取配置文件
    cookie = Config.get_config("bind_bh3", "COOKIE")
    if not cookie:
        await abyss_update.finish("需要真寻主人在config.yaml中配置cookie才能使用该功能")
    #获取群号
    group_id = event.group_id    
    await abyss_update.send(f'正在更新崩坏三深渊排行,耗时较久请耐心等待')        
    await getAbyssData(group_id)
    await abyss_update.finish(f'已更新崩坏三深渊排行，请使用命令 崩坏三深渊排行 或 崩坏三深渊排行全部 查看', at_sender=True ) 

@scheduler.scheduled_job(#定时任务，每周一、周四6时
    "cron",
    day_of_week="mon,thu",
    hour=6,
    minute=0,
)
async def _():
    try:
        bot = get_bot()
        gl = await bot.get_group_list()
        gl = [g["group_id"] for g in gl]
        for g in gl:
            await getAbyssData(g)
            logger.info(f"{g} 生成深渊排行成功")
            time.sleep(60)
    except Exception as e:
        logger.error(f"生成深渊排行错误 e:{e}")

async def getAbyssData(group_id: str):      
    # 删除深渊排行 
    for r in REGION_LIST:
        image_path = os.path.join(os.path.dirname(__file__), f'image/abyss_{group_id}_{r}_{last_cutoff_day(is_abyss = True)}.png')
        if os.path.exists(image_path):
            try:
                os.unlink(image_path)
            except Exception as e:
                logger.error(f'更新崩坏三深渊排行失败,请联系真寻管理员手动处理：{e}')

    qqList = await GroupInfoUser.get_group_member_id_list(group_id)
    region_db = DB("uid.sqlite", tablename="uid_region")
    qid_db = DB("uid.sqlite", tablename="qid_uid")
    #排行榜
    rank={}
    for r in REGION_LIST:
        rank[r]=[]
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
        if ind.index.stats.new_abyss is None:
            logger.info(f"群{group_id}成员{qid}非终级区")
            continue
        abyss = ind.newAbyssReport.reports
        #跳过没打深渊
        if len(abyss) == 0:
            logger.info(f"群{group_id}成员{qid}未打深渊")
            continue
        #跳过非上周结算
        if str(last_cutoff_day(is_abyss = True))!=str(abyss[0].updated_time_second.astimezone().date()):
            logger.info(f"群{group_id}成员{qid}上期未打深渊")
            continue

        rank[region_id].append(ind)
        time.sleep(1)

    #读取配置文件
    totalCount = Config.get_config("rank_bh3", "SHOWCOUNTALL")
    for region in rank.keys():
        #总模板数据
        paraTotal={}
        paraTotal["server"]=ItemTrans.id2server(region)
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
        #未查到可用数据
        if len(rank[region])==0:
            template = open(os.path.join(os.path.dirname(__file__), "template_abyss_none.html"), "r", encoding="utf8").read()
            html=template.format(**paraTotal)
            pic = await html_to_pic(html=html, wait=5, template_path= f"file://{os.path.dirname(__file__)}", no_viewport=True)
            #写文件
            with open(os.path.join(os.path.dirname(__file__), f'image/abyss_{group_id}_{region}_{last_cutoff_day(is_abyss=True)}.png'), "ab") as f:
                f.write(pic)
            continue
            
        #结算时间
        paraTotal["time_second"]=rank[region][0].newAbyssReport.reports[0].updated_time_second.astimezone().date()
        #boss名称
        paraTotal[f"bossName"] = rank[region][0].newAbyssReport.reports[0].boss.name

        #获取rank数据
        rank_data = load_data()
        #清除原数据,避免因更新深渊时掉出榜单而导致出现多个重复名次
        if str(group_id) in rank_data:
            if "abyss_cup" in rank_data[str(group_id)]:
                for rid in rank_data[str(group_id)]["abyss_cup"]:
                    if str(paraTotal["time_second"]) in rank_data[str(group_id)]["abyss_cup"][rid]:
                        rank_data[str(group_id)]["abyss_cup"][rid].pop(str(paraTotal["time_second"]))
            if "abyss_score" in rank_data[str(group_id)]:
                for rid in rank_data[str(group_id)]["abyss_score"]:
                    if str(paraTotal["time_second"]) in rank_data[str(group_id)]["abyss_score"][rid]:
                        rank_data[str(group_id)]["abyss_score"][rid].pop(str(paraTotal["time_second"]))

        #总杯数
        rank[region].sort(key=lambda x: x.index.stats.new_abyss.cup_number, reverse=True)
        templateRankTotal = open(os.path.join(os.path.dirname(__file__), "template_abyss_rank_total.html"), "r", encoding="utf8").read()
        rankNo=1
        finalRankTotal=""
        for i in rank[region]:  
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
            para["cup"]=i.index.stats.new_abyss.cup_number
            para["level"]=ItemTrans.abyss_level(i.index.stats.new_abyss.level)
            para["change"], para["color"]=get_rank_change(group_id, i.index.role.role_id, para["rank"], paraTotal["time_second"], rank_data, type=1)
            finalRankTotal += templateRankTotal.format(**para)
            if rankNo > totalCount:
                break
        paraTotal["rankTotal"] = finalRankTotal

        #boss
        templateRankBoss = open(os.path.join(os.path.dirname(__file__), "template_abyss_rank_boss.html"), "r", encoding="utf8").read()
        finalRankBoss=""
        rank[region].sort(key=lambda x: (x.newAbyssReport.reports[0].settled_level, x.newAbyssReport.reports[0].score), reverse=True)
        rankNo=1
        for i in rank[region]:
            para["rank"] = rankNo
            para={}
            para["nickname"]=i.index.role.nickname
            para["bossRank"]=i.newAbyssReport.reports[0].rank
            para["bossCup"]=i.newAbyssReport.reports[0].cup_number
            para["settledCupNumber"]=i.newAbyssReport.reports[0].settled_cup_number
            para["level"]=ItemTrans.abyss_level(i.index.stats.new_abyss.level)
            para["score"]=i.newAbyssReport.reports[0].score
            para["star1"]=["b", "a", "s", "ss", "sss"][i.newAbyssReport.reports[0].lineup[0].star - 1]
            para["star2"]=["b", "a", "s", "ss", "sss"][i.newAbyssReport.reports[0].lineup[1].star - 1]
            para["star3"]=["b", "a", "s", "ss", "sss"][i.newAbyssReport.reports[0].lineup[2].star - 1]
            para["star4"]=[1, 2, 2, 3, 3, 3, 4][i.newAbyssReport.reports[0].elf.star - 1]
            para["bg1"]=i.newAbyssReport.reports[0].lineup[0].avatar_background_path
            para["bg2"]=i.newAbyssReport.reports[0].lineup[1].avatar_background_path
            para["bg3"]=i.newAbyssReport.reports[0].lineup[2].avatar_background_path 
            para["icon1"]=i.newAbyssReport.reports[0].lineup[0].icon_path
            para["icon2"]=i.newAbyssReport.reports[0].lineup[1].icon_path
            para["icon3"]=i.newAbyssReport.reports[0].lineup[2].icon_path     
            para["elf"]=i.newAbyssReport.reports[0].elf.avatar
            para["boss"]=i.newAbyssReport.reports[0].boss.avatar
            para["change"], para["color"]=get_rank_change(group_id, i.index.role.role_id, rankNo, paraTotal["time_second"], rank_data, type=2)
            finalRankBoss += templateRankBoss.format(**para)
            rankNo += 1
            if rankNo > totalCount:
                break
        paraTotal[f"rankBoss"] = finalRankBoss

        #汇总
        template = open(os.path.join(os.path.dirname(__file__), "template_abyss.html"), "r", encoding="utf8").read()
        html=template.format(**paraTotal)
        pic = await html_to_pic(html=html, wait=5, template_path= f"file://{os.path.dirname(__file__)}", no_viewport=True)
        #写排行图片
        with open(os.path.join(os.path.dirname(__file__), f'image/abyss_{group_id}_{region}_{paraTotal["time_second"]}.png'), "ab") as f:
            f.write(pic)
        #写rank数据
        save_data(rank_data)


#崩坏三战场排行
@battle_field.handle()
async def _(event: GroupMessageEvent):
    #读取配置文件
    cookie = Config.get_config("bind_bh3", "COOKIE")
    if not cookie:
        await battle_field.finish("需要真寻主人在config.yaml中配置cookie才能使用该功能")
    #获取群号 
    group_id = event.group_id
    #获取战场排行    
    image_path = os.path.join(os.path.dirname(__file__), f'image/war_{group_id}_{last_cutoff_day()}.png')
    if not os.path.exists(image_path):
        await battle_field.send(f'正在更新崩坏三战场排行,耗时较久请耐心等待')  
        await getBattleData(group_id)
    await battle_field.finish(image(image_path))

#崩坏三战场排行更新
@battle_field_update.handle()
async def _(event: GroupMessageEvent):
    #读取配置文件
    cookie = Config.get_config("bind_bh3", "COOKIE")
    if not cookie:
        await battle_field_update.finish("需要真寻主人在config.yaml中配置cookie才能使用该功能")
    #获取群号
    group_id = event.group_id    
    await battle_field_update.send(f'正在更新崩坏三战场排行,耗时较久请耐心等待')        
    await getBattleData(group_id)
    await battle_field_update.finish(f'已更新崩坏三战场排行，请使用命令 崩坏三战场排行 查看', at_sender=True ) 

@scheduler.scheduled_job(#定时任务，每周一、周二5时
    "cron",
    day_of_week="mon,tue",
    hour=5,
    minute=0,
)
async def _():
    try:
        bot = get_bot()
        gl = await bot.get_group_list()
        gl = [g["group_id"] for g in gl]
        for g in gl:
            await getBattleData(g)
            logger.info(f"{g} 生成战场排行成功")
            time.sleep(60)
    except Exception as e:
        logger.error(f"生成战场排行错误 e:{e}")

async def getBattleData(group_id: str):      
    #删除战场排行 
    image_path = os.path.join(os.path.dirname(__file__), f'image/war_{group_id}_{last_cutoff_day()}.png')
    if os.path.exists(image_path):
        try:
            os.unlink(image_path)
        except Exception as e:
            logger.error(f'更新崩坏三战场排行失败,请联系真寻管理员手动处理：{e}')

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
            print(ind)
        except InfoError as e:
            continue
        #跳过非终级区
        if 4 != ind.index.stats.battle_field_area:
            logger.info(f"群{group_id}成员{qid}非终级区")
            continue
        bfr = ind.battleFieldReport.reports[0]
        #跳过非上周结算
        if str(last_cutoff_day())!=str(bfr.time_second.astimezone().date()):
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

    #读取配置文件
    totalCount = Config.get_config("rank_bh3", "SHOWCOUNTALL")
    bossCount = Config.get_config("rank_bh3", "SHOWCOUNTBOSS")

    #总模板数据
    paraTotal={}
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
    #未查到可用数据
    if len(rank)==0:
        template = open(os.path.join(os.path.dirname(__file__), "template_battle_none.html"), "r", encoding="utf8").read()
        html=template.format(**paraTotal)
        pic = await html_to_pic(html=html, wait=5, template_path= f"file://{os.path.dirname(__file__)}", no_viewport=True)
        #写文件
        with open(os.path.join(os.path.dirname(__file__), f'image/war_{group_id}_{last_cutoff_day()}.png'), "ab") as f:
            f.write(pic)
        return
        
    #结算时间
    paraTotal["time_second"]=rank[0].battleFieldReport.reports[0].time_second.astimezone().date()

    #boss名称
    for i in range(1,4):
        paraTotal[f"bossName{i}"] = rank[0].battleFieldReport.reports[0].battle_infos[i-1].boss.name

    #获取rank数据
    rank_data = load_data()
    #清除原数据,避免因更新战场时掉出榜单而导致出现多个重复名次
    if str(group_id) in rank_data:
        if "war" in rank_data[str(group_id)]:
            for rid in rank_data[str(group_id)]["war"]:
                if str(paraTotal["time_second"]) in rank_data[str(group_id)]["war"][rid]:
                    rank_data[str(group_id)]["war"][rid].pop(str(paraTotal["time_second"]))

    #总分
    rank.sort(key=lambda x: x.battleFieldReport.reports[0].score, reverse=True)
    templateRankTotal = open(os.path.join(os.path.dirname(__file__), "template_battle_rank_total.html"), "r", encoding="utf8").read()
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
        para["percent"]=f"{i.index.stats.battle_field_ranking_percentage}%"
        para["change"], para["color"]=get_rank_change(group_id, i.index.role.role_id, para["rank"], paraTotal["time_second"], rank_data)
        finalRankTotal += templateRankTotal.format(**para)
        if rankNo > totalCount:
            break
    paraTotal["rankTotal"] = finalRankTotal

    #boss
    templateRankBoss = open(os.path.join(os.path.dirname(__file__), "template_battle_rank_boss.html"), "r", encoding="utf8").read()
    for n in range(3):
        finalRankBoss=""
        rank.sort(key=lambda x: x.battleFieldReport.reports[0].battle_infos[n].score, reverse=True)
        logger.debug(f"\n按{rank[0].battleFieldReport.reports[0].battle_infos[n].boss.name}排序")
        rankNo=1
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
            rankNo += 1
            if rankNo > bossCount:
                break
        paraTotal[f"rankBoss{n+1}"] = finalRankBoss

    #汇总
    template = open(os.path.join(os.path.dirname(__file__), "template_battle.html"), "r", encoding="utf8").read()
    html=template.format(**paraTotal)
    pic = await html_to_pic(html=html, wait=5, template_path= f"file://{os.path.dirname(__file__)}", no_viewport=True)
    #写排行图片
    with open(os.path.join(os.path.dirname(__file__), f'image/war_{group_id}_{paraTotal["time_second"]}.png'), "ab") as f:
        f.write(pic)
    #写rank数据getData(
    save_data(rank_data)

#最新一期结算时间
def last_cutoff_day(today = datetime.now(), is_abyss = False):
    if is_abyss and today.weekday() >= 4:
        return datetime.strftime(today - timedelta(today.weekday()-2), "%Y-%m-%d")
    else:
        return datetime.strftime(today - timedelta(today.weekday()), "%Y-%m-%d")

#上周一
def last_monday(today = datetime.now()):
    return (today - timedelta(days=7)).strftime('%Y-%m-%d')
    
def get_rank_change(group_id, role_id, rank, time_second, data, type = 0):
    group_id = str(group_id)
    role_id = str(role_id)
    time_second_str = str(time_second)
    if type == 0 :
        rank_type = "war" 
    elif type == 1:
        rank_type = "abyss_cup"
    else:  
        rank_type = "abyss_score"      
    if group_id in data:
        if rank_type in data[group_id]:
            if role_id in data[group_id][rank_type]:
                data[group_id][rank_type][role_id][time_second_str] = rank
            else:
                data[group_id][rank_type][role_id] = {time_second_str: rank}
        else:
            data[group_id][rank_type]={role_id: {time_second_str: rank}}
    else:
        data[group_id] = {rank_type: {role_id: {time_second_str: rank}}}
    #获取上周数据
    try:
        last_rank = data[group_id][rank_type][role_id][f'{last_monday(time_second)}']
    except:
        #新上榜
        return "new", "red"
    #名次变化
    change = last_rank - rank
    if change < 0:
        #名次下降
        return f'{-change}↓', "green"
    elif change == 0:
        #名次不变
        return '=', "#896a4d"
    else:
        #名次上升
        return f'{change}↑', "red"

#反序列化排行文件
def load_data():
    if not os.path.exists(RANK_JSON):
        with open(RANK_JSON, "w", encoding="utf8") as f:
            json.dump({}, f)
            return {}
    with open(RANK_JSON, "r", encoding="utf8") as f:
        data: dict = json.load(f)
        #兼容旧版json
        #无内容不判断
        if len(data.keys()) <= 0:
            return data
        is_old = True
        #没war字段，属于旧版，需要调整结构
        for i in data.keys():
            if "war" in data[i]:
                is_old=False
            break
        #调整结构
        if is_old:
            for i in data.keys():
                tmp = data[i]
                data[i]={"war": tmp}            
        return data
#序列化排行文件
def save_data(data):
    with open(RANK_JSON, "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
