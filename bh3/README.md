<!--
 * @Author: MobiusT
 * @Date: 2023-02-25 19:14:10
 * @LastEditors: MobiusT
 * @LastEditTime: 2023-04-21 23:24:22
-->
# bh3

崩坏三相关插件

## 使用

<details>
<summary>崩坏三绑定</summary>
崩坏三绑定[uid] [服务器]<br>
崩坏三服务器列表<br>
崩坏三ck[cookie]     # 该绑定请私聊<br>
崩坏三ck同步         # 该命令要求先绑定原神cookie，通过绑定的原神cookie绑定崩三ck   <br>
崩坏三ck扫码         # 使用米游社扫码绑定崩三ck（不可用扫码器）<br>
</details>
<details>
<summary>崩坏三卡片</summary>
崩坏三卡片                #已绑定uid时使用<br>
崩坏三卡片[uid] [服务器]    #初次使用命令/查询别的玩家的卡片<br>
崩坏三卡片[uid]           #查询已经绑定过uid的玩家的卡片<br>
崩坏三卡片[@]             #查询at的玩家绑定的角色卡片<br>
崩坏三卡片米游社/mys/MYS[米游社id] #查询该米游社id的角色卡片<br>
</details>
<details>
<summary>崩坏三女武神</summary>
崩坏三女武神                #已绑定uid时使用<br>
崩坏三女武神[uid] [服务器]    #初次使用命令/查询别的玩家的女武神<br>
崩坏三女武神[uid]           #查询已经绑定过uid的玩家的女武神<br>
崩坏三女武神[@]             #查询at的玩家绑定的角色女武神<br>
崩坏三女武神米游社/mys/MYS[米游社id] #查询该米游社id的角色女武神<br>
</details>
<details>
<summary>崩坏三手账</summary>
崩坏三手账<br>
<br>
***该功能需要绑定cookie<br>
</details>
<details>
<summary>崩坏三阵容</summary>
崩坏三XXX阵容                #已绑定uid时使用<br>
崩坏三XXX阵容[uid] [服务器]    #初次使用命令/查询别的玩家的女武神<br>
崩坏三XXX阵容[uid]           #查询已经绑定过uid的玩家的女武神<br>
崩坏三XXX阵容[@]             #查询at的玩家绑定的角色女武神<br>
崩坏三XXX阵容米游社/mys/MYS[米游社id] #查询该米游社id的角色女武神<br>
崩坏三阵容更新      #更新阵容简称
</details>
<details>
<summary>崩坏三猜语音</summary>
崩坏三猜语音：正常舰桥、战斗等语音<br>
崩坏三猜语音2/困难：简短的语气或拟声词<br>
崩坏三猜语音答案<br>
崩坏三语音[name]：随机发送指定女武神一段语音<br>
崩坏三语音列表[name]：查看指定女武神所有语音<br>
崩坏三语音[name] [id]：发送指定女武神的指定语音<br>
崩坏三语音新增答案[标准答案]:[别称]  #将新的别称映射到标准答案中<br>
崩坏三语音更新答案    #更新答案模板<br>
更新崩坏三语音列表    #更新语音<br>

<br>
***该功能需要额外语音素材，请超级用户按需根据bh3/guess_voice/readme.md获取免费素材<br>
</details>
<details>
<summary>崩坏三排行</summary>
崩坏三战场排行<br>
崩坏三深渊排行[全部/all] [服务器] [@] #可选参数：[全部/all]全部排行  [服务器]对应服务器的排行  [@]at的人绑定的角色所在服务器<br>
崩坏三战场排行更新<br>
崩坏三深渊排行更新<br>
</details>
<details>
<summary>崩坏三签到</summary>
崩坏三签到       #签到并开启自动签到<br>
崩坏三签到关闭   #关闭自动签到<br>
<br>
***该功能需要绑定cookie<br>
</details>
<details>
<summary>崩坏三兑换码</summary>
[崩坏三]兑换码<br>
</details>

## 可能遇到的问题

<details>
<summary>崩三兑换码发送空白消息</summary>

插件依赖 [@Mrs4s/go-cqhttp](https://github.com/Mrs4s/go-cqhttp) 的合并转发接口，如需启用私聊响应请务必安装 [v1.0.0-rc2](https://github.com/Mrs4s/go-cqhttp/releases/tag/v1.0.0-rc2) 以上版本的 go-cqhttp。

</details>

## 更新

### 2023/04/23[崩坏三绑定](https://github.com/MobiusT/zhenxun_extensive_plugin_mobius/tree/main/bh3/bind_bh3) [v0.3]

1. 优化代码

### 2023/04/21

1. 猜语音、崩三阵容插件适配羽兔及普罗米修斯

2. 修复更新阵容、语音答案出错

### 2023/04/04

1. 调整崩三手账插件的开关触发词，改为与命令触发词一致

### 2023/03/18

1. 调整崩三兑换码插件描述

### 2023/03/09[崩坏三阵容](https://github.com/MobiusT/zhenxun_extensive_plugin_mobius/tree/main/bh3/group_bh3) [v0.2]

1. 崩三语音适配苏莎娜， 优化超级用户帮助写法

2. 崩三阵容适配苏莎娜

3. 崩三阵容新增命令 崩坏三阵容更新  可以从本库更新group.json 【超级用户权限】

### 2023/03/06[崩坏三猜语音](https://github.com/MobiusT/zhenxun_extensive_plugin_mobius/tree/main/bh3/guess_voice) [v0.2]

1. 崩三排行修改为每日更新，避免更新时米游社数据未同步或新增绑定角色时数据不准确

2. 崩三猜语音新增超级用户帮助

3. 崩三猜语音新增命令 崩坏三语音更新答案 可以从本库更新answer.json 【超级用户权限】

### 2023/03/03

1. 修复兑换码周礼包获取出错问题

2. 修复前瞻直播间id无法获取的问题

### 2023/02/27

1. 修复崩三排行结算时间获取错误的问题

2. 修复崩三排行部分玩家头像展示出错的问题

3. 崩三排行兼容真寻2023/02/26 config更新[8133b61](https://github.com/HibiKier/zhenxun_bot/commit/8133b61ebd28459a5a33bd53e998eb636c3725b4)

### 2023/02/26

1. 修改cd类型为群聊

### 2023/02/25[崩坏三绑定](https://github.com/MobiusT/zhenxun_extensive_plugin_mobius/tree/main/bh3/bind_bh3) [v0.2]， [崩坏三兑换码](https://github.com/MobiusT/zhenxun_extensive_plugin_mobius/tree/main/bh3/code_bh3) [v0.1]

1. 新增扫码绑定ck命令： 崩三ck扫码 （新增依赖qrcode）

2. 新增崩坏三兑换码插件，功能测试中；改写自[monsterxcn/nonebot-plugin-gscode](https://github.com/monsterxcn/nonebot-plugin-gscode/tree/main/nonebot_plugin_gscode)

3. 修复崩三手账生成错误，现在可以使用最新版本pillow

```python
ValueError: Operation on closed image
```

### 更早[v0.1]

1. 基于[崩坏三插件](https://github.com/chingkingm/honkai_mys) 改写
