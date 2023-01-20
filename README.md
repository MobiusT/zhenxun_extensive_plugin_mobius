<!--
 * @Author: MobiusT
 * @Date: 2022-11-03 21:30:42
 * @LastEditors: MobiusT
 * @LastEditTime: 2023-01-02 12:06:55
-->
# zhenxun_extensive_plugin_mobius

适用于zhenxun_bot的扩展插件

自学的python，写的可能不是很好（估计有很多bug），见谅

## 列表
- [崩坏三](https://github.com/MobiusT/zhenxun_extensive_plugin_mobius/tree/main/bh3)移植自[崩坏三插件](https://github.com/chingkingm/honkai_mys) 深渊排行未做
- [签退](https://github.com/MobiusT/zhenxun_extensive_plugin_mobius/tree/main/reSign)
- [识宝骂我](https://github.com/MobiusT/zhenxun_extensive_plugin_mobius/tree/main/send_shibao_voice)(改自真寻原版插件骂我)
- [繁中转简中](https://github.com/MobiusT/zhenxun_extensive_plugin_mobius/tree/main/traditional2simplified)
- [echo](https://github.com/MobiusT/zhenxun_extensive_plugin_mobius/tree/main/zhenxun_echo)
- [禁止发烧](https://github.com/MobiusT/zhenxun_extensive_plugin_mobius/tree/main/resendRecallMsgByqid)将指定qq撤回的消息发送至撤回的群聊
- [定时获取签到日志](https://github.com/MobiusT/zhenxun_extensive_plugin_mobius/tree/main/getSignLog)(自用，通过sh脚本获取日志到插件目录后生成图片推送)

## 崩坏三插件ck获取方式
如果已知自己的ck可直接在配置文件中配置，否则按下文处理。示例：COOKIE: cookie_token=xxxxxx;account_id=xxxxxx

1、超级用户私聊真寻【崩三ck】

2、按真寻提示步骤获取login_ticket

3、私聊真寻【崩坏三ck login_ticket=xxxxxxxxxxxxxxx】

4、真寻返回【当前未配置查询ck，请在真寻配置文件config.yaml的bind_bh3.COOKIE下配置如下内容，然后重启真寻。
cookie_token=xxxxxx;account_id=xxxxxx】
根据真寻返回的内容进行配置


提示：

1、第4步仅在超级用户且未配置崩坏三ck时返回，否则为绑定游戏账户ck，用于崩三手账及签到

2、配置完毕后需要重启真寻才能正常使用，重载配置无效 

## 可能遇到的问题
```python
return value.encode(encoding or "ascii")
AttributeError: 'NoneType' object has no attribute 'encode'
```
尝试执行pip install httpx 或 pip install nb-cli

```python
ValueError: Operation on closed image
```
执行pip install pillow==9.1.1



```
签到图片中出现白色方块
```
下载[emoji字体](https://gitee.com/songboy/noto-emoji/tree/master/fonts),放到/usr/share/fonts下，加载字体后重启真寻

## 感谢
[CRAZYShimakaze/genshin_role_info](https://github.com/CRAZYShimakaze/zhenxun_extensive_plugin/tree/main/genshin_role_info) : 源码参考（我是fw）
[HibiKier/zhenxun_bot](https://github.com/HibiKier/zhenxun_bot) : 超好用的基于nonebot2的qq机器人