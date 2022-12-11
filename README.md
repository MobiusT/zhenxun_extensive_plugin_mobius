<!--
 * @Author: MobiusT
 * @Date: 2022-11-03 21:30:42
 * @LastEditors: MobiusT
 * @LastEditTime: 2022-12-11 19:09:02
-->
# zhenxun_extensive_plugin_mobius

适用于zhenxun_bot的扩展插件

自学的python，写的可能不是很好（估计有很多bug），见谅

## 列表
- [崩坏三](https://github.com/MobiusT/zhenxun_extensive_plugin_mobius/tree/main/bh3)移植自[崩坏三插件](https://github.com/chingkingm/honkai_mys)
- [签退](https://github.com/MobiusT/zhenxun_extensive_plugin_mobius/tree/main/reSign)
- [识宝骂我](https://github.com/MobiusT/zhenxun_extensive_plugin_mobius/tree/main/send_shibao_voice)(改自真寻原版插件骂我)
- [繁中转简中](https://github.com/MobiusT/zhenxun_extensive_plugin_mobius/tree/main/traditional2simplified)
- [echo](https://github.com/MobiusT/zhenxun_extensive_plugin_mobius/tree/main/zhenxun_echo)
- [禁止发烧](https://github.com/MobiusT/zhenxun_extensive_plugin_mobius/tree/main/resendRecallMsgByqid)将指定qq撤回的消息发送至撤回的群聊
- [定时获取签到日志](https://github.com/MobiusT/zhenxun_extensive_plugin_mobius/tree/main/getSignLog)(自用，通过sh脚本获取日志到插件目录后生成图片推送)

## 可能遇到的问题
```python
return value.encode(encoding or "ascii")
AttributeError: 'NoneType' object has no attribute 'encode'
```
尝试执行pip install httpx 或 pip install nb-cli

```
签到图片中出现白色方块
```
下载[emoji字体](https://gitee.com/songboy/noto-emoji/tree/master/fonts),放到/usr/share/fonts下，加载字体后重启真寻

## 感谢
[CRAZYShimakaze/genshin_role_info](https://github.com/CRAZYShimakaze/zhenxun_extensive_plugin/tree/main/genshin_role_info) : 源码参考（我是fw）
[HibiKier/zhenxun_bot](https://github.com/HibiKier/zhenxun_bot) : 超好用的基于nonebot2的qq机器人